"""
GIKI-Connect — course project app (social siloing + society bridge + interest-led ties).

Flask serves the UI and APIs; joblib pickles in output/model/ match the notebook pipeline.
Suggests admin-posted events and anonymized peer ideas from output/combined_with_clusters.csv.

Run: python app_server.py  or  START_APP.bat
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import socket
import threading
import time
import uuid
import webbrowser
from pathlib import Path

import joblib
import numpy as np
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
ASSETS = PUBLIC / "assets"
MODEL_DIR = ROOT / "output" / "model"
COHORT_CSV = ROOT / "output" / "combined_with_clusters.csv"
EVENTS_SEED = ROOT / "data" / "events.json"


def events_json_path() -> Path:
    """Vercel serverless filesystem is read-only except /tmp — store mutable events there."""
    if os.environ.get("VERCEL", ""):
        p = Path("/tmp") / "giki-connect" / "events.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    return EVENTS_SEED

# Change in production; for local demo only.
ADMIN_TOKEN = os.environ.get("GIKI_ADMIN_TOKEN", "giki-admin-demo")

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

_cohort: list[dict] = []

# Shown in /api/tribes — helps admins map events to K-Means clusters (ids 0–3).
TRIBE_ADMIN_GUIDE = {
    "0": "Strong on skating, music, cooking vibes — rink outings, open-mic, potluck-style mixers.",
    "1": "Debating, art, fitness — talks, gallery walks, gym challenges across faculties.",
    "2": "Gaming, music, travel — LAN cafés, rhythm-game corners, trip-planning meetups.",
    "3": "Cooking, music, hiking — food collabs, trail days, low-key acoustic hikes.",
}

# Student-facing copy aligned with the course proposal (siloing, society bridge, interest-led ties).
CAMPUS_CONTEXT = {
    "why_title": "What this is about",
    "why": [
        "GIKI is a residential campus, but many students still sit in small circles tied to faculty, province, or batch.",
        "Societies and hobby spaces are the usual “bridge” out of those bubbles—shared interests before shared demographics.",
        "This screen nudges you toward mixers and people who overlap what you like, so connections can be a bit more intentional.",
    ],
    "limits_title": "Keep in mind",
    "limits": [
        "Suggestions are a campus pilot, not a directory—names are anonymized and you should always use good judgment.",
        "One profile does not define you; treat tribes as a light hint, not a label.",
        "Events are posted by admins in the demo—check society boards and official notices for real logistics.",
    ],
    "next_title": "Worth trying next",
    "next": [
        "Go to one cross-faculty mixer or society intro night with a wing-mate from another department.",
        "Pick an event below and commit to saying hello to two people you do not already sit with in class.",
        "If you are in a society, invite someone who is not—especially international or junior-year students who often feel on the edge of cliques.",
    ],
}


def hobby_col(h: str) -> str:
    return f"h_{h.replace(' ', '_').replace('/', '').replace(',', '')}"


def silo_index_from_report(friends: float, same_prov_pct: float, same_fac_pct: float) -> float:
    """Report definition: (# close friends same province OR same faculty) / (total close friends).

    Survey stores marginal % only. Estimated union count (independence for overlap):
    n_or = T * (p + f - p*f) with p,f in [0,1]. Silo_Index = n_or / T = p + f - p*f.
    If T <= 0, return the union fraction only.
    """
    p = max(0.0, min(1.0, float(same_prov_pct) / 100.0))
    fp = max(0.0, min(1.0, float(same_fac_pct) / 100.0))
    t = float(friends)
    union_frac = p + fp - p * fp
    if t <= 0:
        return round(max(0.0, min(1.0, union_frac)), 3)
    n_or = t * union_frac
    return round(max(0.0, min(1.0, n_or / t)), 3)


def load_artifacts():
    global km_model, scaler, feature_cols, cluster_profiles
    km_model = joblib.load(MODEL_DIR / "kmeans.pkl")
    scaler = joblib.load(MODEL_DIR / "scaler.pkl")
    feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
    with open(MODEL_DIR / "cluster_profiles.json", encoding="utf-8") as f:
        cluster_profiles = json.load(f)


def load_cohort():
    global _cohort
    _cohort = []
    if not COHORT_CSV.is_file():
        return
    with open(COHORT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["_cluster"] = int(float(row.get("Cluster", -1)))
            except (TypeError, ValueError):
                continue
            _cohort.append(row)


def load_events_file() -> dict:
    path = events_json_path()
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        if EVENTS_SEED.is_file() and path.resolve() != EVENTS_SEED.resolve():
            shutil.copy2(EVENTS_SEED, path)
        elif not path.is_file():
            path.write_text('{"events":[]}', encoding="utf-8")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_events_file(data: dict) -> None:
    path = events_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def suggest_peers(cluster: int, hobbies: list[str], limit: int = 6) -> list[dict]:
    if not _cohort:
        return []
    want = set(hobbies)
    scored: list[tuple[int, dict]] = []
    for row in _cohort:
        if row.get("_cluster") != cluster:
            continue
        raw_h = row.get("Hobbies") or ""
        theirs = {x.strip() for x in raw_h.replace(";", ",").split(",") if x.strip()}
        overlap = len(want & theirs)
        reg = str(row.get("Reg", "")).strip()
        if reg.upper().startswith("ANON"):
            display = reg
        else:
            display = f"Student …{reg[-4:]}" if len(reg) >= 4 else "Student"
        scored.append(
            (
                overlap,
                {
                    "display": display,
                    "faculty": row.get("Faculty", ""),
                    "province": row.get("Province", ""),
                    "hobbies_preview": ", ".join(sorted(theirs)[:6]),
                    "shared_hobbies": sorted(want & theirs),
                    "overlap": overlap,
                },
            )
        )
    scored.sort(key=lambda x: (-x[0], x[1]["display"]))
    return [p for _, p in scored[:limit]]


def suggest_events(cluster: int, hobbies: list[str]) -> list[dict]:
    data = load_events_file()
    events = data.get("events") or []
    hs = set(hobbies)
    scored: list[tuple[float, dict]] = []
    for e in events:
        tags = set(e.get("hobby_tags") or [])
        clusters = e.get("clusters") or []
        overlap = len(hs & tags)
        c_bonus = 2.0 if cluster in clusters else (0.5 if not clusters else 0.0)
        score = overlap * 3 + c_bonus
        scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    picked = [dict(e) for s, e in scored if s > 0][:8]
    if not picked:
        picked = [dict(e) for s, e in scored[:5]]
    return picked


def tribes_payload() -> dict:
    """Single payload for UI: tribe atlas + campus narrative (cluster_profiles loaded)."""
    tribes = []
    for key in sorted(cluster_profiles.keys(), key=lambda x: int(x)):
        p = cluster_profiles[key]
        tribes.append(
            {
                "id": int(key),
                "name": p["name"],
                "n": p["n"],
                "avg_silo": p["avg_silo"],
                "top_hobbies": p["top_hobbies"],
                "admin_guide": TRIBE_ADMIN_GUIDE.get(
                    str(key),
                    "Match event hobbies to this tribe’s top interests.",
                ),
            }
        )
    return {
        "tribes": tribes,
        "kmeans_note": "Four interest tribes (IDs 0–3). Tick them when posting so the right students see your event first; optional if hobby tags already match.",
        **CAMPUS_CONTEXT,
    }


def predict_row(
    hobbies: list[str],
    soc_hours: float,
    comfort: float,
    same_prov_pct: float,
    same_fac_pct: float,
    friends: float = 4.0,
):
    sel = set(hobbies)
    row = {}
    for h in HOBBIES:
        key = hobby_col(h)
        row[key] = 1 if h in sel else 0
    row["SocHours"] = float(soc_hours)
    row["ComfortScore"] = float(comfort)
    silo = silo_index_from_report(friends, same_prov_pct, same_fac_pct)
    row["Silo_Index"] = silo

    X_new = np.array([[row[c] for c in feature_cols]])
    X_sc = scaler.transform(X_new)
    cluster = int(km_model.predict(X_sc)[0])
    if silo < 0.25:
        silo_lbl = "Low (diverse)"
    elif silo < 0.5:
        silo_lbl = "Moderate"
    else:
        silo_lbl = "High (siloed)"

    prof = cluster_profiles[str(cluster)]
    if silo > 0.5:
        rec = (
            "Your close friendships look quite concentrated—pick one society taster session or "
            "cross-faculty mixer this week and aim to add one contact outside your usual batch."
        )
    elif soc_hours < 1.0:
        rec = (
            "Low society hours this week—if you can, try one society desk or open event; "
            "they are often the easiest bridge between faculties on a residential campus."
        )
    else:
        rec = (
            "Strong overlap with this interest circle—use the events list to host or co-host a small "
            "hobby hangout and invite someone from another province or program."
        )
    peers = suggest_peers(cluster, hobbies)
    events = suggest_events(cluster, hobbies)
    return {
        "cluster": cluster,
        "tribe_name": prof["name"],
        "tribe_size": prof["n"],
        "tribe_avg_silo": prof["avg_silo"],
        "top_hobbies": prof["top_hobbies"],
        "silo_index": silo,
        "silo_label": silo_lbl,
        "recommendation": rec,
        "suggested_peers": peers,
        "suggested_events": events,
        "model_note": "",
    }


app = Flask(
    __name__,
    static_folder=str(ASSETS),
    static_url_path="/assets",
)


@app.get("/")
def index():
    return send_from_directory(str(PUBLIC), "index.html")


@app.get("/api/tribes")
def api_tribes():
    """Tribe definitions + campus narrative for student insight and admin event targeting."""
    return jsonify(tribes_payload())


@app.get("/api/events")
def api_events_list():
    return jsonify(load_events_file())


@app.route("/api/events", methods=["POST", "OPTIONS"])
def api_events_create():
    if request.method == "OPTIONS":
        return ("", 204)
    if request.headers.get("X-Admin-Token", "") != ADMIN_TOKEN:
        return jsonify({"error": "Admin token required (header X-Admin-Token)."}), 403
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    when_iso = (data.get("when_iso") or "").strip()
    place = (data.get("place") or "").strip()
    description = (data.get("description") or "").strip()
    hobby_tags = [str(x) for x in (data.get("hobby_tags") or []) if str(x) in HOBBIES]
    clusters_raw = data.get("clusters") or []
    clusters: list[int] = []
    for c in clusters_raw:
        try:
            clusters.append(int(c))
        except (TypeError, ValueError):
            continue
    if not title or not when_iso:
        return jsonify({"error": "title and when_iso are required."}), 400
    store = load_events_file()
    ev = {
        "id": str(uuid.uuid4())[:12],
        "title": title,
        "when_iso": when_iso,
        "place": place,
        "description": description,
        "hobby_tags": hobby_tags,
        "clusters": clusters,
    }
    store.setdefault("events", []).insert(0, ev)
    save_events_file(store)
    return jsonify({"ok": True, "event": ev})


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
        friends = float(data.get("friends", 4))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid numeric fields"}), 400

    soc = max(0.0, min(soc, 20.0))
    comfort = max(1.0, min(comfort, 5.0))
    sp = max(0.0, min(sp, 100.0))
    sf = max(0.0, min(sf, 100.0))
    friends = max(0.5, min(friends, 20.0))

    if not hobbies:
        return jsonify({"error": "Pick at least one hobby."}), 400

    out = predict_row(hobbies, soc, comfort, sp, sf, friends)
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
    load_cohort()
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
    print(f"  App:     {url}")
    print(f"  Admin:   post events with header X-Admin-Token: {ADMIN_TOKEN}")
    print("  (Set GIKI_ADMIN_TOKEN env var to change the demo token.)")
    print("  Keep this window open. Ctrl+C to stop.")
    print("=" * 56)
    print()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def _bootstrap_model():
    """Load pickles when the module is imported (needed for Vercel — no main() run)."""
    if (MODEL_DIR / "kmeans.pkl").is_file():
        load_artifacts()
        load_cohort()


_bootstrap_model()


if __name__ == "__main__":
    main()
