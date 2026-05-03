"""
GIKI-Connect — local app: uses trained K-Means + scaler from output/model/.
Run:  python app_server.py   OR double-click START_APP.bat (Windows)

Picks a free port from 8765 upward and opens your browser automatically.
"""
from __future__ import annotations

import json
import socket
import threading
import time
import webbrowser
from pathlib import Path

import joblib
import numpy as np
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DESIGN = ROOT / "design"
MODEL_DIR = ROOT / "output" / "model"
FIGMA_SVG = DESIGN / "giki-app-figma.svg"

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


@app.after_request
def _cors(resp):
    """So PRESENTATION_OFFLINE.html can call the API from another port or file preview."""
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/presentation")
def presentation():
    """Same UI + story for class; uses live /api/predict when this tab is served by Flask."""
    return send_from_directory(str(ROOT), "PRESENTATION_OFFLINE.html")


@app.get("/figma.svg")
def figma_svg():
    if not FIGMA_SVG.is_file():
        return ("SVG not found", 404)
    return send_from_directory(str(DESIGN), "giki-app-figma.svg", mimetype="image/svg+xml")


@app.get("/design-preview")
def design_preview():
    """Static layout preview for Figma handoff (matches design/giki-app-figma.svg)."""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
        "<title>GIKI-Connect — design preview</title>"
        "<style>body{margin:0;background:#0c1222;color:#8b95b0;font-family:system-ui,sans-serif;"
        "min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:24px;}"
        "a{color:#2dd4bf}img{max-width:100%;height:auto;border-radius:16px;box-shadow:0 12px 48px rgba(0,0,0,.45)}"
        "p{max-width:36rem;text-align:center;font-size:14px;margin-top:16px}</style></head><body>"
        "<p>Import this same graphic into Figma via <strong>File → Import</strong> → "
        "<code>design/giki-app-figma.svg</code></p>"
        "<p><a href='/'>← Back to app</a> · <a href='/figma.svg' download>Download SVG</a></p>"
        "<img src='/figma.svg' width='393' height='1200' alt='GIKI-Connect Figma frame'/>"
        "</body></html>"
    )


@app.route("/api/predict", methods=["POST", "OPTIONS"])
def api_predict():
    if request.method == "OPTIONS":
        return ("", 204)
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


def _pick_port(start: int = 8765, attempts: int = 25) -> int:
    for port in range(start, start + attempts):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
        finally:
            s.close()
    raise SystemExit("No free TCP port found in range — close other apps using 8765–8790.")


def main():
    if not (MODEL_DIR / "kmeans.pkl").exists():
        raise SystemExit(
            f"Missing model files under {MODEL_DIR}. Run GIKI_Connect_Notebook.ipynb first."
        )
    load_artifacts()
    port = _pick_port()
    base = f"http://127.0.0.1:{port}"
    url = f"{base}/"

    def _open_browser():
        time.sleep(1.8)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    print()
    print("=" * 56)
    print("  GIKI-Connect — SERVER IS RUNNING")
    print("=" * 56)
    print(f"  App:            {url}")
    print(f"  For Sir / slides: {base}/presentation")
    print(f"  Design preview:   {base}/design-preview")
    print(f"  Double-click:     PRESENTATION_OFFLINE.html (works offline; live if server is up)")
    print("  Keep this window OPEN while you present. Ctrl+C to stop.")
    print("=" * 56)
    print()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
