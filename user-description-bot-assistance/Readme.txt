# User Description & KNN Grouping – Submodule

To repozytorium jest częścią większego projektu Hackathon KONST.  
Zawiera dwa niezależne serwisy:

1. **Bot opisujący użytkownika (Conversation Service)**
2. **KNN Grouping – grupowanie użytkowników**

Każdy z nich ma własny skrypt startowy `.bat`, dzięki czemu można je uruchomić jednym kliknięciem.

---

## 📌 Wymagania

Przed uruchomieniem:

1. Musi istnieć wirtualne środowisko `venv`
2. Muszą być zainstalowane zależności (pip install -r requirements.txt)
3. W katalogu projektu musi znajdować się plik `.env`, zawierający m.in.:

OPENAI_API_KEY=
SPRING_WS_URI=
SPRING_WS_HOST_HEADER=
JAVA_BASE_URL=

# 🚀 1. BOT SERVICE  
*(iteracyjne tworzenie opisu użytkownika + wysyłka do backendu)*

Bot:

- otrzymuje wiadomości użytkownika z Javy przez WebSocket,
- prowadzi mini-wywiad,
- buduje opis profilu (w 2–4 zdaniach),
- generuje cechy (traits) przy użyciu OpenAI,
- zapisuje je w backendzie Javy,
- odsyła AI-odpowiedzi z powrotem przez WebSocket.

### ▶ Jak uruchomić?

W głównym katalogu:

Skrypt:

start_service.bat

- aktywuje `venv`,
- odpala FastAPI + klienta WebSocket,
- zaczyna nasłuch na /topic/description.

Diagnostyczny endpoint dostępny jest pod:

http://localhost:8000/

---

# 🧠 2. KNN GROUPING  
*(grupowanie użytkowników w grupy 3–8 osób)*

Serwis:

1. pobiera cechy użytkowników z backendu Javy (`/api/users/features`),
2. buduje wektory cech (w tym geolokalizacja),
3. grupuje użytkowników:
   - KMeans + dostosowanie rozmiarów grup,
   - każda grupa ma **min 3**, **max 8 osób**,
4. wylicza `topTraits` dla każdej grupy,
5. zapisuje wynik do pliku `users_knn_groups.json`,
6. wysyła grupy do Javy przez WebSocket (`/app/groups`).

### ▶ Jak uruchomić?

W głównym katalogu:

knn_start.bat

Skrypt:

- aktywuje `venv`,
- uruchamia logikę grupowania (`python -m knn_gruping.main`),
- wypisuje logi w konsoli,
- wysyła grupy z powrotem do backendu.

---

# 📂 Struktura katalogu (fragment)

---

# ℹ Uwagi

- Ten moduł **nie jest samodzielną aplikacją** — współpracuje z backendem Javy.
- Oba serwisy korzystają z WebSocket/STOMP.
- `OPENAI_API_KEY` musi być poprawny, inaczej bot nie zadziała.

---

# ✔ Podsumowanie

| Usługa | Start | Opis |
|--------|--------|-------|
| **Bot service** | `start_service.bat` | Prowadzi rozmowę, tworzy opis, generuje cechy, wysyła do backendu |
| **KNN grouping** | `knn_start.bat` | Grupuje użytkowników (3–8 osób), zapisuje wynik i wysyła do backendu |









