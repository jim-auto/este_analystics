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
    document.title = `店舗一覧 ${index.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initShops();
