# knn_grouping/clustering.py
import math
from typing import Dict, List

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .config import MIN_CLUSTER_RATIO, MAX_CLUSTER_RATIO


def split_into_chunks_with_range(total: int, min_size: int = 3, max_size: int = 8) -> List[int]:
    sizes = []
    remaining = total

    while remaining > 0:
        if min_size <= remaining <= max_size:
            sizes.append(remaining)
            break

        chosen = None
        for k in range(max_size, min_size - 1, -1):
            rest = remaining - k
            if rest == 0 or rest >= min_size:
                chosen = k
                break

        if chosen is None:
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

    if num_users < 3:
        return [user_ids.copy()]

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

    clusters: Dict[int, List[int]] = {}
    for idx, label in enumerate(best_labels):
        uid = user_ids[idx]
        clusters.setdefault(label, []).append(uid)

    groups: List[List[int]] = []
    small_groups: List[List[int]] = []

    for label, members in clusters.items():
        n = len(members)

        if n < 3:
            small_groups.append(members)
        elif 3 <= n <= 8:
            groups.append(members)
        else:
            sizes = split_into_chunks_with_range(n, min_size=3, max_size=8)
            start = 0
            for s in sizes:
                chunk = members[start:start + s]
                groups.append(chunk)
                start += s

    flat_small = [uid for g in small_groups for uid in g]

    if flat_small:
        print(f"[KMEANS] Mam {len(flat_small)} userów z małych klastrów (<3).")
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

    bad = [g for g in groups if not (3 <= len(g) <= 8)]
    if bad:
        print("[KMEANS] Wykryto grupy spoza zakresu 3–8 – wykonuję globalny fallback.")
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
