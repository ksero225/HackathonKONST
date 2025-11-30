// src/pages/AboutBot.js
import React, { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import SockJS from "sockjs-client";
import { Client } from "@stomp/stompjs";

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

function AboutBot({ user, setUser }) {
  const query = useQuery();
  const userId = query.get("userId");

  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Hej! Opowiedz mi coś o sobie, żebym mógł Cię lepiej poznać. :)",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [finished, setFinished] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  const stompClientRef = useRef(null);

  useEffect(() => {
    const socket = new SockJS(
      "https://continuable-manuela-podgy.ngrok-free.dev/ws-sockjs"
    );

    const client = new Client({
      webSocketFactory: () => socket,
      reconnectDelay: 5000,
      debug: (str) => {
        console.log("STOMP:", str);
      },
      onConnect: () => {
        console.log("STOMP connected");
        setConnectionError(null);

        client.subscribe("/topic/description", (message) => {
          try {
            console.log("RAW STOMP message.body:", message.body);

            // 1. zewnętrzny JSON (headers/body/statusCode)
            let outer;
            try {
              outer = JSON.parse(message.body);
            } catch {
              outer = null;
            }

            // 2. wewnętrzny JSON jako string w "content"
            const contentStr =
              outer?.body?.content ??
              outer?.content ??
              null;

            let inner = null;
            if (contentStr && typeof contentStr === "string") {
              try {
                inner = JSON.parse(contentStr);
              } catch {
                inner = null;
              }
            }

            let botText = "";
            let isFinishedMsg = false;

            if (inner && typeof inner === "object") {
              if (inner.finished === true) {
                // KONIEC ROZMOWY – korzystamy z finalDescription, ALE nie pokazujemy go w czacie
                botText =
                  inner.finalDescription ||
                  inner.currentMessage ||
                  inner.botMessage ||
                  "";
                isFinishedMsg = true;
              } else {
                // W TRAKCIE – currentMessage
                botText =
                  inner.currentMessage ||
                  inner.botMessage ||
                  "";
              }
            }

            if (!botText) {
              botText = contentStr || message.body;
            }

            const botTextStr = String(botText).trim();

            // flaga – czy faktycznie dodaliśmy nową widoczną wiadomość bota
            let addedBotMessage = false;

            setMessages((prev) => {
              const lastUser = [...prev]
                .reverse()
                .find((m) => m.from === "user");

              // echo ostatniej wiadomości usera – ignorujemy
              if (lastUser && lastUser.text.trim() === botTextStr) {
                return prev;
              }

              let next = [...prev];

              // 1️⃣ zwykłe wiadomości bota (finished === false) – pokazujemy w czacie
              if (!isFinishedMsg) {
                next.push({
                  from: "bot",
                  text: botTextStr,
                });
                addedBotMessage = true;
              }

              // 2️⃣ finalna wiadomość (finished === true) – NIE pokazujemy opisu,
              // tylko podziękowanie
              if (isFinishedMsg) {
                next.push({
                  from: "bot",
                  text:
                    "Dzięki za rozmowę! Mam już pełny opis Ciebie i mogę dobrać Ci misje.",
                });
                addedBotMessage = true;
              }

              return next;
            });

            if (isFinishedMsg) {
              setFinished(true);

              // 🔥 aktualizujemy user.userDescription w stanie + localStorage
              if (inner?.finalDescription && typeof setUser === "function") {
                setUser((prev) => {
                  if (!prev) return prev;
                  const updated = {
                    ...prev,
                    userDescription: inner.finalDescription, // dopasuj do nazwy pola na backendzie
                  };
                  localStorage.setItem("user", JSON.stringify(updated));
                  return updated;
                });
              }
            }

            // chowamy "bot pisze..." gdy jakakolwiek nowa wiadomość bota trafiła do czatu
            if (addedBotMessage) {
              setIsLoading(false);
            }
          } catch (err) {
            console.error("Błąd parsowania wiadomości z STOMP:", err);
            setMessages((prev) => [
              ...prev,
              { from: "bot", text: message.body },
            ]);
            setIsLoading(false);
          }
        });
      },
      onStompError: (frame) => {
        console.error("STOMP error:", frame);
        setConnectionError("Błąd protokołu STOMP.");
        setIsLoading(false);
      },
      onWebSocketError: (event) => {
        console.error("WebSocket error:", event);
        setConnectionError("Błąd połączenia z serwerem.");
        setIsLoading(false);
      },
    });

    client.activate();
    stompClientRef.current = client;

    return () => {
      client.deactivate();
    };
  }, [userId, setUser]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || finished) return;

    const userMessage = input.trim();
    setInput("");

    const client = stompClientRef.current;

    if (!client || !client.active) {
      setMessages((prev) => [
        ...prev,
        {
          from: "bot",
          text: "Brak połączenia z serwerem. Spróbuj odświeżyć stronę.",
        },
      ]);
      return;
    }

    // wiadomość użytkownika – zielona bańka po prawej
    setMessages((prev) => [...prev, { from: "user", text: userMessage }]);
    setIsLoading(true); // od tej chwili pokazujemy "bot pisze..."

    client.publish({
      destination: "/app/description",
      body: JSON.stringify({
        userId,
        content: userMessage,
      }),
    });
  };

  useEffect(() => {
    const el = document.getElementById("chatBottom");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="row justify-content-center">
      <div
        className="col-lg-8 col-xl-6 d-flex flex-column"
        style={{ maxHeight: "70vh" }}
      >
        <h2 className="mb-3">Poznajmy się</h2>
        <p className="mb-3">
          Ten krótki dialog z botem pomoże nam stworzyć Twój profil i dopasować
          misje.
        </p>

        {connectionError && (
          <div className="alert alert-danger py-2">
            {connectionError}
          </div>
        )}

<div
  className="border rounded p-3 mb-3 flex-grow-1 overflow-auto chat-box"
>
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`mb-2 d-flex ${
                m.from === "user"
                  ? "justify-content-end"
                  : "justify-content-start"
              }`}
            >
<div
  className={`chat-bubble ${
    m.from === "user"
      ? "chat-bubble-user"
      : "chat-bubble-bot"
  }`}
>
  {m.text}
</div>
            </div>
          ))}

          {/* "Bot pisze..." jako osobny bąbelek bota na końcu */}
          {isLoading && (
            <div className="mb-2 d-flex justify-content-start">
<div
  className="chat-bubble chat-bubble-bot typing-bubble d-inline-flex align-items-center"
>
                <span role="img" aria-label="bot" className="me-2">
                  🤖
                </span>
                <span className="typing-dots">
                  Bot pisze
                  <span className="dot">.</span>
                  <span className="dot">.</span>
                  <span className="dot">.</span>
                </span>
              </div>
            </div>
          )}

          <div id="chatBottom" />
        </div>

        <form onSubmit={handleSubmit} className="d-flex gap-2">
          <input
            type="text"
            className="form-control"
            placeholder={
              finished
                ? "Rozmowa zakończona – możesz przejść dalej."
                : "Napisz odpowiedź i wciśnij Enter..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={finished}
          />
          <button
            type="submit"
            className="btn btn-success"
            disabled={finished}
          >
            Wyślij
          </button>
        </form>

        {finished && (
          <small className="mt-2 text-success">
            Dzięki! Bot ma już wystarczająco informacji, żeby stworzyć opinię o
            Tobie.
          </small>
        )}
      </div>
    </div>
  );
}

export default AboutBot;
