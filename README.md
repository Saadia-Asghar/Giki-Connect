# GIKI-Connect

Interest-tribe app backed by your notebook’s **K-Means** model (`output/model/*.pkl`). Survey + analysis: `GIKI_Connect_Data.xlsx`, `GIKI_Connect_Notebook.ipynb`.

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

**GitHub:** [Saadia-Asghar/Giki-Connect](https://github.com/Saadia-Asghar/Giki-Connect)

## Run the app (replaces the old static “showcase” page)

```powershell
cd d:\hp2\Downloads\giki_project
pip install -r requirements.txt
python app_server.py
```

Open **http://127.0.0.1:8765/** — pick hobbies and sliders, then **Find my tribe**. The server calls the same scaler + K-Means as the notebook.

Or double-run **`serve.ps1`** (installs hint only; it opens the browser after a short delay).

**Cursor:** `Terminal → Run Task… → Serve GIKI app (Flask)` (if defined in `.vscode/tasks.json`).

If you see a model error, run the notebook once so `output/model/kmeans.pkl` (and friends) exist.

## Jupyter (train / refresh model)

```bash
pip install jupyter pandas numpy scikit-learn matplotlib scipy joblib openpyxl
jupyter notebook
```

Run `GIKI_Connect_Notebook.ipynb` top to bottom, then restart `app_server.py`.

## Figma wireframe (optional)

Import `design/giki-connect-frames.svg` into Figma (**File → Import**) if you still want layout frames; the live product UI is `web/`.

## Push

```bash
git add -A && git commit -m "message" && git push origin main
```
