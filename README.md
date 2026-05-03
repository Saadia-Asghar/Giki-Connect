# GIKI-Connect

Analyzing social siloing and the “society bridge” at GIKI — survey data, notebook analysis, and a static showcase UI.

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

**Repository:** [github.com/Saadia-Asghar/Giki-Connect](https://github.com/Saadia-Asghar/Giki-Connect)

## Repo layout

- `index.html` — single project showcase page (open via local server for images)
- `GIKI_Connect_Notebook.ipynb` — full pipeline (cleaning, stats, K-means, figures)
- `GIKI_Connect_Data.xlsx` — survey export
- `output/` — generated CSVs, plots, and `output/model/` pickles after you run the notebook
- `design/giki-connect-frames.svg` — wireframe for **Figma** (File → Import)
- `serve.ps1` — starts Python server, then opens the browser (avoids connection refused)

## Local preview (fixes ERR_CONNECTION_REFUSED)

Nothing listens on port **8765** until you start a server. **Either:**

1. **Terminal** in the project folder: `python -m http.server 8765` — wait until you see `Serving HTTP on...`, **then** open [http://localhost:8765/](http://localhost:8765/)

2. **PowerShell:** `powershell -ExecutionPolicy Bypass -File .\serve.ps1` — opens the browser automatically after a short delay.

3. **Cursor:** `Terminal → Run Task… → Serve site (localhost:8765)`, then open [http://localhost:8765/](http://localhost:8765/) in Simple Browser or Chrome.

If images are missing, run the notebook to create `output/eda_dashboard.png` and `output/cluster_chart.png`.

## Figma (no MCP)

This workspace does **not** include a Figma MCP server. To use the layout in Figma:

1. Open [Figma](https://www.figma.com/) in the browser or desktop app.
2. **File → Import** (or drag onto the canvas).
3. Choose `design/giki-connect-frames.svg`.

You can also paste a screenshot of `index.html` into Figma as a reference layer.

## Jupyter

```bash
pip install jupyter pandas numpy scikit-learn matplotlib scipy joblib openpyxl
jupyter notebook
```

Open `GIKI_Connect_Notebook.ipynb` and run all cells top to bottom.

## Push updates

```bash
git add -A
git commit -m "Your message"
git push origin main
```
