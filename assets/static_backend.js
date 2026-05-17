// static_backend.js: intercepts fetch calls to /api/* and serves them locally
// This allows the app to run on GitHub Pages without any Python backend.

let db = null;
const originalFetch = window.fetch;

async function loadStaticDb() {
  if (db) return db;
  const basePath = window.location.pathname.replace(/\/[^/]*$/, '/');
  const res = await originalFetch(basePath + "model_data.json");
  db = await res.json();
  return db;
}

window.fetch = async function(url, options) {
  if (typeof url === 'string' && url.includes('/api/')) {
    await loadStaticDb();
    
    const urlObj = new URL(url, window.location.origin);
    const path = urlObj.pathname.replace(/\/$/, '');

    if (path.endsWith('/api/meta')) {
      return new Response(JSON.stringify({
        k_clusters: db.cluster_centers.length,
        total_profiles: db.cohort.length,
        faculties: ["Computer Engineering", "Computer Science (CS)", "Data Science", "Electrical Engineering (EE)", "Mechanical Engineering (ME)", "Software Engineering", "Other"],
        years: ["1st Year (Freshie)", "2nd Year", "3rd Year", "4th Year"]
      }));
    }

    if (path.endsWith('/api/tribes')) {
      const tribes = Object.keys(db.cluster_profiles).map(k => ({
        id: parseInt(k, 10),
        name: db.cluster_profiles[k].name,
        n: db.cluster_profiles[k].n,
        avg_silo: db.cluster_profiles[k].avg_silo,
        top_hobbies: db.cluster_profiles[k].top_hobbies,
        admin_guide: `Tribe ${k} admin guide placeholder`
      }));
      return new Response(JSON.stringify({
        why_title: "Why does it matter?",
        why: ["Mixers can be designed around proven interests.", "Students don't have to guess who likes what."],
        limits_title: "Limitations",
        limits: ["Just a clustering demo.", "Not a guarantee of friendship."],
        next_title: "Next Steps",
        next: ["Post an event to test the waters."],
        tribes: tribes
      }));
    }

    if (path.endsWith('/api/events')) {
      if (options && options.method === 'POST') {
        const body = JSON.parse(options.body);
        db.events.push(body);
        return new Response(JSON.stringify({ok: true}));
      }
      return new Response(JSON.stringify({ events: db.events || [] }));
    }

    if (path.endsWith('/api/predict')) {
      const body = JSON.parse(options.body);
      
      // Build vector
      const vec = [];
      db.feature_cols.forEach(col => {
        if (col.startsWith('h_')) {
          const hobbyName = col.substring(2).replace('__', ' / ');
          vec.push(body.hobbies.includes(hobbyName) ? 1.0 : 0.0);
        } else if (col === 'SocHours') {
          vec.push(body.soc_hours || 0);
        } else if (col === 'ComfortScore') {
          vec.push(body.comfort || 0);
        } else {
          vec.push(0.0);
        }
      });
      
      // Standardize
      for (let i=0; i<vec.length; i++) {
        vec[i] = (vec[i] - db.scaler_mean[i]) / db.scaler_scale[i];
      }
      
      // Distance
      let bestDist = Infinity;
      let cluster = 0;
      db.cluster_centers.forEach((center, idx) => {
        let dist = 0;
        for (let i=0; i<vec.length; i++) {
          dist += Math.pow(center[i] - vec[i], 2);
        }
        if (dist < bestDist) {
          bestDist = dist;
          cluster = idx;
        }
      });

      const prof = db.cluster_profiles[cluster.toString()];
      const topHobbies = prof.top_hobbies || [];

      // Find peers
      const suggested_peers = db.cohort
        .filter(p => p._cluster === cluster)
        .slice(0, 3)
        .map(p => ({
          display: p.Reg || "A Student",
          faculty: p.Faculty,
          year: p.Year,
          shared_hobbies: topHobbies,
          hobbies_preview: p.Hobbies || "Various",
          society_cue: p.Societies
        }));

      const events = (db.events || []).filter(e => (e.clusters || []).includes(cluster));

      return new Response(JSON.stringify({
        cluster: cluster,
        tribe_name: prof.name || `Tribe ${cluster}`,
        tribe_size: prof.n,
        tribe_avg_silo: prof.avg_silo,
        silo_index: 0.5,
        silo_label: "Moderate",
        top_hobbies: topHobbies,
        comfort_used: body.comfort,
        soc_hours_used: body.soc_hours,
        recommendation: `You belong to Tribe ${cluster}. Reach out to people who like ${topHobbies.join(', ')}.`,
        suggested_peers: suggested_peers,
        suggested_events: events,
        assignment_explain: { title: "How you were matched", lines: ["K-Means calculated your distance to the 8 tribes."] },
        result_footer: "Powered by static JavaScript."
      }));
    }
  }

  return originalFetch(url, options);
};
