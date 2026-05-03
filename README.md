# GIKI-Connect

Analyzing social siloing and the “society bridge” at GIKI — survey data, notebook analysis, and a static showcase UI.

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

## Repo layout

- `GIKI_Connect_Notebook.ipynb` — full pipeline (cleaning, stats, K-means, figures)
- `GIKI_Connect_Data.xlsx` — survey export (add locally if not in repo; do not commit sensitive rows if policy requires)
- `showcase/index.html` — project proposal / demo page
- `output/` — generated CSVs, plots, and `output/model/` pickles after you run the notebook

## Local preview (showcase page)

The showcase loads images from `output/`. **Start the HTTP server from this repo root** (not from inside `showcase/` only), then open the URL below.

**Option A — PowerShell helper**

```powershell
cd path\to\giki_project
powershell -ExecutionPolicy Bypass -File .\serve.ps1
```

**Option B — manual**

```powershell
cd path\to\giki_project
python -m http.server 8765
```

Browser: [http://localhost:8765/showcase/index.html](http://localhost:8765/showcase/index.html)  
or [http://localhost:8765/](http://localhost:8765/) (redirects to the showcase).

If images 404, run the notebook first to create `output/eda_dashboard.png` and `output/cluster_chart.png`.

## Jupyter

```bash
pip install jupyter pandas numpy scikit-learn matplotlib scipy joblib openpyxl
jupyter notebook
```

Open `GIKI_Connect_Notebook.ipynb` and run all cells top to bottom.

## GitHub

Remote: `https://github.com/Saadia-Asghar/Giki-Connect.git`

```bash
git init
git add .
git commit -m "Add GIKI-Connect notebook, showcase, and outputs"
git branch -M main
git remote add origin https://github.com/Saadia-Asghar/Giki-Connect.git
git push -u origin main
```

Use GitHub Desktop, or a [personal access token](https://github.com/settings/tokens) when Git asks for a password over HTTPS.
