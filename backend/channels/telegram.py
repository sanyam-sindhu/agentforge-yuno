import re
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import select
from backend.core.config import get_settings
from backend.core.database import AsyncSessionLocal
from backend.models.workflow import Workflow
from backend.models.execution import Execution
from backend.runtime.engine import run_workflow

settings = get_settings()


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to AgentForge!\n\n"
        "Commands:\n"
        "/research <topic> — Research any topic and get a report\n"
        "/triage <message> — Classify and respond to a support message\n\n"
        "Or just send any message to trigger Research by default."
    )


async def _run(update: Update, template_id: str, user_text: str):
    started_at = time.time()
    await update.message.reply_text("Processing your request...")

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Workflow).where(Workflow.template_id == template_id).limit(1)
            )
            workflow = result.scalar_one_or_none()

            if not workflow:
                await update.message.reply_text(f"Workflow '{template_id}' not found. Check the UI.")
                return

            execution = Execution(workflow_id=workflow.id, input_text=user_text)
            db.add(execution)
            await db.commit()
            await db.refresh(execution)

            output = await run_workflow(execution.id, workflow, user_text, db)

        elapsed = time.time() - started_at
        output = _strip_markdown(output or "Done! Check the AgentForge UI for details.")
        footer = f"\n\n⏱ Completed in {elapsed:.1f}s"

        if len(output) + len(footer) > 4000:
            output = output[:4000 - len(footer)] + "...(truncated)"
        output += footer

        await update.message.reply_text(output)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"Error: {e}")


async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else update.message.text
    if not text:
        await update.message.reply_text("Usage: /research <topic>")
        return
    await _run(update, "research_report", text)


async def cmd_triage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else update.message.text
    if not text:
        await update.message.reply_text("Usage: /triage <your support message>")
        return
    await _run(update, "customer_support_triage", text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _run(update, "research_report", update.message.text)


def build_telegram_app():
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("triage", cmd_triage))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
