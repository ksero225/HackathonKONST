import os
import json
import threading
import time
from textwrap import dedent
from typing import Optional, List, Dict

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

import websocket  # klient WebSocket/STOMP
import requests   # HTTP do backendu Javy
import re
import numpy as np

# ================== KONFIG OPENAI / .ENV ==================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Brak zmiennej środowiskowej OPENAI_API_KEY (sprawdź plik .env)")

client = OpenAI(api_key=OPENAI_API_KEY)

# JAVA_BASE_URL z .env
JAVA_BASE_URL = os.getenv("JAVA_BASE_URL")
if not JAVA_BASE_URL:
    raise RuntimeError("Brak zmiennej środowiskowej JAVA_BASE_URL (dodaj do .env)")

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


def stomp_frame(command, headers=None, body: str = "") -> str:
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
        self.ws = None
        self.connected = False
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True

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

    def on_message(self, ws, message):
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


WS_URI = os.getenv("WS_URI", "wss://continuable-manuela-podgy.ngrok-free.dev/ws")
ws_client = WebSocketClient(WS_URI)
ws_client.start()

# ================== MODEL CECH ==================


class ProfileFeatures(BaseModel):
    activities: List[str] = []
    style_intensity: Optional[str] = None
    style_competition: Optional[str] = None
    group_size: Optional[str] = None
    atmosphere: Optional[str] = None
    location_hint: Optional[str] = None
    tags: List[str] = []

    lat: Optional[float] = None
    lon: Optional[float] = None


def normalize_feature_name(name: str) -> str:
    if not name:
        return name
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = name.replace(" ", "_")
    name = re.sub(r"[^0-9a-ząćęłńóśźż_]", "", name)
    return name


def normalize_profile_features(p: ProfileFeatures) -> ProfileFeatures:
    return ProfileFeatures(
        activities=[normalize_feature_name(a) for a in p.activities],
        style_intensity=p.style_intensity,
        style_competition=p.style_competition,
        group_size=p.group_size,
        atmosphere=p.atmosphere,
        location_hint=p.location_hint,
        tags=[normalize_feature_name(t) for t in p.tags],
        lat=p.lat,
        lon=p.lon,
    )


def extract_features_from_description(description: str) -> ProfileFeatures:
    system_prompt = dedent("""
    Jesteś asystentem, który z gotowego opisu profilu użytkownika wyciąga cechy do grupowania ludzi w aplikacji społecznościowej.

    TWOJE ZADANIE:
    - Przeczytaj opis profilu (po polsku).
    - Wyciągnij z niego kluczowe informacje:
      * aktywności / zainteresowania (lista fraz),
      * styl/intensywność: bardziej spokojnie czy ambitnie,
      * czy szuka raczej chillowego klimatu, czy rywalizacji,
      * w jakiej wielkości grupie czuje się najlepiej,
      * jaki klimat spotkań preferuje (spokojnie/energicznie),
      * co da się wywnioskować o lokalizacji / typowych miejscach,
      * proste tagi (np. "bieganie", "planszówki", "kawa", "mała_grupa", "spokojnie", itp.).

    ZWRÓĆ TYLKO CZYSTY JSON O STRUKTURZE:
    {
      "activities": [lista stringów],
      "style_intensity": "spokojnie" | "ambitnie" | "mieszane" | null,
      "style_competition": "chill" | "rywalizacja" | "mieszane" | null,
      "group_size": "małe" | "średnie" | "duże" | null,
      "atmosphere": "spokojnie" | "energicznie" | "mieszane" | null,
      "location_hint": string lub null,
      "tags": [lista stringów]
    }

    Nie dodawaj żadnych komentarzy poza JSON-em.
    """).strip()

    user_prompt = (
        f"Oto opis profilu użytkownika:\n\n{description}\n\n"
        f"Wyodrębnij cechy zgodnie z formatem."
    )

    print(f"[LOG] Ekstrakcja cech z opisu (finalDescription):\n{description}\n")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=300,
    )

    content = response.choices[0].message.content.strip()
    print(f"[DEBUG] OpenAI (extract_features) raw content: {content!r}")

    try:
        data = json.loads(content)
    except Exception:
        print("⚠️ Model zwrócił coś, co nie jest JSON-em. Zwracam puste cechy.")
        return ProfileFeatures()

    features = ProfileFeatures(
        activities=data.get("activities") or [],
        style_intensity=data.get("style_intensity"),
        style_competition=data.get("style_competition"),
        group_size=data.get("group_size"),
        atmosphere=data.get("atmosphere"),
        location_hint=data.get("location_hint"),
        tags=data.get("tags") or [],
    )

    print(f"[LOG] Surowe cechy wyekstrahowane z opisu: {features}")
    return features


def is_sparse_description(description: str) -> bool:
    return len(description.split()) < 5


def build_tag_index(profiles: List[ProfileFeatures]) -> Dict[str, int]:
    all_tags = set()
    for p in profiles:
        all_tags.update(p.tags)
        all_tags.update(p.activities)
    tag_index = {tag: i for i, tag in enumerate(sorted(all_tags))}
    print(f"[LOG] Zbudowano tag_index (tag -> index): {tag_index}")
    return tag_index


def profile_to_vector(profile: ProfileFeatures, tag_index: Dict[str, int]) -> np.ndarray:
    v = np.zeros(len(tag_index), dtype=float)

    for act in profile.activities:
        if act in tag_index:
            idx = tag_index[act]
            v[idx] = max(v[idx], 1.0)

    for tag in profile.tags:
        if tag in tag_index:
            idx = tag_index[tag]
            v[idx] = max(v[idx], 0.7)

    if profile.style_intensity == "ambitnie":
        v *= 1.1

    max_val = v.max()
    if max_val > 0:
        v = v / max_val

    print(f"[LOG] Wektor cech (bez sparse): {v}")
    return v


def profile_to_vector_with_sparse_flag(
    profile: ProfileFeatures,
    tag_index: Dict[str, int],
    description: str,
) -> np.ndarray:
    v = profile_to_vector(profile, tag_index)
    if is_sparse_description(description):
        print("[LOG] Opis jest krótki ('skąpy') – obniżam wagi x0.5")
        v *= 0.5
    print(f"[LOG] Wektor cech (po sparse flag): {v}")
    return v


def vector_to_readable_dict(v: np.ndarray, tag_index: Dict[str, int]) -> Dict[str, float]:
    idx_to_tag = {idx: tag for tag, idx in tag_index.items()}
    result = {}
    for idx, val in enumerate(v):
        if val > 0:
            tag = idx_to_tag[idx]
            result[tag] = round(float(val), 2)
    print(f"[LOG] traits (tag -> wartość): {result}")
    return result


def send_final_description_to_backend(user_id: int, final_description: str):
    """
    1) Wyciąga cechy z final_description,
    2) Buduje wektor,
    3) Zamienia na mapę traits,
    4) Wysyła POST na /api/users/{userId}/description
    + LOGI na każdym etapie.
    """
    print("\n================= [FLOW] ZAPIS OPISU DO BACKENDU =================")
    print(f"[FLOW] user_id={user_id}")
    print(f"[FLOW] finalDescription:\n{final_description}\n")

    try:
        # 1. Ekstrakcja cech
        raw_features = extract_features_from_description(final_description)
        print(f"[LOG] raw_features (przed normalizacją): {raw_features}")

        features = normalize_profile_features(raw_features)
        print(f"[LOG] features (po normalizacji): {features}")

        # 2. Tag index na podstawie cech tego użytkownika
        tag_index = build_tag_index([features])

        # 3. Wektor
        vec = profile_to_vector_with_sparse_flag(features, tag_index, final_description)

        # 4. traits (czytelny słownik)
        traits = vector_to_readable_dict(vec, tag_index)

        payload = {
            "text": final_description,
            "traits": traits,
        }

        url = f"{JAVA_BASE_URL}/api/users/{user_id}/description"
        print(f"[HTTP] POST {url}")
        print(f"[HTTP] Payload JSON: {json.dumps(payload, ensure_ascii=False)}")

        resp = requests.put(url, json=payload)
        print(f"[HTTP] Odpowiedź backendu: {resp.status_code}")
        print(f"[HTTP] Body odpowiedzi: {resp.text}")
        print("================= [FLOW] ZAPIS OPISU ZAKOŃCZONY =================\n")

    except Exception as e:
        print(f"❌ [HTTP] Błąd wysyłania opisu do backendu: {e}")


# ================== FUNKCJA BOTA – iteracyjne budowanie opisu ==================


def refine_description_with_openai(
    description: str,
    transcript: List[QA],
    last_question: str,
    last_answer: str,
) -> tuple[str, bool, Optional[str]]:
    system_prompt = dedent(
        """
        Jesteś asystentem, który prowadzi rozmowę z użytkownikiem i na jej podstawie
        buduje opis profilu do aplikacji społecznościowej.

        TEN OPIS MA BYĆ PODSTAWĄ DO WYCIĄGANIA CECH DO GRUPOWANIA UŻYTKOWNIKÓW:
        - rodzaje aktywności / zainteresowań (ale nie pytaj o to zawsze wprost),
        - styl / intensywność (luźno vs ambitnie, rywalizacja vs chill),
        - preferowany typ grupy i atmosfery (małe grupы vs większe, spokojnie vs głośno),
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
