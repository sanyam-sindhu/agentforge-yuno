import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.channels.telegram import handle_message


@pytest.mark.asyncio
async def test_handle_message_no_workflow():
    update = MagicMock()
    update.message.text = "Research AI trends"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("backend.channels.telegram.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        mock_session_cls.return_value = mock_session

        await handle_message(update, context)

    calls = [str(c) for c in update.message.reply_text.call_args_list]
    assert any("Processing" in c for c in calls)
    assert any("No workflow" in c for c in calls)


@pytest.mark.asyncio
async def test_handle_message_with_workflow():
    update = MagicMock()
    update.message.text = "Research AI trends"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    mock_workflow = MagicMock()
    mock_workflow.id = 1

    with patch("backend.channels.telegram.AsyncSessionLocal") as mock_session_cls, \
         patch("backend.channels.telegram.run_workflow", new_callable=AsyncMock, return_value="Report ready!"):

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_workflow)))
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session_cls.return_value = mock_session

        await handle_message(update, context)

    calls = [str(c) for c in update.message.reply_text.call_args_list]
    assert any("Report ready!" in c for c in calls)
