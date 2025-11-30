# knn_grouping/backend.py
import json
from typing import Any, List, Optional

import requests

from .config import JAVA_BASE_URL, FEATURES_PATH


def fetch_features_from_backend() -> Optional[List[dict]]:
    url = f"{JAVA_BASE_URL}{FEATURES_PATH}"
    print(f"[HTTP] GET {url}")

    try:
        resp = requests.get(url)
        print(f"[HTTP] Status: {resp.status_code}")

        try:
            data: Any = resp.json()
        except ValueError:
            print("❌ [HTTP] Odpowiedź nie jest poprawnym JSON-em:")
            print(resp.text)
            return None

        print("[LOG] Przykładowe dane (pierwsze 1–2 rekordy):")
        if isinstance(data, list):
            print(json.dumps(data[:2], ensure_ascii=False, indent=2))
            return data
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return None

    except requests.RequestException as e:
        print(f"❌ [HTTP] Błąd podczas wywołania endpointu: {e}")
        return None
