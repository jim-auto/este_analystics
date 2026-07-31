function initSubareaFilters() {
  const search = document.getElementById("subarea-search");
  const sortSelect = document.getElementById("subarea-sort");
  const tbody = document.querySelector("#subareas-table tbody");
  const countEl = document.getElementById("subareas-count");
  if (!tbody) return;

  const rows = [...tbody.querySelectorAll("tr")];

  function applyFilters() {
    const q = (search?.value || "").trim().toLowerCase();
    let visible = 0;

    rows.forEach((row) => {
      const name = row.dataset.name || "";
      const show = !q || name.includes(q);
      row.style.display = show ? "" : "none";
      if (show) visible += 1;
    });

    if (countEl) countEl.textContent = String(visible);
  }

  function applySort() {
    const value = sortSelect?.value || "shop_count-desc";
    const [field, dir] = value.split("-");
    const visibleRows = rows.filter((r) => r.style.display !== "none");

    visibleRows.sort((a, b) => {
      let av;
      let bv;
      if (field === "name") {
        av = a.dataset.name || "";
        bv = b.dataset.name || "";
        return dir === "asc" ? av.localeCompare(bv, "ja") : bv.localeCompare(av, "ja");
      }
      const key = field === "shop_count" ? "shopCount" : field === "price_median" ? "price" : "signals";
      const map = { shopCount: "shop-count", price: "price", signals: "signals" };
      av = Number(a.dataset[map[key]] || 0);
      bv = Number(b.dataset[map[key]] || 0);
      if (field === "price_median" && !a.dataset.price) av = dir === "asc" ? 999999 : 0;
      if (field === "price_median" && !b.dataset.price) bv = dir === "asc" ? 999999 : 0;
      return dir === "asc" ? av - bv : bv - av;
    });

    visibleRows.forEach((row) => tbody.appendChild(row));
  }

  search?.addEventListener("input", () => {
    applyFilters();
    applySort();
  });
  sortSelect?.addEventListener("change", applySort);
}

async function initSubareas() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const root = document.getElementById("subareas-root");

  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === region);
  });

  try {
    const data = await loadJson(`subareas_${region}.json`);
    root.innerHTML = renderSubareaList(data.areas || [], region, data.region_label);
    initSubareaFilters();
    document.title = `サブエリア ${data.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initSubareas();
