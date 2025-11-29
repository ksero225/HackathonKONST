import os
from textwrap import dedent
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

# Wczytaj zmienne środowiskowe z .env (w tym OPENAI_API_KEY)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Brak zmiennej środowiskowej OPENAI_API_KEY (sprawdź plik .env)")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(
    title="ProfilBot Conversation API",
    description="Dynamiczny bot do rozmowy i iteracyjnego budowania opisu profilu",
    version="0.4.1",
)

# ===== MODELE DANYCH =====


class QA(BaseModel):
    question: str
    answer: str


class ChatState(BaseModel):
    # aktualny opis profilu
    description: str = ""
    # historia pytań/odpowiedzi (pełny wywiad)
    transcript: List[QA] = []
    # ostatnie pytanie zadane przez bota, na które user właśnie odpowiada
    last_question: Optional[str] = None
    # czy rozmowa została zakończona (opis zaakceptowany przez model)
    finished: bool = False


class StartResponse(BaseModel):
    bot_message: str
    state: ChatState
    # podgląd opisu (na starcie pusty)
    current_description: str


class ChatRequest(BaseModel):
    user_message: str
    state: ChatState


class ChatResponse(BaseModel):
    bot_message: str
    state: ChatState
    is_finished: bool
    final_description: Optional[str] = None  # tylko przy zakończeniu
    # zawsze zwracamy aktualny opis jako podgląd
    current_description: str


# ===== FUNKCJE POMOCNICZE Z OPENAI =====


def refine_description_with_openai(
    description: str,
    transcript: List[QA],
    last_question: str,
    last_answer: str,
) -> tuple[str, bool, Optional[str]]:
    """
    Jeden krok iteracji:
    - mamy aktualny opis (description),
    - pełny transcript (wszystkie Q/A),
    - ostatnie pytanie i odpowiedź.

    OpenAI:
    - aktualizuje opis na podstawie nowej odpowiedzi,
    - ocenia, czy opis jest już wystarczający do wyciągnięcia cech,
    - jeśli NIE: generuje kolejne, bardziej finezyjne pytanie doprecyzowujące.

    Zwraca:
    - new_description (str)
    - sufficient (bool)
    - next_question (str | None)
    """

    system_prompt = dedent("""
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
    1) Weź dotychczasowy opis oraz ostatnią odpowiedź użytkownika
       i zaktualizuj opis tak, aby:
       - był spójny,
       - zawierał kluczowe informacje z całej rozmowy,
       - miał maksymalnie 3–4 zdania.

    2) Oceń, czy na podstawie tego opisu da się już zbudować sensowny
       wektor cech do grupowania użytkowników (aktywnosci, styl, grupa, klimat, miejsca).
       Jeśli tak → sufficient = true.
       Jeśli nie → sufficient = false i wygeneruj jedno konkretne,
       DOPEŁNIAJĄCE pytanie.

    FORMAT ODPOWIEDZI:
    Zwróć TYLKO czysty JSON:
    {
      "new_description": "...",
      "sufficient": true/false,
      "next_question": "..." albo null
    }
    Bez żadnych dodatkowych komentarzy.
    """).strip()

    # Tekstowy zapis transcriptu (historia rozmowy)
    if transcript:
        conv_lines = []
        for i, qa in enumerate(transcript, start=1):
            conv_lines.append(f"Pytanie {i}: {qa.question}")
            conv_lines.append(f"Odpowiedź {i}: {qa.answer}")
        conv_text = "\n".join(conv_lines)
    else:
        conv_text = "(Brak wcześniejszych pytań i odpowiedzi - to początek rozmowy.)"

    user_prompt = dedent(f"""
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
    3) Jeśli nie, zaproponuj next_question - naturalne, konkretne pytanie, które
       pomoże dodać brakujące informacje (ale nie musi być wprost o "zainteresowaniach").
    """).strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=300,
    )

    import json
    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)
        new_description = data.get("new_description", description) or description
        sufficient = bool(data.get("sufficient", False))
        next_question = data.get("next_question")
    except Exception:
        # awaryjnie: jeśli model zwróci coś dziwnego, zachowujemy stary opis
        new_description = description or last_answer
        sufficient = False
        next_question = (
            "Czy mógłbyś opisać trochę dokładniej, z jakimi ludźmi i w jakich miejscach "
            "najbardziej lubisz spędzać czas?"
        )

    # Bezpieczeństwo: minimalnie 2 Q/A zanim pozwolimy zakończyć
    if len(transcript) < 2:
        sufficient = False

    # Jeśli insufficient, a pytania brak → daj awaryjne pytanie
    if not sufficient and (not next_question or next_question.strip() == ""):
        next_question = (
            "Dodaj proszę jeszcze coś o tym, jakie sytuacje lubisz najbardziej "
            "np. spokojne rozmowy w kawiarni, wypad w góry, planszówki, sporty itp."
        )

    return new_description, sufficient, next_question


# ===== ENDPOINTY API =====


@app.get("/")
def root():
    return {"status": "ok", "message": "ProfilBot Conversation API działa (iteracyjny opis)"}


@app.post("/start-profile", response_model=StartResponse)
def start_profile():
    """
    Start rozmowy:
    - opis pusty,
    - transcript pusty,
    - bot prosi o pierwszy ogólny opis użytkownika.
    """
    state = ChatState(
        description="",
        transcript=[],
        last_question=(
            "Na początek opisz w 2–3 zdaniach, jak lubisz spędzać czas z innymi ludźmi "
            "i czego szukasz w takich spotkaniach?"
        ),
        finished=False,
    )

    return StartResponse(
        bot_message=state.last_question,
        state=state,
        current_description=state.description,
    )


@app.post("/chat-profile", response_model=ChatResponse)
def chat_profile(req: ChatRequest):
    """
    Jeden krok rozmowy:
    - przyjmuje wiadomość użytkownika + stan,
    - dodaje Q/A do transcriptu,
    - woła OpenAI, aby:
        * zaktualizował opis,
        * ocenił, czy opis jest wystarczający,
        * ewentualnie wygenerował kolejne pytanie.
    """
    state = req.state
    user_message = req.user_message.strip()

    # jeśli już zakończone
    if state.finished:
        return ChatResponse(
            bot_message="Rozmowa już została zakończona. Możesz rozpocząć nową, wywołując /start-profile.",
            state=state,
            is_finished=True,
            final_description=state.description,
            current_description=state.description,
        )

    # musimy mieć ostatnie pytanie, żeby stworzyć parę Q/A
    if not state.last_question:
        return ChatResponse(
            bot_message="Coś poszło nie tak z kontekstem rozmowy. Zacznij proszę od nowa wywołując /start-profile.",
            state=state,
            is_finished=True,
            final_description=None,
            current_description=state.description,
        )

    # dopisujemy Q/A do transcriptu
    qa = QA(question=state.last_question, answer=user_message)
    state.transcript.append(qa)

    # wołamy OpenAI, żeby:
    # - zaktualizował opis,
    # - sprawdził, czy już wystarczy,
    # - podał ewentualnie kolejne pytanie
    new_description, sufficient, next_question = refine_description_with_openai(
        description=state.description,
        transcript=state.transcript,
        last_question=state.last_question,
        last_answer=user_message,
    )

    state.description = new_description

    if sufficient:
        state.finished = True
        state.last_question = None

        bot_message = (
            "Na podstawie naszej rozmowy przygotowałem taki opis Twojego profilu:\n\n"
            f"{new_description}\n\n"
            "Możesz go zapisać w swoim profilu. Jeśli kiedyś będziesz chciał coś zmienić, "
            "wystarczy rozpocząć nową rozmowę."
        )

        return ChatResponse(
            bot_message=bot_message,
            state=state,
            is_finished=True,
            final_description=new_description,
            current_description=new_description,
        )
    else:
        # kolejne pytanie doprecyzowujące
        state.last_question = next_question

        # front może sam zdecydować, czy wyświetlać sam opis czy opis + pytanie,
        # dlatego opis zwracamy jako osobne pole.
        bot_message = next_question

        return ChatResponse(
            bot_message=bot_message,
            state=state,
            is_finished=False,
            final_description=None,
            current_description=new_description,
        )
