async function initShop() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const shopId = params.get("id");
  const root = document.getElementById("shop-root");

  if (!shopId) {
    root.innerHTML = "<p class='error'>店舗IDが指定されていません</p>";
    return;
  }

  try {
    const index = await loadJson(`shops_${region}.json`);
    const shop = (index.shops || []).find((s) => String(s.id) === String(shopId));
    if (!shop) {
      root.innerHTML = `<p class='error'>店舗が見つかりません（ID: ${escapeHtml(shopId)}）</p>`;
      return;
    }
    root.innerHTML = renderShopDetail(shop, region, index.region_label);
    document.title = `${shop.name} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initShop();
