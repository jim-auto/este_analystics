async function initBbs() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const root = document.getElementById("bbs-root");

  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === region);
  });

  try {
    const data = await loadJson(`${region}.json`);
    const bbs = data.bbs || {};
    bbs.region_key = region;
    root.innerHTML = renderBbsInsights(bbs, data.region_label);
    document.title = `掲示板解析 ${data.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initBbs();
