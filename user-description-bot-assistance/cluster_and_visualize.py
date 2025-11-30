import json
from typing import List, Dict

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches  # <-- nowy import


# ===== HELPERY DO TAGÓW =====

def build_tag_index(dicts: List[Dict[str, float]]) -> Dict[str, int]:
    """
    Zbiera wszystkie tagi ze wszystkich rekordów
    i buduje słownik: tag -> index (pozycja w wektorze).
    """
    all_tags = set()
    for d in dicts:
        all_tags.update(d.keys())

    tag_index = {tag: i for i, tag in enumerate(sorted(all_tags))}
    return tag_index


def dict_to_vector(d: Dict[str, float], tag_index: Dict[str, int]) -> np.ndarray:
    """
    Zamienia pojedynczy słownik {tag: waga} na wektor numpy.
    Jeśli w słowniku nie ma jakiegoś tagu, w tym miejscu będzie 0.0.
    """
    v = np.zeros(len(tag_index), dtype=float)
    for tag, val in d.items():
        if tag in tag_index:
            idx = tag_index[tag]
            v[idx] = float(val)
    return v


def vector_to_readable_dict(v: np.ndarray, tag_index: Dict[str, int]) -> Dict[str, float]:
    """
    Zamienia wektor numpy na słownik {tag: wartość} tylko dla niezerowych wartości.
    Zaokrągla wartości do 2 miejsc po przecinku.
    """
    idx_to_tag = {idx: tag for tag, idx in tag_index.items()}
    result = {}
    for idx, val in enumerate(v):
        if val > 0:
            tag = idx_to_tag[idx]
            result[tag] = round(float(val), 2)
    return result


# ===== WYBÓR LICZBY KLASTRÓW =====

def choose_best_k(X: np.ndarray, k_min: int = 2, k_max: int = 10) -> int:
    """
    Wybiera najlepszą liczbę klastrów na podstawie silhouette score.
    """
    n_samples = X.shape[0]

    max_k_allowed = min(k_max, n_samples - 1)
    if max_k_allowed < k_min:
        print("Za mało próbek na automatyczny wybór k, ustawiam k=1.")
        return 1

    best_k = k_min
    best_score = -1.0

    print("=== Szukanie najlepszego k (silhouette score) ===")
    for k in range(k_min, max_k_allowed + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=100)
        labels = kmeans.fit_predict(X)

        if len(set(labels)) < 2:
            print(f"k={k}: tylko jeden klaster, pomijam silhouette.")
            continue

        score = silhouette_score(X, labels)
        print(f"k={k}: silhouette_score = {score:.4f}")

        if score > best_score:
            best_score = score
            best_k = k

    print(f"\nWybrane k = {best_k} (najwyższy silhouette_score = {best_score:.4f})\n")
    return best_k


# ===== ODCZYT PLIKU, K-MEANS I WIZUALIZACJA =====

if __name__ == "__main__":
    input_path = "profiles_vectors_augmented.txt"
    print(f"=== K-means na profilach z pliku {input_path} ===\n")

    # 1. Wczytanie wszystkich linii JSON -> list[dict[tag->float]]
    records: List[Dict[str, float]] = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            if isinstance(obj, dict) and "features" in obj and isinstance(obj["features"], dict):
                records.append(obj["features"])
            elif isinstance(obj, dict):
                records.append(obj)
            else:
                raise ValueError(f"Nieoczekiwany format linii: {obj}")

    print(f"Wczytano {len(records)} profili.\n")

    # 2. Budowa słownika tagów
    tag_index = build_tag_index(records)

    print("=== Słownik tagów (tag_index) ===")
    for tag, idx in sorted(tag_index.items(), key=lambda x: x[1]):
        print(f"{idx:2d} -> {tag}")
    print()

    # 3. Macierz X: każdy użytkownik -> wektor
    X = np.vstack([dict_to_vector(d, tag_index) for d in records])

    print("=== Macierz X (pierwsze wiersze) ===")
    print(X[:5])
    print()

    # 4. Automatyczny wybór liczby klastrów
    best_k = choose_best_k(X, k_min=10, k_max=30)

    # 5. K-means z wybranym k
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=100)
    kmeans.fit(X)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    # 6. Opis klastrów: skład + top tagi (bez lat/lon) + nazwa klastra
    print("\n=== Klastry (k-means) ===")

    idx_to_tag = {idx: tag for tag, idx in tag_index.items()}
    ignore_tags_for_name = {"lat", "lon"}
    cluster_names: Dict[int, str] = {}

    for cluster_id in range(best_k):
        print(f"\n--- Klaster {cluster_id} ---")
        indices = [i for i, lab in enumerate(labels) if lab == cluster_id]
        print("Użytkownicy w tym klastrze:", [i + 1 for i in indices])

        center_vec = centers[cluster_id]

        # znajdź cechę o największej wartości, pomijając lat/lon
        best_feat_idx = None
        best_feat_val = -1.0
        for idx, val in enumerate(center_vec):
            tag = idx_to_tag[idx]
            if tag in ignore_tags_for_name:
                continue
            if val > best_feat_val:
                best_feat_val = val
                best_feat_idx = idx

        if best_feat_idx is not None:
            main_feature_name = idx_to_tag[best_feat_idx]
        else:
            main_feature_name = f"Cluster_{cluster_id}"

        cluster_names[cluster_id] = main_feature_name
        print(f"Nazwa klastra (największa cecha): {main_feature_name}")

        # Top 5 cech (też pomijając lat/lon)
        sorted_indices = np.argsort(center_vec)[::-1]
        top_idx = [
            i for i in sorted_indices
            if idx_to_tag[i] not in ignore_tags_for_name
        ][:5]

        top_tags = [
            (idx_to_tag[i], round(float(center_vec[i]), 2))
            for i in top_idx if center_vec[i] > 0
        ]

        print("Top tagi klastra:")
        for tag, val in top_tags:
            print(f"  - {tag}: {val}")

    # 7. Wizualizacja na mapie: lon (x) vs lat (y)
    idx_lat = tag_index.get("lat")
    idx_lon = tag_index.get("lon")

    if idx_lat is None or idx_lon is None:
        print("Brak 'lat' lub 'lon' w cechach – nie mogę zrobić wykresu współrzędnych.")
    else:
        lats = X[:, idx_lat]
        lons = X[:, idx_lon]

        plt.figure(figsize=(8, 6))
        cmap = plt.get_cmap("tab10")
        scatter = plt.scatter(lons, lats, c=labels, cmap=cmap, s=80)

        # Podpisy z numerami użytkowników (1..N)
        for i, (x, y) in enumerate(zip(lons, lats)):
            plt.text(x + 0.0003, y + 0.0003, str(i + 1), fontsize=8)

        # Podpisy klastrów nazwą (w miejscu średniej pozycji punktów klastra)
        for cluster_id in range(best_k):
            indices = [i for i, lab in enumerate(labels) if lab == cluster_id]
            if not indices:
                continue
            mean_lon = float(np.mean(lons[indices]))
            mean_lat = float(np.mean(lats[indices]))
            name = cluster_names.get(cluster_id, str(cluster_id))
            plt.text(
                mean_lon,
                mean_lat,
                name,
                fontsize=10,
                fontweight="bold",
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
            )

        # LEGENDARZ: kolor -> nazwa klastra
        legend_handles = []
        for cluster_id in range(best_k):
            color = cmap(cluster_id % cmap.N)
            label = f"{cluster_id}: {cluster_names.get(cluster_id, '')}"
            patch = mpatches.Patch(color=color, label=label)
            legend_handles.append(patch)

        plt.legend(
            handles=legend_handles,
            title="Klastry (id: nazwa)",
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
            borderaxespad=0.0,
        )

        plt.title(f"K-means – użytkownicy w przestrzeni geograficznej (k={best_k})")
        plt.xlabel("lon")
        plt.ylabel("lat")
        plt.colorbar(scatter, label="Klaster (id)")
        plt.tight_layout()
        plt.show()

    print("\n=== Koniec analizy ===")
