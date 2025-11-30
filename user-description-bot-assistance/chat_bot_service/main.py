import json
import threading
import time
from textwrap import dedent
from typing import Optional, List, Dict, Tuple

from fastapi import FastAPI
from pydantic import BaseModel
import websocket  # klient WebSocket/STOMP

from config import client, WS_URI
from traits import send_final_description_to_backend


# ================== FASTAPI APP ==================

app = FastAPI(
    title="ProfilBot Conversation API",
    description="Dynamiczny bot do rozmowy i iteracyjnego budowania opisu profilu",
    version="0.4.1",
)


# ================== STAN ROZMÓW (per userId) ==================


class QA(BaseModel):
    question: str
    answer: str


class ChatState(BaseModel):
    description: str = ""
    transcript: List[QA] = []
    last_question: Optional[str] = None
    finished: bool = False


user_states: Dict[int, ChatState] = {}
states_lock = threading.Lock()


# ================== STOMP / WEBSOCKET ==================


def stomp_frame(command: str, headers: Optional[Dict[str, str]] = None, body: str = "") -> str:
    if headers is None:
        headers = {}
    frame = command + "\n"
    for key, value in headers.items():
        frame += f"{key}:{value}\n"
    frame += "\n" + body + "\0"
    return frame


class WebSocketClient:
    """
    Klient WebSocket z komunikacją STOMP.
    Odbiera wiadomości użytkowników i wysyła odpowiedzi AI
    jako DescriptionChatMessage do backendu Javy.
    """

    def __init__(self, uri: str):
        self.uri = uri
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self):
        self.thread.start()
        print("🚀 [WS] Klient WebSocket uruchomiony w tle.")

    def _run_loop(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.uri,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )
                self.ws.run_forever()
            except Exception as e:
                print(f"⚠️ [WS] Błąd wątku: {e}")
                time.sleep(3)

            if self.running:
                print("🔄 [WS] Próba ponownego połączenia za 3s...")
                time.sleep(3)

    def on_open(self, ws):
        print("✅ [WS] Połączono z serwerem.")
        self.connected = True

        connect_frame = stomp_frame(
            "CONNECT",
            headers={
                "accept-version": "1.1,1.2",
                "host": "localhost",
            },
        )
        ws.send(connect_frame)
        time.sleep(0.5)

        sub_frame = stomp_frame(
            "SUBSCRIBE",
            headers={
                "id": "sub-desc-0",
                "destination": "/topic/description",
            },
        )
        ws.send(sub_frame)
        print("🎧 [WS] Zasubskrybowano /topic/description")

    def on_message(self, ws, message: str):
        if message == "\n":
            return

        if "\n\n" not in message:
            print(f"📩 [WS RAW]: {message!r}")
            return

        header, body = message.split("\n\n", 1)
        clean_body = body.replace("\x00", "").strip()

        if not clean_body:
            return

        try:
            data = json.loads(clean_body)

            status_code = data.get("statusCode")
            status_value = data.get("statusCodeValue")
            resp_body = data.get("body", {}) or {}

            user_id = resp_body.get("userId")
            content = resp_body.get("content")

            print("📩 [WS ODBIÓR]:")
            print(f"   status: {status_code} ({status_value})")
            print(f"   userId: {user_id}")
            print(f"   content: {content!r}")

            # rozpoznanie czy to nasza wiadomość AI (żeby nie zrobić pętli)
            is_ai_message = False
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and parsed.get("type") == "AI":
                        is_ai_message = True
                except json.JSONDecodeError:
                    pass

            if is_ai_message:
                print("ℹ️ [WS] Otrzymano wiadomość AI – pomijam (żeby nie wejść w pętlę).")
                return

            if user_id is not None and isinstance(content, str):
                handle_user_message(user_id=int(user_id), user_text=content)
            else:
                print("⚠️ [WS] Brak userId lub content nie jest tekstem – pomijam.")

        except json.JSONDecodeError:
            print(f"⚠️ [WS] Nie udało się zparsować JSON: {clean_body!r}")
        except Exception as e:
            print(f"❌ [WS] Błąd obsługi wiadomości: {e}")

    def on_error(self, ws, error):
        print(f"❌ [WS] Błąd: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 [WS] Rozłączono.")
        self.connected = False

    def send_description(self, user_id: int, content_string: str):
        """
        Wysyła DescriptionChatMessage przez STOMP:
        { "userId": ..., "content": "..." }
        """
        print(
            f"[DEBUG] send_description() called, user_id={user_id}, "
            f"connected={self.connected}, ws_is_not_none={self.ws is not None}"
        )

        if not user_id:
            print("⚠️ [WS] Brak user_id - nie wysyłam wiadomości STOMP.")
            return

        if self.ws and self.connected:
            try:
                payload = {
                    "userId": user_id,
                    "content": content_string,
                }
                body = json.dumps(payload, ensure_ascii=False)
                body_bytes = body.encode("utf-8")

                send_frame = stomp_frame(
                    "SEND",
                    headers={
                        "destination": "/app/description",
                        "content-type": "application/json;charset=UTF-8",
                        "content-length": str(len(body_bytes)),
                    },
                    body=body,
                )

                print(f"[WS] STOMP frame body: {body}")
                self.ws.send(send_frame)
                print(
                    f"📤 [WS WYSŁANO] User: {user_id} | Content len: {len(content_string)}"
                )
            except Exception as e:
                print(f"❌ [WS] Błąd wysyłania: {e}")
        else:
            print("⚠️ [WS] Nie można wysłać - brak połączenia.")


# Inicjalizacja klienta WS
ws_client = WebSocketClient(WS_URI)
ws_client.start()


# ================== FUNKCJA BOTA – iteracyjne budowanie opisu ==================


def refine_description_with_openai(
    description: str,
    transcript: List[QA],
    last_question: str,
    last_answer: str,
) -> Tuple[str, bool, Optional[str]]:
    system_prompt = dedent(
        """
        Jesteś asystentem, który prowadzi rozmowę z użytkownikiem i na jej podstawie
        buduje opis profilu do aplikacji społecznościowej.

        TEN OPIS MA BYĆ PODSTAWĄ DO WYCIĄGANIA CECH DO GRUPOWANIA UŻYTKOWNIKÓW:
        - rodzaje aktywności / zainteresowań (ale nie pytaj o to zawsze wprost),
        - styl / intensywność (luźno vs ambitnie, rywalizacja vs chill),
        - preferowany typ grupy i atmosfery (małe grupy vs większe, spokojnie vs głośno),
        - ogólna lokalizacja / kontekst (np. centrum, dzielnica, miasto, typ miejsc).

        WAŻNE:
        - Twoje pytania nie mogą być cały czas takie same.
        - Nie pytaj tylko sucho o "aktywności".
        - Możesz dopytywać o:
          * przykładowe sytuacje ("jak wygląda idealne spotkanie z ludźmi?"),
          * towarzystwo ("z jakimi osobami najlepiej się dogadujesz?"),
          * klimat ("raczej głośne miejsca czy spokojne rozmowy?"),
          * miejsca ("bardziej parki, miasto, kawiarnie, ścianka wspinaczkowa?").
        - Pytania mają brzmieć naturalnie i po ludzku, po polsku.

        TWOJE ZADANIE W TYM KROKU:
        1) Weź dotychczasowy opis oraz ostatnią odpowiedź użytkownika i zaktualizuj opis tak, aby:
           - był spójny,
           - zawierał kluczowe informacje z całej rozmowy,
           - miał maksymalnie 3–4 zdania.
        2) Oceń, czy na podstawie tego opisu da się już zbudować sensowny wektor cech do grupowania użytkowników
           (aktywności, styl, grupa, klimat, miejsca).
           Jeśli tak → sufficient = true.
           Jeśli nie → sufficient = false i wygeneruj jedno konkretne, DOPEŁNIAJĄCE pytanie.

        FORMAT ODPOWIEDZI:
        Zwróć TYLKO czysty JSON, bez żadnych komentarzy, bez markdown:
        {
          "new_description": "...",
          "sufficient": true/false,
          "next_question": "..." albo null
        }
        """
    ).strip()

    if transcript:
        conv_lines = []
        for i, qa in enumerate(transcript, start=1):
            conv_lines.append(f"Pytanie {i}: {qa.question}")
            conv_lines.append(f"Odpowiedź {i}: {qa.answer}")
        conv_text = "\n".join(conv_lines)
    else:
        conv_text = "(Brak wcześniejszych pytań i odpowiedzi - to początek rozmowy.)"

    user_prompt = dedent(
        f"""
        DOTYCHCZASOWY OPIS PROFILU:
        {description or "(brak opisu - tworzysz go od zera)"}

        HISTORIA ROZMOWY:
        {conv_text}

        OSTATNI KROK:
        Pytanie: {last_question}
        Odpowiedź: {last_answer}

        Na tej podstawie:
        1) Zaktualizuj opis (pole new_description),
        2) Oceń sufficient (czy opis jest już wystarczający),
        3) Jeśli nie, zaproponuj next_question - naturalne, konkretne pytanie,
           które pomoże dodać brakujące informacje (ale nie musi być wprost o "zainteresowaniach").
        PAMIĘTAJ: zwracasz tylko surowy JSON, bez innych treści.
        """
    ).strip()

    print("[FLOW] refine_description_with_openai() – wywołanie modelu")
    print(f"[FLOW] last_question: {last_question}")
    print(f"[FLOW] last_answer:  {last_answer}")
    print(f"[FLOW] prev_description: {description}\n")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=300,
    )

    raw_content = response.choices[0].message.content.strip()
    print(f"[DEBUG] OpenAI (refine) raw content: {raw_content!r}")

    json_str = None
    if raw_content.startswith("{"):
        json_str = raw_content
    else:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = raw_content[start: end + 1]

    try:
        if not json_str:
            raise ValueError("Nie udało się wyodrębnić JSON z odpowiedzi modelu.")
        data = json.loads(json_str)

        new_description = data.get("new_description", description) or description
        sufficient = bool(data.get("sufficient", False))
        next_question = data.get("next_question")

        print(f"[LOG] new_description: {new_description}")
        print(f"[LOG] sufficient: {sufficient}")
        print(f"[LOG] next_question: {next_question}\n")

    except Exception as e:
        print(f"[WARN] Błąd parsowania JSON z OpenAI: {e}. raw_content={raw_content!r}")
        new_description = description or last_answer
        sufficient = False
        next_question = (
            "Czy mógłbyś opisać trochę dokładniej, z jakimi ludźmi i w jakich miejscach "
            "najbardziej lubisz spędzać czas?"
        )

    if len(transcript) < 2:
        print("[LOG] Mniej niż 2 Q/A – sufficient ustawione na False (za mało danych).")
        sufficient = False

    if not sufficient and (not next_question or next_question.strip() == ""):
        next_question = (
            "Dodaj proszę jeszcze coś o tym, jakie sytuacje lubisz najbardziej "
            "np. spokojne rozmowy w kawiarni, wypad w góry, planszówki, sporty itp."
        )
        print("[LOG] Brak next_question – ustawiam awaryjne pytanie.")

    return new_description, sufficient, next_question


# ================== GŁÓWNA LOGIKA – OBSŁUGA WIADOMOŚCI UŻYTKOWNIKA ==================


def handle_user_message(user_id: int, user_text: str):
    print(f"\n[FLOW] handle_user_message(user_id={user_id}, user_text={user_text!r})")

    with states_lock:
        state = user_states.get(user_id)
        if state is None or state.finished:
            print(f"[LOG] Tworzę nowy ChatState dla user_id={user_id}")
            state = ChatState()
            user_states[user_id] = state

    # Pierwsza wiadomość
    if not state.last_question and not state.transcript:
        print("[FLOW] Pierwsza wiadomość w rozmowie (syntetyczne pytanie startowe).")
        synthetic_question = (
            "Na początek opisz w 2–3 zdaniach, jak lubisz spędzać czas z innymi ludźmi "
            "i czego szukasz w takich spotkaniach?"
        )
        qa = QA(question=synthetic_question, answer=user_text)
        state.transcript.append(qa)

        new_description, sufficient, next_question = refine_description_with_openai(
            description=state.description,
            transcript=state.transcript,
            last_question=synthetic_question,
            last_answer=user_text,
        )

        state.description = new_description

        if sufficient:
            print("[FLOW] Model uznał opis za wystarczający już po pierwszej wiadomości.")
            state.finished = True
            state.last_question = None

            ai_message = {
                "type": "AI",
                "finished": True,
                "finalDescription": new_description,
            }

            print("[FLOW] Wysyłam finalDescription po WebSocket...")
            ws_client.send_description(
                user_id=user_id,
                content_string=json.dumps(ai_message, ensure_ascii=False),
            )

            print("[FLOW] Wywołuję zapis finalDescription + traits do backendu...")
            send_final_description_to_backend(user_id, new_description)

        else:
            print("[FLOW] Model potrzebuje więcej danych – wysyłam pytanie doprecyzowujące.")
            state.finished = False
            state.last_question = next_question

            ai_message = {
                "type": "AI",
                "finished": False,
                "botMessage": next_question,
                "currentDescription": new_description,
            }

            ws_client.send_description(
                user_id=user_id,
                content_string=json.dumps(ai_message, ensure_ascii=False),
            )

        with states_lock:
            user_states[user_id] = state
        return

    # Kolejne wiadomości
    if not state.last_question:
        print(f"⚠️ [BOT] Brak last_question dla user_id={user_id}. Resetuję stan.")
        state = ChatState()
        with states_lock:
            user_states[user_id] = state
        handle_user_message(user_id=user_id, user_text=user_text)
        return

    print(f"[FLOW] Odpowiedź na pytanie: {state.last_question!r}")
    qa = QA(question=state.last_question, answer=user_text)
    state.transcript.append(qa)

    new_description, sufficient, next_question = refine_description_with_openai(
        description=state.description,
        transcript=state.transcript,
        last_question=state.last_question,
        last_answer=user_text,
    )

    state.description = new_description

    if sufficient:
        print("[FLOW] Model uznał, że opis jest już wystarczający – kończę rozmowę.")
        state.finished = True
        state.last_question = None

        ai_message = {
            "type": "AI",
            "finished": True,
            "finalDescription": new_description,
        }

        print("[FLOW] Wysyłam finalDescription po WebSocket...")
        ws_client.send_description(
            user_id=user_id,
            content_string=json.dumps(ai_message, ensure_ascii=False),
        )

        print("[FLOW] Wywołuję zapis finalDescription + traits do backendu...")
        send_final_description_to_backend(user_id, new_description)
    else:
        print("[FLOW] Model nadal potrzebuje doprecyzowania – zadaję kolejne pytanie.")
        state.finished = False
        state.last_question = next_question

        ai_message = {
            "type": "AI",
            "finished": False,
            "botMessage": next_question,
            "currentDescription": new_description,
        }

        ws_client.send_description(
            user_id=user_id,
            content_string=json.dumps(ai_message, ensure_ascii=False),
        )

    with states_lock:
        user_states[user_id] = state


# ================== ENDPOINT DIAGNOSTYCZNY ==================


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "ProfilBot Conversation API działa (iteracyjny opis, WebSocket-driven, traits->Java)",
    }
