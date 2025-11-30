# traits.py
import json
import re
from textwrap import dedent
from typing import List, Optional, Dict

import numpy as np
import requests
from pydantic import BaseModel

from config import client, JAVA_BASE_URL


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
    4) Wysyła PUT na /api/users/{userId}/description
    """
    print("\n================= [FLOW] ZAPIS OPISU DO BACKENDU =================")
    print(f"[FLOW] user_id={user_id}")
    print(f"[FLOW] finalDescription:\n{final_description}\n")

    try:
        raw_features = extract_features_from_description(final_description)
        print(f"[LOG] raw_features (przed normalizacją): {raw_features}")

        features = normalize_profile_features(raw_features)
        print(f"[LOG] features (po normalizacji): {features}")

        tag_index = build_tag_index([features])
        vec = profile_to_vector_with_sparse_flag(features, tag_index, final_description)
        traits = vector_to_readable_dict(vec, tag_index)

        payload = {
            "text": final_description,
            "traits": traits,
        }

        url = f"{JAVA_BASE_URL}/api/users/{user_id}/description"
        print(f"[HTTP] PUT {url}")
        print(f"[HTTP] Payload JSON: {json.dumps(payload, ensure_ascii=False)}")

        resp = requests.put(url, json=payload)
        print(f"[HTTP] Odpowiedź backendu: {resp.status_code}")
        print(f"[HTTP] Body odpowiedzi: {resp.text}")
        print("================= [FLOW] ZAPIS OPISU ZAKOŃCZONY =================\n")

    except Exception as e:
        print(f"❌ [HTTP] Błąd wysyłania opisu do backendu: {e}")
