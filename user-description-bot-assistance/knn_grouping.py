import os
import json
import math
import threading
import time
from typing import Dict, List, Tuple

import numpy as np
import requests
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import websocket  # klient WebSocket/STOMP

# ================== KONFIGURACJA / .ENV ==================

load_dotenv()

JAVA_BASE_URL = os.getenv("JAVA_BASE_URL")
if not JAVA_BASE_URL:
    raise RuntimeError("Brak zmiennej środowiskowej JAVA_BASE_URL (dodaj do .env)")

FEATURES_PATH = "/api/users/features"

OUTPUT_GROUPS_FILE = "users_knn_groups.json"

# GEO – wzmocnienie wpływu lokalizacji
GEO_WEIGHT = 3.0

# Zakres liczby klastrów względem liczby userów
MIN_CLUSTER_RATIO = 0.14
MAX_CLUSTER_RATIO = 0.35

# WS URI
WS_URI = os.getenv("WS_URI", "wss://continuable-manuela-podgy.ngrok-free.dev/ws")


# ================== STOMP / WEBSOCKET DO WYSYŁANIA GRUP ==================


def stomp_frame(command, headers=None, body: str = "") -> str:
    if headers is None:
        headers = {}
    frame = command + "\n"
    for key, value in headers.items():
        frame += f"{key}:{value}\n"
    frame += "\n" + body + "\0"
    return frame


class GroupsWebSocketClient:
    """
    Prosty klient WS/STOMP tylko do:
    - CONNECT
    - SUBSCRIBE na /topic/groups (podgląd odpowiedzi)
    - SEND na /app/groups  (trafia w @MessageMapping("/groups"))
    """

    def __init__(self, uri: str):
        self.uri = uri
        self.ws = None
        self.connected = False

    def connect(self):
        def _run():
            self.ws = websocket.WebSocketApp(
                self.uri,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
            self.ws.run_forever()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        time.sleep(1.5)

    def on_open(self, ws):
        print("✅ [WS-GROUPS] Połączono z serwerem.")
        self.connected = True

        connect_frame = stomp_frame(
            "CONNECT",
            headers={
                "accept-version": "1.1,1.2",
                "host": "localhost",
            },
        )
        ws.send(connect_frame)
        time.sleep(0.3)

        sub_frame = stomp_frame(
            "SUBSCRIBE",
            headers={
                "id": "sub-groups-0",
                "destination": "/topic/groups",
            },
        )
        ws.send(sub_frame)
        print("🎧 [WS-GROUPS] Zasubskrybowano /topic/groups")

    def on_message(self, ws, message):
        if message == "\n":
            return

        if "\n\n" in message:
            header, body = message.split("\n\n", 1)
            clean_body = body.replace("\x00", "").strip()
            if clean_body:
                print(f"📩 [WS-GROUPS ODBIÓR]: {clean_body[:200]}...")

    def on_error(self, ws, error):
        print(f"❌ [WS-GROUPS] Błąd: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 [WS-GROUPS] Rozłączono.")
        self.connected = False

    def send_groups(self, groups_payload: List[dict]):
        """
        Wysyła listę obiektów:
        {
          "groupId": ...,
          "users": [...],
          "topTraits": [...],
          "latitude": ...,
          "longitude": ...
        }
        do @MessageMapping("/groups") -> /app/groups
        """
        if not self.ws or not self.connected:
            print("⚠️ [WS-GROUPS] Brak połączenia – nie wysyłam.")
            return

        try:
            body = json.dumps(groups_payload, ensure_ascii=False)
            body_bytes = body.encode("utf-8")

            send_frame = stomp_frame(
                "SEND",
                headers={
                    "destination": "/app/groups",
                    "content-type": "application/json;charset=UTF-8",
                    "content-length": str(len(body_bytes)),
                },
                body=body,
            )

            print(f"[WS-GROUPS] STOMP SEND frame body (skrót): {body[:200]}...")
            self.ws.send(send_frame)
            print(f"📤 [WS-GROUPS WYSŁANO] {len(groups_payload)} grup.")
        except Exception as e:
            print(f"❌ [WS-GROUPS] Błąd wysyłania: {e}")


# ================== POBIERANIE DANYCH Z BACKENDU ==================


def fetch_features_from_backend():
    url = f"{JAVA_BASE_URL}{FEATURES_PATH}"
    print(f"[HTTP] GET {url}")

    try:
        resp = requests.get(url)
        print(f"[HTTP] Status: {resp.status_code}")

        try:
            data = resp.json()
        except ValueError:
            print("❌ [HTTP] Odpowiedź nie jest poprawnym JSON-em:")
            print(resp.text)
            return None

        print("[LOG] Przykładowe dane (pierwsze 1–2 rekordy):")
        if isinstance(data, list):
            print(json.dumps(data[:2], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))

        return data

    except requests.RequestException as e:
        print(f"❌ [HTTP] Błąd podczas wywołania endpointu: {e}")
        return None


# ================== POMOCNICZE: WYCIĄGANIE CECH ==================


def extract_traits_from_record(rec: dict) -> Dict[str, float]:
    """
    Z wejścia:
    {
      "userId": ...,
      "topTraits": { "bieganie": 0.9, "jachty": 0.8, ... },
      ...
    }
    wyciąga dict cech -> waga.
    """
    traits = rec.get("traits")
    if isinstance(traits, dict) and traits:
        return {str(k): float(v) for k, v in traits.items()}

    top_traits = rec.get("topTraits")
    if isinstance(top_traits, dict) and top_traits:
        return {str(k): float(v) for k, v in top_traits.items()}

    if isinstance(top_traits, list) and top_traits:
        return {str(name): 1.0 for name in top_traits}

    return {}


# ================== BUDOWANIE WEKTORÓW CECH ==================


def build_trait_index(users_data: List[dict]) -> Dict[str, int]:
    all_traits = set()

    for rec in users_data:
        traits = extract_traits_from_record(rec)
        for t in traits.keys():
            all_traits.add(t)

    trait_index = {trait: i for i, trait in enumerate(sorted(all_traits))}
    print(f"[LOG] Zbudowano trait_index (trait -> index), liczba cech: {len(trait_index)}")
    return trait_index


def build_feature_matrix(
    users_data: List[dict],
    trait_index: Dict[str, int],
    geo_weight: float = GEO_WEIGHT,
) -> Tuple[np.ndarray, List[int]]:
    num_users = len(users_data)
    num_traits = len(trait_index)

    matrix = np.zeros((num_users, num_traits + 2), dtype=float)
    user_ids: List[int] = []

    for row_idx, rec in enumerate(users_data):
        user_id = rec.get("userId")
        user_ids.append(user_id)

        traits = extract_traits_from_record(rec)
        for name, val in traits.items():
            if name in trait_index:
                col = trait_index[name]
                matrix[row_idx, col] = float(val)

        lat = rec.get("latitude") or 0.0
        lon = rec.get("longitude") or 0.0

        matrix[row_idx, num_traits] = float(lat) * geo_weight
        matrix[row_idx, num_traits + 1] = float(lon) * geo_weight

    print(
        f"[LOG] Zbudowano macierz cech: shape={matrix.shape}, liczba userów={len(user_ids)}"
    )
    return matrix, user_ids


# ================== KMEANS ==================
def split_into_chunks_with_range(total: int, min_size: int = 3, max_size: int = 8) -> List[int]:
    """
    Dzieli liczbę 'total' na listę rozmiarów grup z zakresu [min_size, max_size].
    Stara się nie zostawiać resztki 1–2.
    """
    sizes = []
    remaining = total

    while remaining > 0:
        # jeśli to, co zostało, mieści się w zakresie – bierzemy całość
        if min_size <= remaining <= max_size:
            sizes.append(remaining)
            break

        chosen = None
        # wybieramy największą możliwą grupę, która nie zostawi reszty < min_size
        for k in range(max_size, min_size - 1, -1):
            rest = remaining - k
            if rest == 0 or rest >= min_size:
                chosen = k
                break

        if chosen is None:
            # fallback – nie powinno się zdarzyć w normalnych danych,
            # ale na wszelki wypadek bierzemy wszystko
            sizes.append(remaining)
            break

        sizes.append(chosen)
        remaining -= chosen

    return sizes


def compute_kmeans_groups(
    matrix: np.ndarray,
    user_ids: List[int],
) -> List[List[int]]:
    num_users = matrix.shape[0]
    if num_users == 0:
        return []

    # Jeżeli userów jest bardzo mało, nie ma jak zrobić grup po 3 osoby
    if num_users < 3:
        return [user_ids.copy()]

    # --- 1. Szukanie najlepszego k (jak było) ---
    min_k = max(2, int(math.ceil(num_users * MIN_CLUSTER_RATIO)))
    max_k = int(math.ceil(num_users * MAX_CLUSTER_RATIO))
    max_k = max(min_k, max_k)
    max_k = min(max_k, num_users)

    print(f"[KMEANS] Testuję k w zakresie [{min_k}, {max_k}]")

    best_k = None
    best_score = -1.0
    best_labels = None

    for k in range(min_k, max_k + 1):
        print(f"[KMEANS] Próbuję k={k}...")
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(matrix)

        if len(set(labels)) < 2:
            print(f"[KMEANS] k={k} dał 1 klaster – pomijam w ocenie.")
            continue

        score = silhouette_score(matrix, labels)
        print(f"[KMEANS] k={k}, silhouette_score={score:.4f}")

        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels

    if best_k is None:
        print("[KMEANS] Nie udało się policzyć silhouette_score – używam min_k jako fallback.")
        best_k = min_k
        kmeans = KMeans(n_clusters=best_k, n_init=10, random_state=42)
        best_labels = kmeans.fit_predict(matrix)
        best_score = -1.0

    print(f"[KMEANS] Wybrane k={best_k} z najlepszym silhouette_score={best_score:.4f}")

    # --- 2. Grupowanie userów po labelach ---
    clusters: Dict[int, List[int]] = {}
    for idx, label in enumerate(best_labels):
        uid = user_ids[idx]
        clusters.setdefault(label, []).append(uid)

    # --- 3. Rozbijanie / zbieranie tak, aby grupy miały 3–8 osób ---
    groups: List[List[int]] = []
    small_groups: List[List[int]] = []

    for label, members in clusters.items():
        n = len(members)

        if n < 3:
            # za mały klaster – na razie odkładamy, później dołączymy do innych
            small_groups.append(members)
        elif 3 <= n <= 8:
            groups.append(members)
        else:
            # duży klaster – dzielimy na kilka grup po 3–8 osób
            sizes = split_into_chunks_with_range(n, min_size=3, max_size=8)
            start = 0
            for s in sizes:
                chunk = members[start:start + s]
                groups.append(chunk)
                start += s

    # Spłaszczamy wszystkie "za małe" klastery
    flat_small = [uid for g in small_groups for uid in g]

    # --- 4. Próbujemy dopełnić istniejące grupy małymi userami ---
    if flat_small:
        print(f"[KMEANS] Mam {len(flat_small)} userów z małych klastrów (<3).")
        # indeksy grup, które mają jeszcze miejsce (mniej niż 8 osób)
        capacities = [(i, 8 - len(g)) for i, g in enumerate(groups) if len(g) < 8]
        small_idx = 0

        for gi, cap in capacities:
            for _ in range(cap):
                if small_idx >= len(flat_small):
                    break
                groups[gi].append(flat_small[small_idx])
                small_idx += 1
            if small_idx >= len(flat_small):
                break

        # jeśli jeszcze ktoś został, robimy z nich nowe grupy według 3–8
        remaining = flat_small[small_idx:]
        if remaining:
            print(
                f"[KMEANS] Po dopełnieniu istniejących grup zostało "
                f"{len(remaining)} userów – tworzę nowe grupy 3–8."
            )
            sizes = split_into_chunks_with_range(len(remaining), min_size=3, max_size=8)
            start = 0
            for s in sizes:
                chunk = remaining[start:start + s]
                groups.append(chunk)
                start += s

    # --- 5. Walidacja: jeżeli coś nadal nie spełnia 3–8, robimy globalny fallback ---
    bad = [g for g in groups if not (3 <= len(g) <= 8)]
    if bad:
        print("[KMEANS] Wykryto grupy spoza zakresu 3–8 – wykonuję globalny fallback.")
        # globalny podział wszystkich userów na sensowne rozmiary 3–8
        all_users = [uid for group in groups for uid in group]
        groups = []
        sizes = split_into_chunks_with_range(len(all_users), min_size=3, max_size=8)
        start = 0
        for s in sizes:
            chunk = all_users[start:start + s]
            groups.append(chunk)
            start += s

    print(f"[KMEANS] Powstało {len(groups)} grup (każda 3–8 osób).")
    return groups



# ================== BUDOWANIE STRUKTURY WYJŚCIOWEJ (PER-GROUP) ==================


def build_group_export_for_ws(
    groups: List[List[int]],
    users_data: List[dict],
) -> List[dict]:
    """
    Zwraca dokładnie:
    {
      "groupId": int,
      "users": [userId...],
      "topTraits": [3 najbardziej wspólne cechy],
      "latitude": średnia lat,
      "longitude": średnia lon
    }
    """
    user_by_id: Dict[int, dict] = {}
    for rec in users_data:
        uid = rec.get("userId")
        if uid is not None:
            user_by_id[uid] = rec

    group_records: List[dict] = []

    for group_idx, group_user_ids in enumerate(groups, start=1):
        trait_sums: Dict[str, float] = {}
        lats = []
        lons = []

        for uid in group_user_ids:
            rec = user_by_id.get(uid)
            if not rec:
                continue

            traits = extract_traits_from_record(rec)
            for name, val in traits.items():
                trait_sums[name] = trait_sums.get(name, 0.0) + float(val)

            lat = rec.get("latitude")
            lon = rec.get("longitude")
            if lat is not None and lon is not None:
                lats.append(float(lat))
                lons.append(float(lon))

        sorted_traits = sorted(
            trait_sums.items(), key=lambda x: x[1], reverse=True
        )
        top_traits = [name for name, _ in sorted_traits[:3]]

        if lats and lons:
            avg_lat = sum(lats) / len(lats)
            avg_lon = sum(lons) / len(lons)
        else:
            avg_lat = None
            avg_lon = None

        group_records.append(
            {
                "groupId": group_idx,
                "users": group_user_ids,
                "topTraits": top_traits,
                "latitude": avg_lat,
                "longitude": avg_lon,
            }
        )

    print(f"[LOG] Przygotowano {len(group_records)} rekordów group-level.")
    return group_records


def save_groups_to_file(
    group_records: List[dict],
    filename: str = OUTPUT_GROUPS_FILE,
):
    print(f"[IO] Zapisuję {len(group_records)} rekordów do pliku: {filename}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(group_records, f, ensure_ascii=False, indent=2)
    print("✅ Zapisano grupy w formacie groupId + users + topTraits + lat/lon.\n")


# ================== MAIN ==================


def main():
    data = fetch_features_from_backend()
    if not data:
        print("❌ Brak danych – przerywam.")
        return

    if not isinstance(data, list):
        print("❌ Oczekiwana lista obiektów {userId, topTraits, latitude, longitude}.")
        return

    print(f"[FLOW] Liczba rekordów z backendu: {len(data)}")

    trait_index = build_trait_index(data)
    matrix, user_ids = build_feature_matrix(data, trait_index, geo_weight=GEO_WEIGHT)
    groups = compute_kmeans_groups(matrix, user_ids)

    # 1) PER-GROUP: dokładnie taki format, jak opisałeś
    ws_group_records = build_group_export_for_ws(groups, data)

    # 2) zapis do pliku
    save_groups_to_file(ws_group_records, filename=OUTPUT_GROUPS_FILE)

    # 3) wysyłka po WebSocket/STOMP do Javy
    print("[FLOW] Nawiązuję połączenie WS, żeby wysłać grupy...")
    ws_client = GroupsWebSocketClient(WS_URI)
    ws_client.connect()
    time.sleep(1)

    ws_client.send_groups(ws_group_records)

    time.sleep(2)

    print("[PREVIEW] Pierwsze kilka grup:")
    for i, g in enumerate(ws_group_records[:5], start=1):
        print(f"  Grupa {g['groupId']}: users={g['users']}, topTraits={g['topTraits']}")


if __name__ == "__main__":
    main()
