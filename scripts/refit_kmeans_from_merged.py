"""
Rebuild K-Means + scaler + feature_cols from output/merged_dataset.csv
(use after changing feature definitions in the notebook, without re-running Excel steps).

Requires: output/merged_dataset.csv (from notebook Step 5 save).
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
MERGED = ROOT / "output" / "merged_dataset.csv"
MODEL_DIR = ROOT / "output" / "model"

HOBBIES_ALL = [
    "Music",
    "Art",
    "Cooking",
    "Fitness",
    "Football",
    "Hiking",
    "Coding / Programming",
    "Reading",
    "Debating",
    "Gaming",
    "Cricket",
    "Photography",
    "Travelling",
    "Skating",
]


def main() -> None:
    combined = pd.read_csv(MERGED)
    # Strip any stray h_* columns if an older script version wrote them here
    combined = combined[[c for c in combined.columns if not str(c).startswith("h_")]]
    # Report silo: (# same-prov OR same-fac) / T ≈ p + f − p×f with p,f from % (see notebook)
    _p = combined["SameProvince_pct"].fillna(12.5) / 100.0
    _f = combined["SameFaculty_pct"].fillna(12.5) / 100.0
    combined["Silo_Index"] = _p + _f - _p * _f
    combined.to_csv(MERGED, index=False)

    tr = combined.copy()
    for h in HOBBIES_ALL:
        col = f"h_{h.replace(' ', '_').replace('/', '').replace(',', '')}"
        tr[col] = tr["Hobbies"].fillna("").apply(lambda x: 1 if h in str(x) else 0)

    hobby_cols = [c for c in tr.columns if c.startswith("h_")]
    feature_cols = hobby_cols + ["SocHours", "ComfortScore", "Silo_Index"]
    X = tr[feature_cols].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    K = 8
    km_model = KMeans(n_clusters=K, random_state=42, n_init=20)
    km_model.fit(X_scaled)
    tr["Cluster"] = km_model.labels_

    cluster_profiles: dict = {}
    for c in range(K):
        grp = tr[tr["Cluster"] == c]
        top_h = grp[hobby_cols].sum().sort_values(ascending=False).head(3).index.tolist()
        top_h = [h.replace("h_", "").replace("_", " ") for h in top_h]
        avg_s = grp["Silo_Index"].mean()
        cluster_profiles[str(c)] = {
            "name": " & ".join(top_h[:2]),
            "n": int(len(grp)),
            "avg_silo": round(float(avg_s), 3),
            "top_hobbies": top_h,
        }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(km_model, MODEL_DIR / "kmeans.pkl")
    joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
    joblib.dump(feature_cols, MODEL_DIR / "feature_cols.pkl")
    with open(MODEL_DIR / "cluster_profiles.json", "w", encoding="utf-8") as f:
        json.dump(cluster_profiles, f, indent=2)
    tr.to_csv(ROOT / "output" / "combined_with_clusters.csv", index=False)
    print("Wrote:", MODEL_DIR / "kmeans.pkl", MODEL_DIR / "scaler.pkl", MODEL_DIR / "feature_cols.pkl")
    print("Wrote:", MODEL_DIR / "cluster_profiles.json", ROOT / "output" / "combined_with_clusters.csv")
    print("feature_cols tail:", feature_cols[-4:])


if __name__ == "__main__":
    main()
