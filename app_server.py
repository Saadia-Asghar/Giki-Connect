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

# Populated from cohort CSV for demo form (faculty / year pickers).
_FORM_FACULTIES: list[str] = []
_FORM_YEARS: list[str] = []

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
        "Treat the suggestions like a curated bulletin—pick what fits your week; they are hints, not a verdict on your social life.",
    ],
    "limits_title": "Keep in mind",
    "limits": [
        "Suggestions are a campus pilot, not a directory—names are anonymized and you should always use good judgment.",
        "One profile does not define you; treat tribes as a light hint, not a label.",
        "Events are posted by admins in the demo—check society boards and official notices for real logistics.",
    ],
    "next_title": "Worth trying next",
    "next": [
        "Pick one event below and aim to greet two people you do not already hang out with.",
        "If you are not in a society yet, try one intro or taster session this month—it is the fastest on-campus bridge between faculties.",
        "If you already are in a society, bring one friend who is not; international and junior-year students often benefit most from that invite.",
    ],
}


def hobby_col(h: str) -> str:
    return f"h_{h.replace(' ', '_').replace('/', '').replace(',', '')}"


# Short activity-format hints keyed to survey hobby labels (used in /api/predict copy only).
HOBBY_MICRO_TIPS = {
    "Music": "Try turn-taking formats (listening round, low-stakes open mic) so conversation is not only small talk.",
    "Art": "Sketch-walks or timed collage blocks give people something to point at while they chat.",
    "Cooking": "Potluck prep or one shared recipe keeps hands busy and lowers pressure to perform socially.",
    "Fitness": "Pair warm-ups or short relay formats avoid one person leading the whole hour.",
    "Football": "Small-sided games or skills drills create natural rotation between faces.",
    "Hiking": "Pick a route with a clear halfway landmark so pairs can split and regroup comfortably.",
    "Coding / Programming": "Pairing, mini demos, or bug hunts carry half the conversation in the work itself.",
    "Reading": "Themed chapters or 20-minute silent blocks plus one debrief line keep introverts in the loop.",
    "Debating": "Rotating prep roles and timed floor splits quieter voices in fairly.",
    "Gaming": "Co-op rounds or board-game corners let people join without monopolising the mic.",
    "Cricket": "Net sessions or fielding drills mix skill levels without awkward lulls.",
    "Photography": "Photo walks with a shared prompt card beat unstructured mingling for first contact.",
    "Travelling": "Itinerary snippets or budget hacks are easy icebreakers before deeper travel talk.",
    "Skating": "Beginner lanes or buddy checks make repeat contact natural across weeks.",
}


def _first_society_token(societies: str) -> str:
    s = (societies or "").strip()
    if not s:
        return ""
    return s.split(",")[0].strip()[:72]


def _hobby_sig(label: str) -> str:
    """Loose key so 'Coding / Programming' matches notebook 'Coding  Programming'."""
    return "".join(c.lower() for c in str(label) if c.isalnum())


def _hobbies_overlap_tribe(user_hobbies: list[str], top_hobbies: list[str]) -> list[str]:
    tops = [_hobby_sig(t) for t in top_hobbies]
    out: list[str] = []
    for h in user_hobbies:
        hs = _hobby_sig(h)
        if not hs:
            continue
        for i, ts in enumerate(tops):
            if hs == ts or (len(hs) >= 8 and (hs in ts or ts in hs)):
                out.append(h)
                break
    return list(dict.fromkeys(out))


def build_insight_sections(
    cluster: int,
    prof: dict,
    silo: float,
    silo_lbl: str,
    comfort: float,
    soc_hours: float,
    hobbies: list[str],
    societies: str,
) -> list[dict]:
    """Rule-based narrative from model inputs + cluster profile (honest: not a second ML model)."""
    top = [str(h) for h in prof.get("top_hobbies") or []]
    cohort_silo = float(prof.get("avg_silo") or 0.5)
    delta = silo - cohort_silo
    key_bullets: list[str] = []

    if comfort < 3:
        key_bullets.append(
            "Your comfort score is on the lower side for talking across provinces—seed trust with "
            "low-commitment invites (one lab task, a short walk) before suggesting bigger collaborative projects."
        )
    elif comfort <= 4.25:
        key_bullets.append(
            "You sit in a balanced comfort band—alternate familiar hangouts with one new context per month."
        )
    else:
        key_bullets.append(
            "Higher comfort with cross-group chat—open formats can work; themed prompts or short rotations "
            "still help quieter peers join without one voice dominating."
        )

    if silo >= 0.55:
        key_bullets.append(
            "Your estimated friendship concentration is on the higher side—layer light prompts or parallel "
            "activities into technical or hobby hangouts so quieter people have a clear hook."
        )
    elif silo < 0.35:
        key_bullets.append(
            "Your estimate skews toward more diverse close ties—great footing for co-hosting mixed-faculty hangs; "
            "still give newcomers a concrete first task so they know how to enter the conversation."
        )

    key_bullets = key_bullets[:4]

    hobby_bullets: list[str] = []
    overlap_h = _hobbies_overlap_tribe(hobbies, top)
    if overlap_h:
        hobby_bullets.append(
            "You overlap this tribe’s top survey hobbies on "
            + ", ".join(overlap_h[:3])
            + "—use those topics as the shared spine when you reach out."
        )
    for h in hobbies[:3]:
        tip = HOBBY_MICRO_TIPS.get(h)
        if tip:
            hobby_bullets.append(f"{h}: {tip}")
    if not hobby_bullets:
        hobby_bullets.append(
            "Pick formats with a visible shared task so the activity carries part of the conversation for everyone."
        )
    hobby_bullets = hobby_bullets[:4]

    soc_first = _first_society_token(societies)
    society_bullets: list[str] = []
    if soc_first:
        society_bullets.append(
            f"You selected societies including “{soc_first}” on the form (not fed into K-Means today)—"
            "peer-led or committee-led sessions there usually beat one-way lectures for meeting same-interest people."
        )
    elif soc_hours >= 1.5:
        society_bullets.append(
            f"Society hours in your form are healthy ({soc_hours:.1f} h/wk)—consider dedicating one recurring slot "
            "to invite someone from another faculty into an activity you already run."
        )
    else:
        society_bullets.append(
            "Societies act like a filter: members self-select topics they care about, so shared interests surface "
            "faster than in a random tutorial group."
        )
    society_bullets.extend(
        [
            "Search or ask once about your strongest hobby inside a society channel or desk—shared activity beats cold small talk for a first real conversation.",
            "Newcomers: say what you want in one line (study partner for X, casual football)—specificity gets replies; “anyone free?” rarely does.",
            "Repeat beats perfect: showing up to the same society meet two weeks in a row beats one mega-event you never follow up.",
        ]
    )

    cohort_bullets = [
        f"This tribe ({prof.get('name', '')}) averages {cohort_silo:.3f} friendship concentration in the training sample; "
        f"your estimate is {silo:.3f} ({silo_lbl}).",
    ]
    if delta > 0.08:
        cohort_bullets.append(
            "Your estimate sits above this tribe’s cohort average—structured hangs with a clear activity may feel easier than large unstructured rooms."
        )
    elif delta < -0.08:
        cohort_bullets.append(
            "Your estimate sits below this tribe’s cohort average—strong footing for hosting small hobby-led hangs that widen others’ circles."
        )
    else:
        cohort_bullets.append(
            "You are close to this tribe’s average—blend familiar faces with one new context when you plan the week."
        )

    event_shapes = [
        "Quiet café blocks with optional show-and-tell at the end",
        "Short co-design jams blending visual and systems thinking",
        "Maker tables with parallel stations (art, board games, light prototyping)",
        "Reading or game nights with themed corners people drift between",
        "Outdoor segments paired with a lightweight shared task",
    ]
    i0 = cluster % len(event_shapes)
    picked_shapes = [event_shapes[(i0 + j) % len(event_shapes)] for j in range(3)]

    sections: list[dict] = [
        {
            "id": "key_pointers",
            "title": "Key pointers",
            "bullets": key_bullets,
            "footnote": "Derived from your sliders, comfort score, and this cluster’s cohort averages in the training CSV—not a clinical assessment.",
        },
        {
            "id": "hobby_formats",
            "title": "Your hobbies → formats that fit",
            "bullets": hobby_bullets,
        },
        {
            "id": "societies_newcomers",
            "title": "Societies & newcomers",
            "bullets": society_bullets,
        },
        {
            "id": "cohort_compare",
            "title": "You vs this tribe’s training sample",
            "bullets": cohort_bullets,
        },
        {
            "id": "event_shapes",
            "title": "Event shapes that tend to fit",
            "subtitle": "Based on your tribe and inputs—not tied to a specific venue on campus.",
            "bullets": picked_shapes,
        },
    ]
    return sections


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


def _unique_csv_column(path: Path, column: str) -> list[str]:
    if not path.is_file():
        return []
    seen: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = (row.get(column) or "").strip()
            if v:
                seen.add(v)
    return sorted(seen)


def load_cohort():
    global _cohort, _FORM_FACULTIES, _FORM_YEARS
    _cohort = []
    _FORM_FACULTIES = []
    _FORM_YEARS = []
    if not COHORT_CSV.is_file():
        return
    with open(COHORT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["_cluster"] = int(float(row.get("Cluster", -1)))
            except (TypeError, ValueError):
                continue
            _cohort.append(row)
    _FORM_FACULTIES = _unique_csv_column(COHORT_CSV, "Faculty")
    _FORM_YEARS = _unique_csv_column(COHORT_CSV, "Year")


def training_meta() -> dict:
    """Live numbers for demo banner — matches saved model & cohort."""
    total_n = sum(int(p["n"]) for p in cluster_profiles.values())
    pca_pct: float | None = None
    pca_path = MODEL_DIR / "pca.pkl"
    if pca_path.is_file():
        pca = joblib.load(pca_path)
        pca_pct = round(float(sum(pca.explained_variance_ratio_)) * 100, 2)
    return {
        "k_clusters": len(cluster_profiles),
        "total_profiles": total_n,
        "n_features": len(feature_cols),
        "pca_variance_pct": pca_pct,
    }


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
        soc_cell = str(row.get("Societies") or "").strip()
        society_cue = soc_cell.split(",")[0].strip()[:56] if soc_cell else ""
        scored.append(
            (
                overlap,
                {
                    "display": display,
                    "faculty": row.get("Faculty", ""),
                    "province": row.get("Province", ""),
                    "year": (row.get("Year") or "").strip(),
                    "hobbies_preview": ", ".join(sorted(theirs)[:6]),
                    "shared_hobbies": sorted(want & theirs),
                    "overlap": overlap,
                    "society_cue": society_cue,
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
        "kmeans_note": "",
        **CAMPUS_CONTEXT,
    }


def predict_row(
    hobbies: list[str],
    soc_hours: float,
    comfort: float,
    same_prov_pct: float,
    same_fac_pct: float,
    friends: float = 4.0,
    societies: str = "",
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
    insight_sections = build_insight_sections(
        cluster,
        prof,
        silo,
        silo_lbl,
        comfort,
        soc_hours,
        hobbies,
        societies,
    )
    k_all = len(cluster_profiles)
    assignment_explain = {
        "title": "How your tribe was chosen",
        "lines": [
            (
                f"You are in cluster ID {cluster} (out of {k_all}). The friendly name \"{prof['name']}\" and the "
                f"{prof['n']} students in sample line come from output/model/cluster_profiles.json — the same export the notebook uses to label tribes."
            ),
            (
                "Assignment rule: your form builds one row with the 17 training features (hobby flags, society hours, "
                "comfort, silo index). That row is scaled with output/model/scaler.pkl and passed to output/model/kmeans.pkl; "
                "predict returns exactly one integer: the tribe ID you see above."
            ),
            (
                "Faculty, year, and society chips are stored under submitted in the API response for your write-up, "
                "but they are not multiplied into those 17 numbers unless you change the notebook, retrain, and export new pickles."
            ),
        ],
    }
    return {
        "cluster": cluster,
        "tribe_name": prof["name"],
        "tribe_size": prof["n"],
        "tribe_avg_silo": prof["avg_silo"],
        "top_hobbies": prof["top_hobbies"],
        "silo_index": silo,
        "silo_label": silo_lbl,
        "comfort_used": comfort,
        "soc_hours_used": soc_hours,
        "recommendation": rec,
        "suggested_peers": peers,
        "suggested_events": events,
        "insight_sections": insight_sections,
        "assignment_explain": assignment_explain,
        "result_footer": (
            "Narrative blocks combine your submitted sliders, the K-Means cluster label, "
            "and cohort fields from combined_with_clusters.csv—simple rules, not a second model."
        ),
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


@app.get("/api/meta")
def api_meta():
    """Demo stats + form dropdown options (faculty / year from cohort CSV)."""
    return jsonify(
        {
            **training_meta(),
            "faculties": _FORM_FACULTIES,
            "years": _FORM_YEARS,
        }
    )


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

    soc_member_raw = data.get("soc_member", True)
    if isinstance(soc_member_raw, str):
        soc_member = soc_member_raw.strip().lower() in ("yes", "true", "1", "y", "member")
    else:
        soc_member = bool(soc_member_raw)
    if not soc_member:
        soc = 0.0

    soc = max(0.0, min(soc, 20.0))
    comfort = max(1.0, min(comfort, 5.0))
    sp = max(0.0, min(sp, 100.0))
    sf = max(0.0, min(sf, 100.0))
    friends = max(0.5, min(friends, 20.0))

    if not hobbies:
        return jsonify({"error": "Pick at least one hobby."}), 400

    societies_in = str(data.get("societies") or "").strip()[:500]
    out = predict_row(hobbies, soc, comfort, sp, sf, friends, societies_in)
    out["submitted"] = {
        "faculty": str(data.get("faculty") or "").strip()[:120],
        "year": str(data.get("year") or "").strip()[:80],
        "soc_member": soc_member,
        "societies": societies_in,
    }
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
