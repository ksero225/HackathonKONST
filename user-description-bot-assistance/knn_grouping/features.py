# knn_grouping/features.py
from typing import Dict, List, Tuple

import numpy as np

from .config import GEO_WEIGHT


def extract_traits_from_record(rec: dict) -> Dict[str, float]:
    traits = rec.get("traits")
    if isinstance(traits, dict) and traits:
        return {str(k): float(v) for k, v in traits.items()}

    top_traits = rec.get("topTraits")
    if isinstance(top_traits, dict) and top_traits:
        return {str(k): float(v) for k, v in top_traits.items()}

    if isinstance(top_traits, list) and top_traits:
        return {str(name): 1.0 for name in top_traits}

    return {}


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
