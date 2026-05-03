# GIKI-Connect

Web app that loads your **trained K-Means** from `output/model/*.pkl` and maps a student’s hobbies + social sliders to an **interest tribe** — for presenting how the model can be used on campus (mixers, societies).

**Authors:** Fatima Tabasum (2024178), Saadia Asghar (2024550) · Theory of Data Science · Instructor: Sir Shahab Ansari

**GitHub:** [Saadia-Asghar/Giki-Connect](https://github.com/Saadia-Asghar/Giki-Connect)

---

## Show Sir during class (fixes “connection refused”)

`ERR_CONNECTION_REFUSED` means **no server was running** in the background. The app is not a file you double-click alone — you start Python once, then use the browser.

### Easiest (Windows)

1. **Double-click `START_APP.bat`** in this folder.  
2. Wait until a **black window** says `SERVER IS RUNNING` and your **browser opens by itself**.  
3. **Leave that black window open** the whole time you present. Closing it stops the app.

If the browser does not open, read the URL printed in the black window (port may be **8766** if **8765** is busy) and paste it into Chrome/Edge.

### Manual

```powershell
cd d:\hp2\Downloads\giki_project
pip install -r requirements.txt
python app_server.py
```

Wait for `SERVER IS RUNNING`, then open the printed link (usually **http://127.0.0.1:8765/**).

### URLs when the server is running

| Link | Use |
|------|-----|
| **/** | Main app — “Find my tribe” with **real** K-Means |
| **/presentation** | Same idea + short banner for explaining the project to Sir |
| **/design-preview** | Figma-style layout preview |

You can also double-click **`PRESENTATION_OFFLINE.html`** from the folder: it tries the live API on common ports; if the server is off, it still shows the **UI and tribe names** (offline demo) so you are never stuck with a blank error page.

---

## Before the first run

Run **`GIKI_Connect_Notebook.ipynb`** once (all cells) so `output/model/kmeans.pkl` exists.

---

## Jupyter

```bash
pip install jupyter pandas numpy scikit-learn matplotlib scipy joblib openpyxl
jupyter notebook
```

---

## Figma

Import **`design/giki-app-figma.svg`** in Figma (**File → Import**). There is no built-in Figma MCP in this repo.

---

## Push

```bash
git add -A && git commit -m "message" && git push origin main
```
