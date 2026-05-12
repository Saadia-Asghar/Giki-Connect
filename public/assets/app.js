const HOBBIES = [
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
];

/**
 * Optional society chips — saved with the form; they do not change the tribe number in this demo.
 */
const SOCIETIES = [
  "ACM (GIK chapter)",
  "AIAA (GIK)",
  "AIChE (GIK)",
  "ASHRAE (GIK)",
  "ASME (GIK)",
  "ASM/TMS (GIK)",
  "CDES (dramatics & entertainment)",
  "Character Building Society",
  "GIK Sports Society",
  "GIK WebTeam",
  "GMS — Mathematics Society",
  "Google Developer Groups on Campus (GDGoC)",
  "Graduate Students Society",
  "IEEE (GIK chapter)",
  "IET (GIK chapter)",
  "Literary and Debating Society",
  "Media Club",
  "Microsoft Club GIK",
  "Naqsh Arts Society",
  "Netronix",
  "Project Topi",
  "Science Society",
  "SOPHEP",
  "SPIE (GIK chapter)",
  "Women Engineers Society",
];

const TRIBE_ACCENT = ["#7c1d3a", "#9c2748", "#a8556f", "#b45309"];

const ATLAS_INTRO_DEFAULT =
  'Each card is one <strong>interest tribe</strong> (numbered <strong>0–3</strong>). After you run the form, <strong>your tribe card is outlined in rose</strong> so you always know which one is yours.';

/** @type {null | Record<string, unknown>} */
let tribesData = null;

/** @type {null | Record<string, unknown>} */
let metaData = null;

function el(id) {
  return document.getElementById(id);
}

/**
 * When the HTML is not served by Flask (Live Preview, opening the file, another port),
 * API calls must target the Flask origin. Set once via ?api=http://127.0.0.1:8765 (no trailing slash);
 * stored in localStorage. Optional: data-api-base on the html element, or meta name="giki-api-base".
 */
function getApiBase() {
  try {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("api");
    if (q) {
      const normalized = String(q).trim().replace(/\/$/, "");
      if (normalized) {
        try {
          localStorage.setItem("gikiApiBase", normalized);
          const u = new URL(window.location.href);
          u.searchParams.delete("api");
          const tail = `${u.pathname}${u.search}${u.hash}`;
          window.history.replaceState({}, "", tail || "/");
        } catch (_) {
          /* ignore */
        }
        return normalized;
      }
    }
  } catch (_) {
    /* ignore */
  }
  try {
    const ls = localStorage.getItem("gikiApiBase");
    if (ls) return String(ls).trim().replace(/\/$/, "");
  } catch (_) {
    /* ignore */
  }
  const ds = document.documentElement?.dataset?.apiBase;
  if (ds) return String(ds).trim().replace(/\/$/, "");
  const meta = document.querySelector('meta[name="giki-api-base"]');
  if (meta?.content) return String(meta.content).trim().replace(/\/$/, "");
  return "";
}

function apiUrl(path) {
  const base = getApiBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  if (!base) return p;
  return `${base}${p}`;
}

/** Parse JSON body; Flask sometimes returned HTML on 500, which made r.json() throw. */
async function readResponseJson(r) {
  const text = await r.text();
  if (!text.trim()) {
    return { ok: true, data: {} };
  }
  try {
    return { ok: true, data: JSON.parse(text) };
  } catch {
    return {
      ok: false,
      data: {},
      parseError: true,
      snippet: text.slice(0, 160).replace(/\s+/g, " "),
    };
  }
}

function setResultsJumpAvailable(on) {
  const a = el("jump-to-results");
  if (!a) return;
  a.classList.toggle("is-disabled", !on);
  a.setAttribute("aria-disabled", on ? "false" : "true");
  if (on) {
    a.removeAttribute("tabindex");
    a.removeAttribute("title");
  } else {
    a.setAttribute("tabindex", "-1");
    a.setAttribute("title", "Find your tribe first — then use this link to jump to your results.");
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function tribeById(id) {
  if (!tribesData?.tribes) return null;
  return tribesData.tribes.find((t) => t.id === id) || null;
}

function tribeLabel(id) {
  const t = tribeById(id);
  return t ? `Tribe ID ${id} — ${t.name}` : `Tribe ID ${id}`;
}

function slugId(s) {
  const raw = String(s)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return (raw || "item").slice(0, 36);
}

/** @param {{ idPrefix?: string }} [options] */
function buildChipGrid(containerId, items, options = {}) {
  const grid = el(containerId);
  if (!grid) return;
  const idPrefix = options.idPrefix || containerId;
  grid.innerHTML = "";
  items.forEach((name, idx) => {
    const lab = document.createElement("label");
    const inp = document.createElement("input");
    inp.type = "checkbox";
    inp.value = name;
    const sid = `${idPrefix}-${slugId(name)}-${idx}`;
    inp.id = sid;
    lab.setAttribute("for", sid);
    const sp = document.createElement("span");
    sp.textContent = name;
    lab.appendChild(inp);
    lab.appendChild(sp);
    grid.appendChild(lab);
  });
}

function buildHobbyGrid(containerId) {
  buildChipGrid(containerId, HOBBIES, {
    idPrefix: containerId.replace(/-/g, "_"),
  });
}

function readSelectedSocieties() {
  if (!readSocMember()) return "";
  return Array.from(document.querySelectorAll("#society-grid input:checked"))
    .map((i) => i.value)
    .join(", ");
}

function buildClusterPicks() {
  const box = el("cluster-picks");
  if (!box) return;
  box.innerHTML = "";
  for (let c = 0; c < 4; c++) {
    const lab = document.createElement("label");
    const inp = document.createElement("input");
    inp.type = "checkbox";
    inp.value = String(c);
    const sp = document.createElement("span");
    sp.textContent = tribeLabel(c);
    lab.appendChild(inp);
    lab.appendChild(sp);
    box.appendChild(lab);
  }
}

function renderStudentInsight() {
  const root = el("student-insight-body");
  if (!tribesData) {
    root.innerHTML =
      "<p class=\"hint\">Could not load context. Is the server running?</p>";
    return;
  }
  const ul = (items) =>
    `<ul class="insight-list">${items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>`;
  root.innerHTML = `
    <h3 class="insight-h3">${escapeHtml(tribesData.why_title || "")}</h3>
    ${ul(tribesData.why || [])}
    <h3 class="insight-h3">${escapeHtml(tribesData.limits_title || "")}</h3>
    ${ul(tribesData.limits || [])}
    <h3 class="insight-h3">${escapeHtml(tribesData.next_title || "")}</h3>
    ${ul(tribesData.next || [])}
  `;
}

function renderTribeGrid(containerId) {
  const grid = el(containerId);
  if (!tribesData || !grid) return;
  grid.innerHTML = "";
  (tribesData.tribes || []).forEach((t) => {
    const card = document.createElement("article");
    card.className = "tribe-mini-card";
    card.dataset.tribeId = String(t.id);
    card.style.borderLeftColor = TRIBE_ACCENT[t.id % 4] || TRIBE_ACCENT[0];
    const tops = (t.top_hobbies || []).join(", ");
    card.setAttribute("role", "group");
    card.setAttribute(
      "aria-label",
      `Tribe ID ${t.id}, ${escapeHtml(t.name)}, ${t.n} students in training sample`,
    );
    card.innerHTML = `
      <div class="tribe-mini-id">Tribe ID ${t.id}</div>
      <h4 class="tribe-mini-name">${escapeHtml(t.name)}</h4>
      <p class="tribe-mini-stats">${t.n} people in survey sample · avg friendship concentration ${t.avg_silo}</p>
      <p class="tribe-mini-tops">Top hobbies: <strong>${escapeHtml(tops)}</strong></p>
      <p class="tribe-mini-guide">${escapeHtml(t.admin_guide || "")}</p>
    `;
    grid.appendChild(card);
  });
}

function renderAdminTribeAtlas() {
  renderTribeGrid("admin-tribe-cards");
}

function renderPublicTribeShowcase() {
  renderTribeGrid("public-tribe-cards");
}

function readSliders() {
  return {
    soc_hours: parseFloat(el("soc_hours").value),
    comfort: parseFloat(el("comfort").value),
    friends: parseFloat(el("friends").value),
    same_prov_pct: parseFloat(el("same_prov_pct").value),
    same_fac_pct: parseFloat(el("same_fac_pct").value),
  };
}

function syncSliderLabels() {
  const s = readSliders();
  el("soc_hours_v").textContent = `${s.soc_hours} h/wk`;
  el("comfort_v").textContent = String(s.comfort);
  el("friends_v").textContent = String(s.friends);
  el("same_prov_pct_v").textContent = `${Math.round(s.same_prov_pct)}%`;
  el("same_fac_pct_v").textContent = `${Math.round(s.same_fac_pct)}%`;

  const sh = el("soc_hours");
  if (sh) sh.setAttribute("aria-valuetext", `${s.soc_hours} hours per week`);
  const cm = el("comfort");
  if (cm) cm.setAttribute("aria-valuetext", `${s.comfort} of 5`);
  const fr = el("friends");
  if (fr) fr.setAttribute("aria-valuetext", `${s.friends} close friends`);
  const sp = el("same_prov_pct");
  if (sp) sp.setAttribute("aria-valuetext", `${Math.round(s.same_prov_pct)} percent`);
  const sf = el("same_fac_pct");
  if (sf) sf.setAttribute("aria-valuetext", `${Math.round(s.same_fac_pct)} percent`);
}

function fmtWhen(iso) {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatTribeTargets(clusterIds) {
  if (!clusterIds || !clusterIds.length) return "";
  const parts = clusterIds.map((c) => tribeLabel(+c));
  return ` · Targets: ${parts.join("; ")}`;
}

/** @param {{ showTargets?: boolean }} [opts] */
function renderEvents(targetEl, events, opts = {}) {
  const showTargets = opts.showTargets !== false;
  const root = el(targetEl);
  root.innerHTML = "";
  if (!events || !events.length) {
    root.innerHTML =
      '<p class="hint" style="margin:0">No events yet — post one in the Admin tab.</p>';
    return;
  }
  events.forEach((e) => {
    const div = document.createElement("div");
    div.className = "event-card";
    const tags = (e.hobby_tags || []).join(", ");
    const cl = showTargets ? formatTribeTargets(e.clusters || []) : "";
    div.innerHTML = `<h4>${escapeHtml(e.title || "")}</h4><div class="meta">${escapeHtml(fmtWhen(e.when_iso))} · ${escapeHtml(e.place || "TBA")}${escapeHtml(cl)}</div><p>${escapeHtml(e.description || "")}</p><div class="meta">Hobby tags: ${escapeHtml(tags || "—")}</div>`;
    root.appendChild(div);
  });
}

function renderPeerList(peers) {
  const root = el("peer-list");
  root.innerHTML = "";
  if (!peers || !peers.length) {
    root.innerHTML =
      '<p class="hint" style="margin:0">No matches in the demo list—try another hobby or check back after new mixers are posted.</p>';
    return;
  }
  peers.forEach((p) => {
    const div = document.createElement("article");
    div.className = "peer-card";
    const shared = (p.shared_hobbies || []).join(", ") || "—";
    const topH = (p.shared_hobbies || [])[0] || "shared interests";
    const tag =
      shared !== "—"
        ? `Often joins ${escapeHtml(topH)} circles; overlaps with you on ${escapeHtml(shared)}.`
        : "Same tribe in the survey list—use society or hobby channels for a soft hello.";
    const yr = p.year ? ` · ${escapeHtml(String(p.year))}` : "";
    const soc =
      p.society_cue &&
      `<div class="peer-cue"><span class="peer-cue-label">Society cue (from sample)</span> ${escapeHtml(p.society_cue)}</div>`;
    div.innerHTML = `
      <div class="peer-card-head">
        <span class="peer-name">${escapeHtml(p.display)}</span>
        <span class="peer-meta">${escapeHtml(p.faculty || "")}${yr}</span>
      </div>
      <p class="peer-tagline">${tag}</p>
      ${soc || ""}
      <div class="peer-interests"><span class="peer-interests-label">Interests</span> ${escapeHtml(p.hobbies_preview || "—")}</div>
      <div class="peer-ice"><span class="peer-ice-label">Icebreaker</span> Offer a 20-minute concrete plan (walk, lab session, one game) instead of a vague “hang sometime”.</div>
    `;
    root.appendChild(div);
  });
}

function renderInsightSections(sections) {
  const root = el("insight-sections");
  if (!root) return;
  if (!sections || !sections.length) {
    root.innerHTML = "";
    return;
  }
  root.innerHTML = sections
    .map((sec) => {
      const sid = escapeHtml(String(sec.id || ""));
      const bullets = (sec.bullets || [])
        .map((b) => `<li>${escapeHtml(b)}</li>`)
        .join("");
      const sub = sec.subtitle
        ? `<p class="insight-block-sub">${escapeHtml(sec.subtitle)}</p>`
        : "";
      const foot = sec.footnote
        ? `<p class="insight-foot">${escapeHtml(sec.footnote)}</p>`
        : "";
      return `<section class="insight-block" data-insight="${sid}">
        <h3 class="insight-block-title">${escapeHtml(sec.title || "")}</h3>
        ${sub}
        <ul class="insight-bullets">${bullets}</ul>
        ${foot}
      </section>`;
    })
    .join("");
}

function highlightPublicTribeCard(clusterId) {
  document.querySelectorAll("#public-tribe-cards .tribe-mini-card").forEach((card) => {
    const isYours =
      clusterId != null &&
      clusterId !== "" &&
      Number(card.dataset.tribeId) === Number(clusterId);
    card.classList.toggle("tribe-mini-card--yours", isYours);
    card.classList.remove("tribe-mini-card--pulse");
    if (isYours) {
      // Re-trigger animation if user runs again.
      void card.offsetWidth;
      card.classList.add("tribe-mini-card--pulse");
      window.setTimeout(() => {
        card.classList.remove("tribe-mini-card--pulse");
      }, 3200);
    }
  });
}

function setAtlasIntro(html) {
  const intro = el("tribe-atlas-intro");
  if (intro) intro.innerHTML = html;
}

function renderAssignmentExplain(ex) {
  const body = el("assignment-explain-body");
  if (!body) return;
  if (!ex || !ex.lines || !ex.lines.length) {
    body.innerHTML = "";
    return;
  }
  const title = ex.title ? `<p class="assignment-lead">${escapeHtml(ex.title)}</p>` : "";
  const lis = ex.lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("");
  body.innerHTML = `${title}<ul class="assignment-list">${lis}</ul>`;
}

function renderResultStatChips(data) {
  const root = el("result-stat-chips");
  if (!root) return;
  const ch = data.comfort_used != null ? String(data.comfort_used) : "—";
  const sh = data.soc_hours_used != null ? String(data.soc_hours_used) : "—";
  root.innerHTML = `
    <li><span class="stat-chip-k">People in tribe</span><span class="stat-chip-v">${escapeHtml(String(data.tribe_size))}</span></li>
    <li><span class="stat-chip-k">Tribe avg. focus</span><span class="stat-chip-v">${escapeHtml(String(data.tribe_avg_silo))}</span></li>
    <li><span class="stat-chip-k">Your focus</span><span class="stat-chip-v">${escapeHtml(String(data.silo_index))}</span></li>
    <li><span class="stat-chip-k">Comfort</span><span class="stat-chip-v">${escapeHtml(ch)}</span></li>
    <li><span class="stat-chip-k">Soc. h/wk</span><span class="stat-chip-v">${escapeHtml(sh)}</span></li>
  `;
}

async function predict() {
  const err = el("error");
  err.textContent = "";
  const hobbies = Array.from(
    document.querySelectorAll("#hobby-grid input:checked"),
  ).map((i) => i.value);
  const body = {
    hobbies,
    ...readSliders(),
    soc_member: readSocMember(),
    faculty: el("faculty")?.value || "",
    year: el("year")?.value || "",
    societies: readSelectedSocieties(),
  };
  const btn = el("submit");
  btn.disabled = true;
  try {
    const r = await fetch(apiUrl("/api/predict"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const parsed = await readResponseJson(r);
    if (!parsed.ok) {
      err.textContent = r.ok
        ? `Unexpected response (not JSON). ${parsed.snippet || ""}`
        : `Server error ${r.status} (non-JSON body — often an old Flask process). Stop the server (Ctrl+C), run python app_server.py again, hard-refresh the page (Ctrl+F5). ${parsed.snippet || ""}`;
      el("result").classList.add("hidden");
      const provErr = el("result-provenance");
      if (provErr) provErr.textContent = "";
      setResultsJumpAvailable(false);
      setAtlasIntro(ATLAS_INTRO_DEFAULT);
      return;
    }
    const data = parsed.data;
    if (!r.ok) {
      err.textContent = data.error || `Request failed (${r.status})`;
      el("result").classList.add("hidden");
      const provErr = el("result-provenance");
      if (provErr) provErr.textContent = "";
      setResultsJumpAvailable(false);
      setAtlasIntro(ATLAS_INTRO_DEFAULT);
      return;
    }
    const k = tribesData?.tribes?.length ?? 4;
    const pill = el("tribe-id-pill");
    if (pill) {
      pill.textContent = `Tribe ID ${data.cluster}`;
      pill.setAttribute(
        "aria-label",
        `Your interest tribe number is ${data.cluster}. There are ${k} tribes, numbered 0 through ${k - 1}.`,
      );
    }
    el("tribe-title").textContent = data.tribe_name;
    el("result-kicker").textContent = "Your match";
    el("result-tagline").textContent = `Tribe ${data.cluster} of ${k}. Next: top hobbies in this tribe, then events and people picked for you.`;
    const prov = el("result-provenance");
    if (prov) {
      prov.textContent =
        "Tribe names and group sizes come from the same saved survey analysis as the course write-up.";
    }
    renderResultStatChips(data);
    el("silo-fill").style.width = `${Math.min(100, Number(data.silo_index) * 100)}%`;
    el("silo-label").textContent = `${data.silo_index} — ${data.silo_label}`;
    const pills = el("tribe-hobbies");
    pills.innerHTML = "";
    (data.top_hobbies || []).forEach((h) => {
      const sp = document.createElement("span");
      sp.textContent = h;
      pills.appendChild(sp);
    });
    el("rec").textContent = data.recommendation;
    renderInsightSections(data.insight_sections || []);
    renderAssignmentExplain(data.assignment_explain);
    const foot = el("result-model-foot");
    if (foot) foot.textContent = data.result_footer || "";
    renderEvents("event-list", data.suggested_events, { showTargets: false });
    renderPeerList(data.suggested_peers || []);
    highlightPublicTribeCard(data.cluster);
    setAtlasIntro(
      `You matched <strong>Tribe ID ${data.cluster}</strong> — <strong>${escapeHtml(data.tribe_name)}</strong>. ` +
        `Scroll this card row: <strong>yours is outlined in rose</strong> and labeled “Your tribe”.`,
    );
    const resultEl = el("result");
    resultEl.classList.remove("hidden");
    setResultsJumpAvailable(true);
    resultEl.classList.remove("result-shell--reveal");
    void resultEl.offsetWidth;
    resultEl.classList.add("result-shell--reveal");
    window.setTimeout(() => {
      resultEl.classList.remove("result-shell--reveal");
    }, 900);
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    const msg = e instanceof TypeError && String(e.message || "").includes("fetch")
      ? "Network error — is Flask running? Start python app_server.py, use the URL it prints, or add ?api=http://127.0.0.1:PORT for Live Preview."
      : `Something went wrong: ${e instanceof Error ? e.message : String(e)}`;
    err.textContent = msg;
    el("result").classList.add("hidden");
    const provCatch = el("result-provenance");
    if (provCatch) provCatch.textContent = "";
    setResultsJumpAvailable(false);
    setAtlasIntro(ATLAS_INTRO_DEFAULT);
  } finally {
    btn.disabled = false;
  }
}

async function loadAdminEvents() {
  try {
    const r = await fetch(apiUrl("/api/events"));
    const data = await r.json();
    renderEvents("admin-event-list", data.events || []);
  } catch {
    el("admin-event-list").innerHTML =
      '<p class="hint">Could not load events.</p>';
  }
}

async function adminPostEvent() {
  el("admin-error").textContent = "";
  el("admin-ok").textContent = "";
  const token = el("admin-token").value.trim();
  const title = el("ev-title").value.trim();
  const when_iso = el("ev-when").value;
  const place = el("ev-place").value.trim();
  const description = el("ev-desc").value.trim();
  const hobby_tags = Array.from(
    document.querySelectorAll("#admin-hobby-grid input:checked"),
  ).map((i) => i.value);
  const clusters = Array.from(
    document.querySelectorAll("#cluster-picks input:checked"),
  ).map((i) => parseInt(i.value, 10));
  if (!title || !when_iso) {
    el("admin-error").textContent = "Title and date/time are required.";
    return;
  }
  const whenNorm =
    when_iso.length === 16 ? `${when_iso}:00` : when_iso;
  const btn = el("admin-submit");
  btn.disabled = true;
  try {
    const r = await fetch(apiUrl("/api/events"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Token": token,
      },
      body: JSON.stringify({
        title,
        when_iso: whenNorm,
        place,
        description,
        hobby_tags,
        clusters,
      }),
    });
    const data = await r.json();
    if (!r.ok) {
      el("admin-error").textContent = data.error || "Failed";
      return;
    }
    el("admin-ok").textContent = "Event published.";
    el("ev-title").value = "";
    el("ev-place").value = "";
    el("ev-desc").value = "";
    document
      .querySelectorAll("#admin-hobby-grid input:checked, #cluster-picks input:checked")
      .forEach((i) => {
        i.checked = false;
      });
    await loadAdminEvents();
  } catch (e) {
    el("admin-error").textContent = "Network error.";
  } finally {
    btn.disabled = false;
  }
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const name = tab.getAttribute("data-tab");
      document.querySelectorAll(".tab").forEach((t) => {
        t.classList.toggle("active", t === tab);
        t.setAttribute("aria-selected", t === tab ? "true" : "false");
      });
      const pStudent = el("panel-student");
      const pGuide = el("panel-guide");
      const pAdmin = el("panel-admin");
      pStudent.classList.toggle("hidden", name !== "student");
      pGuide.classList.toggle("hidden", name !== "guide");
      pAdmin.classList.toggle("hidden", name !== "admin");
      pStudent.setAttribute("aria-hidden", name === "student" ? "false" : "true");
      pGuide.setAttribute("aria-hidden", name === "guide" ? "false" : "true");
      pAdmin.setAttribute("aria-hidden", name === "admin" ? "false" : "true");
      if (name === "admin") loadAdminEvents();
    });
  });
}

async function loadTribesContext() {
  try {
    const r = await fetch(apiUrl("/api/tribes"));
    if (r.ok) tribesData = await r.json();
  } catch {
    tribesData = null;
  }
}

async function loadMeta() {
  try {
    const r = await fetch(apiUrl("/api/meta"));
    if (r.ok) metaData = await r.json();
  } catch {
    metaData = null;
  }
}

function renderDemoStats() {
  const root = el("demo-stats");
  if (!root) return;
  if (!metaData) {
    root.innerHTML = "<p class=\"hint\">Stats unavailable (is the server running?).</p>";
    return;
  }
  root.innerHTML = `
    <div class="stat"><strong>${escapeHtml(String(metaData.total_profiles))}</strong><span>profiles in survey pool</span></div>
    <div class="stat"><strong>${escapeHtml(String(metaData.k_clusters))}</strong><span>interest tribes</span></div>
    <div class="stat"><strong>Survey-based</strong><span>hobbies, society time, comfort &amp; friendships</span></div>
  `;
}

function fillFacultyYearSelects() {
  const fac = el("faculty");
  const yr = el("year");
  if (!fac || !yr || !metaData) return;
  const facs = metaData.faculties || [];
  const years = metaData.years || [];
  fac.replaceChildren();
  yr.replaceChildren();
  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = "Select your faculty";
  fac.appendChild(opt0);
  facs.forEach((f) => {
    const o = document.createElement("option");
    o.value = f;
    o.textContent = f;
    fac.appendChild(o);
  });
  const y0 = document.createElement("option");
  y0.value = "";
  y0.textContent = "Select year";
  yr.appendChild(y0);
  years.forEach((y) => {
    const o = document.createElement("option");
    o.value = y;
    o.textContent = y;
    yr.appendChild(o);
  });
}

function readSocMember() {
  const r = document.querySelector('input[name="soc_member"]:checked');
  return !!(r && r.value === "yes");
}

function syncSocMemberUi() {
  const on = readSocMember();
  const hoursWrap = el("soc-hours-wrap");
  const societiesWrap = el("soc-societies-wrap");
  if (hoursWrap) {
    hoursWrap.style.opacity = on ? "1" : "0.45";
    hoursWrap.querySelectorAll("input").forEach((inp) => {
      inp.disabled = !on;
    });
  }
  if (societiesWrap) {
    societiesWrap.style.opacity = on ? "1" : "0.45";
    societiesWrap.querySelectorAll("#society-grid input").forEach((inp) => {
      inp.disabled = !on;
      if (!on) inp.checked = false;
    });
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadMeta(), loadTribesContext()]);
  renderDemoStats();
  fillFacultyYearSelects();
  buildHobbyGrid("hobby-grid");
  buildChipGrid("society-grid", SOCIETIES, { idPrefix: "soc" });
  buildHobbyGrid("admin-hobby-grid");
  buildClusterPicks();
  renderStudentInsight();
  renderAdminTribeAtlas();
  renderPublicTribeShowcase();
  setupTabs();
  ["soc_hours", "comfort", "friends", "same_prov_pct", "same_fac_pct"].forEach((id) => {
    el(id).addEventListener("input", syncSliderLabels);
  });
  document.querySelectorAll('input[name="soc_member"]').forEach((inp) => {
    inp.addEventListener("change", () => {
      syncSocMemberUi();
      syncSliderLabels();
    });
  });
  syncSocMemberUi();
  syncSliderLabels();
  el("submit").addEventListener("click", predict);
  el("admin-submit").addEventListener("click", adminPostEvent);
  el("scroll-to-atlas")?.addEventListener("click", () => {
    el("tribe-atlas-public")?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  el("try-another-mix")?.addEventListener("click", () => {
    el("step-hobbies")?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  setResultsJumpAvailable(false);
  const pStudent = el("panel-student");
  const pGuide = el("panel-guide");
  const pAdmin = el("panel-admin");
  pStudent?.setAttribute("aria-hidden", "true");
  pGuide?.setAttribute("aria-hidden", "false");
  pAdmin?.setAttribute("aria-hidden", "true");
});
