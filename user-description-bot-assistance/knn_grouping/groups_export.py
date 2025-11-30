# knn_grouping/groups_export.py
import json
from typing import Dict, List

from .features import extract_traits_from_record
from .config import OUTPUT_GROUPS_FILE


def build_group_export_for_ws(
    groups: List[List[int]],
    users_data: List[dict],
) -> List[dict]:
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
