import { useEffect, useRef, useState } from "react";

export function useWebSocket() {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    const wsBase = import.meta.env.VITE_API_URL
      ? import.meta.env.VITE_API_URL.replace(/^http/, "ws")
      : `ws://${window.location.host}`;
    const socket = new WebSocket(`${wsBase}/ws/monitor`);
    ws.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        setEvents((prev) => [parsed, ...prev].slice(0, 200));
      } catch {}
    };

    return () => socket.close();
  }, []);

  const clear = () => setEvents([]);

  return { events, connected, clear };
}
