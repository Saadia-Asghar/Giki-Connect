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

function buildHobbies() {
  const grid = el("hobby-grid");
  grid.innerHTML = "";
  HOBBIES.forEach((h) => {
    const id = `h-${h.replace(/[^a-zA-Z0-9]+/g, "-")}`;
    const lab = document.createElement("label");
    const inp = document.createElement("input");
    inp.type = "checkbox";
    inp.value = h;
    inp.id = id;
    const sp = document.createElement("span");
    sp.textContent = h;
    lab.appendChild(inp);
    lab.appendChild(sp);
    grid.appendChild(lab);
  });
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
      el("result").classList.remove("visible");
      return;
    }
    el("tribe-title").textContent = `Tribe ${data.cluster} — ${data.tribe_name}`;
    el("tribe-meta").textContent = `About ${data.tribe_size} similar profiles in the training set · avg silo in tribe ${data.tribe_avg_silo}`;
    el("silo-fill").style.width = `${Math.min(100, data.silo_index * 100)}%`;
    el("silo-label").textContent = `Silo index ${data.silo_index} — ${data.silo_label}`;
    const pills = el("tribe-hobbies");
    pills.innerHTML = "";
    (data.top_hobbies || []).forEach((h) => {
      const sp = document.createElement("span");
      sp.textContent = h;
      pills.appendChild(sp);
    });
    el("rec").textContent = data.recommendation;
    el("result").classList.add("visible");
  } catch (e) {
    err.textContent = "Cannot reach the app server. Run python app_server.py from the project folder.";
    el("result").classList.remove("visible");
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  buildHobbies();
  ["soc_hours", "comfort", "same_prov_pct", "same_fac_pct"].forEach((id) => {
    el(id).addEventListener("input", syncSliderLabels);
  });
  syncSliderLabels();
  el("submit").addEventListener("click", predict);
});
