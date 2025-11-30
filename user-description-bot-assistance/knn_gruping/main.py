# knn_grouping/main.py
import time

from .backend import fetch_features_from_backend
from .config import GEO_WEIGHT, OUTPUT_GROUPS_FILE, WS_URI
from .features import build_trait_index, build_feature_matrix
from .clustering import compute_kmeans_groups
from .groups_export import build_group_export_for_ws, save_groups_to_file
from .ws_client import GroupsWebSocketClient


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

    ws_group_records = build_group_export_for_ws(groups, data)
    save_groups_to_file(ws_group_records, filename=OUTPUT_GROUPS_FILE)

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
