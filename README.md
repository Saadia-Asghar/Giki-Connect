# GIKI-Connect

Campus app concept: **students** enter hobbies + social sliders → the **same K-Means + scaler** saved from your notebook assigns an **interest tribe**, then the app suggests **admin-posted events** and **anonymized peers** from `output/combined_with_clusters.csv` (same cluster + hobby overlap). **GIKI admin** posts events via the Admin tab (JSON storage in `data/events.json`).

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

**GitHub:** [Saadia-Asghar/Giki-Connect](https://github.com/Saadia-Asghar/Giki-Connect)

## Is the app really using the trained model?

**Yes.** On each “Get tribe & suggestions” request the server:

1. Builds the same feature row as the notebook (`h_*` hobby columns + `SocHours`, `ComfortScore`, `SameProvince_pct`, `SameFaculty_pct`).
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

## Push

```bash
git add -A && git commit -m "message" && git push origin main
```
