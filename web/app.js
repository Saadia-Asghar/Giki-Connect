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

function el(id) {
  return document.getElementById(id);
}

function buildHobbyGrid(containerId) {
  const grid = el(containerId);
  if (!grid) return;
  grid.innerHTML = "";
  HOBBIES.forEach((h) => {
    const lab = document.createElement("label");
    const inp = document.createElement("input");
    inp.type = "checkbox";
    inp.value = h;
    const sp = document.createElement("span");
    sp.textContent = h;
    lab.appendChild(inp);
    lab.appendChild(sp);
    grid.appendChild(lab);
  });
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
    sp.textContent = `Tribe ${c}`;
    lab.appendChild(inp);
    lab.appendChild(sp);
    box.appendChild(lab);
  }
}

function readSliders() {
  return {
    soc_hours: parseFloat(el("soc_hours").value),
    comfort: parseFloat(el("comfort").value),
    same_prov_pct: parseFloat(el("same_prov_pct").value),
    same_fac_pct: parseFloat(el("same_fac_pct").value),
  };
}

function syncSliderLabels() {
  const s = readSliders();
  el("soc_hours_v").textContent = `${s.soc_hours} h/wk`;
  el("comfort_v").textContent = String(s.comfort);
  el("same_prov_pct_v").textContent = `${Math.round(s.same_prov_pct)}%`;
  el("same_fac_pct_v").textContent = `${Math.round(s.same_fac_pct)}%`;
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

function renderEvents(targetEl, events) {
  const root = el(targetEl);
  root.innerHTML = "";
  if (!events || !events.length) {
    root.innerHTML =
      '<p class="hint" style="margin:0">No events yet — admin can post one in the Admin tab.</p>';
    return;
  }
  events.forEach((e) => {
    const div = document.createElement("div");
    div.className = "event-card";
    const tags = (e.hobby_tags || []).join(", ");
    const cl = (e.clusters || []).length
      ? ` · Tribes ${e.clusters.join(", ")}`
      : "";
    div.innerHTML = `<h4>${escapeHtml(e.title || "")}</h4><div class="meta">${escapeHtml(fmtWhen(e.when_iso))} · ${escapeHtml(e.place || "TBA")}${cl}</div><p>${escapeHtml(e.description || "")}</p><div class="meta">Tags: ${escapeHtml(tags || "—")}</div>`;
    root.appendChild(div);
  });
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function renderPeerList(peers) {
  const root = el("peer-list");
  root.innerHTML = "";
  if (!peers || !peers.length) {
    root.innerHTML =
      '<p class="hint" style="margin:0">No cohort rows for this cluster (check combined_with_clusters.csv).</p>';
    return;
  }
  peers.forEach((p) => {
    const div = document.createElement("div");
    div.className = "peer-row";
    const shared = (p.shared_hobbies || []).join(", ") || "—";
    div.innerHTML = `<div class="who">${escapeHtml(p.display)}</div><div class="meta">${escapeHtml(p.faculty || "")} · ${escapeHtml(p.province || "")}</div><div class="meta">${escapeHtml(p.hobbies_preview || "")}</div><div class="shared">Shared with you: ${escapeHtml(shared)} · score ${p.overlap}</div>`;
    root.appendChild(div);
  });
}

async function predict() {
  const err = el("error");
  err.textContent = "";
  const hobbies = Array.from(
    document.querySelectorAll("#hobby-grid input:checked"),
  ).map((i) => i.value);
  const body = { hobbies, ...readSliders() };
  const btn = el("submit");
  btn.disabled = true;
  try {
    const r = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) {
      err.textContent = data.error || "Request failed";
      el("result").classList.add("hidden");
      return;
    }
    el("tribe-title").textContent = `Tribe ${data.cluster} — ${data.tribe_name}`;
    el("tribe-meta").textContent = `About ${data.tribe_size} similar profiles in the training set · avg silo in tribe ${data.tribe_avg_silo}`;
    el("model-note").textContent = data.model_note || "";
    el("silo-fill").style.width = `${Math.min(100, data.silo_index * 100)}%`;
    el("silo-label").textContent = `${data.silo_index} — ${data.silo_label}`;
    const pills = el("tribe-hobbies");
    pills.innerHTML = "";
    (data.top_hobbies || []).forEach((h) => {
      const sp = document.createElement("span");
      sp.textContent = h;
      pills.appendChild(sp);
    });
    el("rec").textContent = data.recommendation;
    renderEvents("event-list", data.suggested_events);
    renderPeerList(data.suggested_peers || []);
    el("result").classList.remove("hidden");
  } catch (e) {
    err.textContent =
      "Cannot reach the server. Run START_APP.bat or python app_server.py from the project folder.";
    el("result").classList.add("hidden");
  } finally {
    btn.disabled = false;
  }
}

async function loadAdminEvents() {
  try {
    const r = await fetch("/api/events");
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
    const r = await fetch("/api/events", {
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
      el("panel-student").classList.toggle("hidden", name !== "student");
      el("panel-admin").classList.toggle("hidden", name !== "admin");
      if (name === "admin") loadAdminEvents();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  buildHobbyGrid("hobby-grid");
  buildHobbyGrid("admin-hobby-grid");
  buildClusterPicks();
  setupTabs();
  ["soc_hours", "comfort", "same_prov_pct", "same_fac_pct"].forEach((id) => {
    el(id).addEventListener("input", syncSliderLabels);
  });
  syncSliderLabels();
  el("submit").addEventListener("click", predict);
  el("admin-submit").addEventListener("click", adminPostEvent);
});
