# GIKI-Connect

Campus app concept: **students** enter hobbies + social sliders → the **same K-Means + scaler** saved from your notebook assigns an **interest tribe**, then the app suggests **admin-posted events** and **anonymized peers** from `output/combined_with_clusters.csv` (same cluster + hobby overlap). **GIKI admin** posts events via the Admin tab (JSON storage in `data/events.json`).

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

**GitHub:** [Saadia-Asghar/Giki-Connect](https://github.com/Saadia-Asghar/Giki-Connect)

## Is the app really using the trained model?

**Yes.** On each “Get tribe & suggestions” request the server:

1. Builds the same feature row as the notebook (`h_*` hobby columns + `SocHours`, `ComfortScore`, **`Silo_Index`** = (same-province % + same-faculty %) ÷ 200).
2. Runs `scaler.transform(...)` then `kmeans.predict(...)` on **`output/model/scaler.pkl`** and **`output/model/kmeans.pkl`** (joblib).

Event and peer suggestions are **on top of** that prediction (rules + CSV), not a replacement for the model.

## Run locally

```powershell
cd d:\hp2\Downloads\giki_project
pip install -r requirements.txt
python app_server.py
```

Or double-click **`START_APP.bat`**. Leave the console open while you use the app.

## Admin events

1. Open the app → **GIKI admin** tab — read **“What tribes are”** (four K-Means clusters, ids **0–3**, names from `cluster_profiles.json`).  
2. Default token: **`giki-admin-demo`** (override with env **`GIKI_ADMIN_TOKEN`**).  
3. Post title, time, place, description, **hobby tags**, and optionally **target tribes** so the right students see the event first.  
4. Events live in **`data/events.json`**. API: `GET /api/tribes` returns tribe atlas + campus “why / limits / roadmap” copy for the UI.

## Jupyter (retrain / refresh pickles)

```bash
pip install jupyter pandas numpy scikit-learn matplotlib scipy joblib openpyxl
jupyter notebook
```

Run `GIKI_Connect_Notebook.ipynb` top to bottom, then restart `app_server.py`.

If you only changed how **K-Means features** are defined but already have `output/merged_dataset.csv`, you can refresh pickles + `combined_with_clusters.csv` with:

`python scripts/refit_kmeans_from_merged.py`

## Deploy on Vercel

1. Import repo **Saadia-Asghar/Giki-Connect**, branch **main**.  
2. **Framework Preset:** choose **Flask** (or “Other” if Flask is not listed).  
3. **Root Directory:** `./`  
4. **Environment variables (optional):** `GIKI_ADMIN_TOKEN` = your secret (otherwise default demo token is used).

Production routing follows [Vercel’s Flask 3 example](https://github.com/vercel/examples/tree/main/python/flask3): **`vercel.json`** rewrites every path to **`/api/index`**, and **`api/index.py`** exposes the Flask instance **`app`** (`from app_server import app`). Root **`app.py`** is kept as a thin re-export for tools that look for it; the live deployment uses **`api/index.py`**.

Static UI lives under **`public/`** (`index.html` + `assets/`), per [Vercel’s Flask static guidance](https://vercel.com/docs/frameworks/backend/flask). The API stays on the same domain (`/api/...`).

**Note:** Admin-posted events on Vercel are written under **`/tmp`** (ephemeral per serverless instance). For a real campus rollout, use a database or Vercel KV / Postgres. Cold starts load **scikit-learn** + pickles — first request can take several seconds.

## Push

```bash
git add -A && git commit -m "message" && git push origin main
```
