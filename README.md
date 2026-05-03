# GIKI-Connect

Interest-tribe **web app** using your notebook’s K-Means (`output/model/*.pkl`). Data: `GIKI_Connect_Data.xlsx`, pipeline: `GIKI_Connect_Notebook.ipynb`.

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

**GitHub:** [Saadia-Asghar/Giki-Connect](https://github.com/Saadia-Asghar/Giki-Connect)

The old static **proposal showcase** (`index.html` + `showcase/`) has been removed in favor of this app.

## Local preview

```powershell
cd d:\hp2\Downloads\giki_project
pip install -r requirements.txt
python app_server.py
```

| URL | What |
|-----|------|
| http://127.0.0.1:8765/ | **App** — hobbies, sliders, Find my tribe |
| http://127.0.0.1:8765/design-preview | **Design preview** — same layout as the Figma SVG |
| http://127.0.0.1:8765/figma.svg | Raw SVG (download or import into Figma) |

Or run **`serve.ps1`** (opens the app after a short delay).

**Cursor:** `Terminal → Run Task… → Serve GIKI app (Flask)`.

If the app fails to start, run the notebook once so `output/model/kmeans.pkl` exists.

## Figma (import — no MCP)

Cursor does not ship a Figma MCP here. To get the design **into Figma**:

1. In Figma: **File → Import** (or drag the file onto the canvas).
2. Choose **`design/giki-app-figma.svg`** — mobile frame, layer names, and **tokens** match `web/styles.css`.
3. Optional notes: **`design/FIGMA.txt`**

## Jupyter

```bash
pip install jupyter pandas numpy scikit-learn matplotlib scipy joblib openpyxl
jupyter notebook
```

Run `GIKI_Connect_Notebook.ipynb` top to bottom, then restart `app_server.py`.

## Push

```bash
git add -A && git commit -m "message" && git push origin main
```
