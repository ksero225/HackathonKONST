import React, { useEffect, useRef, useState } from "react";
import SockJS from "sockjs-client";
import { Client } from "@stomp/stompjs";

const WS_URL = "https://continuable-manuela-podgy.ngrok-free.dev/ws-sockjs";

function EventGroupChat({ user, eventId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [connectionError, setConnectionError] = useState(null);

  const stompClientRef = useRef(null);

  useEffect(() => {
    if (!eventId) return;

    const socket = new SockJS(WS_URL);

    const client = new Client({
      webSocketFactory: () => socket,
      reconnectDelay: 5000,
      debug: (str) => {
        console.log("STOMP (event chat):", str);
      },
      onConnect: () => {
        console.log("STOMP connected (event chat), eventId:", eventId);
        setConnectionError(null);

        const topic = `/topic/event-chat.${eventId}`;

        client.subscribe(topic, (message) => {
          try {
            const bodyStr = message.body || "";
            let payload;
            try {
              payload = JSON.parse(bodyStr);
            } catch {
              payload = null;
            }

            const text = payload?.content || bodyStr;
            const senderId = payload?.senderId ?? null;

            const own =
              senderId != null &&
              user?.userId != null &&
              Number(senderId) === Number(user.userId);

            const senderLabel = own
              ? "Ty"
              : senderId != null
              ? `Uczestnik #${senderId}`
              : "Uczestnik";

            setMessages((prev) => [
              ...prev,
              {
                text,
                senderId,
                senderLabel,
                own,
              },
            ]);
          } catch (err) {
            console.error("Błąd parsowania wiadomości event-chat:", err);
          }
        });
      },
      onStompError: (frame) => {
        console.error("STOMP error (event chat):", frame);
        setConnectionError("Błąd protokołu STOMP (czat wydarzenia).");
      },
      onWebSocketError: (event) => {
        console.error("WebSocket error (event chat):", event);
        setConnectionError("Błąd połączenia z serwerem (czat wydarzenia).");
      },
    });

    client.activate();
    stompClientRef.current = client;

    return () => {
      client.deactivate();
      stompClientRef.current = null;
    };
  }, [eventId, user?.userId]);

  useEffect(() => {
    const el = document.getElementById("eventChatBottom");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || !eventId) return;

    const client = stompClientRef.current;
    if (!client || !client.connected) {
      setConnectionError("Brak połączenia z serwerem czatu.");
      return;
    }

    const content = input.trim();
    setInput("");

    const senderId = user?.userId || user?.id;

    setMessages((prev) => [
      ...prev,
      {
        text: content,
        senderId,
        senderLabel: "Ty",
        own: true,
      },
    ]);

    try {
      client.publish({
        destination: "/app/event-chat",
        body: JSON.stringify({
          eventId,
          senderId,
          content,
        }),
      });
    } catch (err) {
      console.error("Błąd przy wysyłce przez STOMP:", err);
      setConnectionError("Nie udało się wysłać wiadomości (brak połączenia).");
    }
  };

  if (!eventId) return null;

  return (
    <div className="d-flex flex-column h-100">
      <h5 className="mb-2">Czat uczestników</h5>
      <p className="small text-muted mb-2">
        Rozmawiaj z osobami zapisanymi na to wydarzenie.
      </p>

      {connectionError && (
        <div className="alert alert-danger py-1 small">
          {connectionError}
        </div>
      )}

      <div
        className="border rounded p-2 flex-grow-1 overflow-auto chat-box"
        style={{ minHeight: "260px" }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`mb-1 d-flex ${
              m.own ? "justify-content-end" : "justify-content-start"
            }`}
          >
            <div
              className={`chat-bubble ${
                m.own ? "chat-bubble-user" : "chat-bubble-bot"
              }`}
              style={{ maxWidth: "80%" }}
            >
              {!m.own && (
                <div className="small fw-bold mb-1">{m.senderLabel}</div>
              )}
              <div>{m.text}</div>
            </div>
          </div>
        ))}

        <div id="eventChatBottom" />
      </div>

      <form onSubmit={handleSubmit} className="d-flex gap-2 mt-2">
        <input
          type="text"
          className="form-control"
          placeholder="Napisz wiadomość do grupy..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="btn btn-success">
          Wyślij
        </button>
      </form>
    </div>
  );
}

export default EventGroupChat;
