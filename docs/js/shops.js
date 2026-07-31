function initShopFilters() {
  const search = document.getElementById("shop-search");
  const areaFilter = document.getElementById("shop-area-filter");
  const signalFilter = document.getElementById("shop-signal-filter");
  const tbody = document.querySelector("#shops-table tbody");
  const countEl = document.getElementById("shops-count");
  if (!tbody) return;

  const rows = [...tbody.querySelectorAll("tr")];

  function applyFilters() {
    const q = (search?.value || "").trim().toLowerCase();
    const area = areaFilter?.value || "";
    const signal = signalFilter?.value || "";
    let visible = 0;

    rows.forEach((row) => {
      const name = row.dataset.name || "";
      const rowArea = row.dataset.area || "";
      const signals = (row.dataset.signals || "").split(",").filter(Boolean);
      const matchName = !q || name.includes(q);
      const matchArea = !area || rowArea === area;
      const matchSignal = !signal || signals.includes(signal);
      const show = matchName && matchArea && matchSignal;
      row.style.display = show ? "" : "none";
      if (show) visible += 1;
    });

    if (countEl) countEl.textContent = String(visible);
  }

  search?.addEventListener("input", applyFilters);
  areaFilter?.addEventListener("change", applyFilters);
  signalFilter?.addEventListener("change", applyFilters);
}

async function initShops() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const root = document.getElementById("shops-root");

  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === region);
  });

  try {
    const index = await loadJson(`shops_${region}.json`);
    root.innerHTML = renderShopList(index.shops || [], region, index.region_label);
    initShopFilters();
    document.title = `店舗一覧 ${index.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initShops();
