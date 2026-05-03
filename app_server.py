"""
GIKI-Connect — local app: uses trained K-Means + scaler from output/model/.
Run from project root:  python app_server.py
Then open http://127.0.0.1:8765/
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
MODEL_DIR = ROOT / "output" / "model"

HOBBIES = [
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


def hobby_col(h: str) -> str:
    return f"h_{h.replace(' ', '_').replace('/', '').replace(',', '')}"


def load_artifacts():
    global km_model, scaler, feature_cols, cluster_profiles
    km_model = joblib.load(MODEL_DIR / "kmeans.pkl")
    scaler = joblib.load(MODEL_DIR / "scaler.pkl")
    feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
    with open(MODEL_DIR / "cluster_profiles.json", encoding="utf-8") as f:
        cluster_profiles = json.load(f)


def predict_row(hobbies: list[str], soc_hours: float, comfort: float, same_prov_pct: float, same_fac_pct: float):
    sel = set(hobbies)
    row = {}
    for h in HOBBIES:
        key = hobby_col(h)
        row[key] = 1 if h in sel else 0
    row["SocHours"] = float(soc_hours)
    row["ComfortScore"] = float(comfort)
    row["SameProvince_pct"] = float(same_prov_pct)
    row["SameFaculty_pct"] = float(same_fac_pct)

    X_new = np.array([[row[c] for c in feature_cols]])
    X_sc = scaler.transform(X_new)
    cluster = int(km_model.predict(X_sc)[0])
    silo = round((same_prov_pct + same_fac_pct) / 200, 3)
    if silo < 0.25:
        silo_lbl = "Low (diverse)"
    elif silo < 0.5:
        silo_lbl = "Moderate"
    else:
        silo_lbl = "High (siloed)"

    prof = cluster_profiles[str(cluster)]
    rec = (
        "Try a society or hobby mixer to meet people outside your usual circle."
        if silo > 0.5
        else "Your profile fits this interest tribe — great anchor for mixers and collaborations."
    )
    return {
        "cluster": cluster,
        "tribe_name": prof["name"],
        "tribe_size": prof["n"],
        "tribe_avg_silo": prof["avg_silo"],
        "top_hobbies": prof["top_hobbies"],
        "silo_index": silo,
        "silo_label": silo_lbl,
        "recommendation": rec,
    }


app = Flask(__name__, static_folder=str(WEB), static_url_path="/assets")


@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.post("/api/predict")
def api_predict():
    data = request.get_json(force=True, silent=True) or {}
    hobbies = data.get("hobbies") or []
    if not isinstance(hobbies, list):
        return jsonify({"error": "hobbies must be a list"}), 400
    hobbies = [str(h) for h in hobbies if str(h) in HOBBIES]
    try:
        soc = float(data.get("soc_hours", 0))
        comfort = float(data.get("comfort", 4))
        sp = float(data.get("same_prov_pct", 50))
        sf = float(data.get("same_fac_pct", 50))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid numeric fields"}), 400

    soc = max(0.0, min(soc, 20.0))
    comfort = max(1.0, min(comfort, 5.0))
    sp = max(0.0, min(sp, 100.0))
    sf = max(0.0, min(sf, 100.0))

    if not hobbies:
        return jsonify({"error": "Pick at least one hobby."}), 400

    out = predict_row(hobbies, soc, comfort, sp, sf)
    return jsonify(out)


def main():
    if not (MODEL_DIR / "kmeans.pkl").exists():
        raise SystemExit(
            f"Missing model files under {MODEL_DIR}. Run GIKI_Connect_Notebook.ipynb first."
        )
    load_artifacts()
    print("GIKI-Connect app — http://127.0.0.1:8765/")
    app.run(host="127.0.0.1", port=8765, debug=False)


if __name__ == "__main__":
    main()
