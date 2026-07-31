async function initIndex() {
  const updatedEl = document.getElementById("updated-at");
  const cardsEl = document.getElementById("region-cards");
  const chartEl = document.getElementById("price-chart");

  try {
    const summary = await loadJson("summary.json");
    updatedEl.textContent = `最終更新: ${summary.updated_at}`;

    cardsEl.innerHTML = summary.regions
      .map((r) => {
        return `
          <article class="card">
            <h2>${escapeHtml(r.label)}</h2>
            <p class="sub">${escapeHtml(r.subtitle)}</p>
            <div class="stat-grid">
              <div class="stat">
                <div class="label">掲載店舗数（公式）</div>
                <div class="value">${r.total_shops?.toLocaleString("ja-JP") ?? "—"}</div>
              </div>
              <div class="stat">
                <div class="label">90分 中央値</div>
                <div class="value">${yen(r.price_median)}</div>
              </div>
              <div class="stat">
                <div class="label">クーポン掲載</div>
                <div class="value">${r.coupon_count ?? 0}件</div>
              </div>
              <div class="stat">
                <div class="label">今すぐ案内可（サンプル）</div>
                <div class="value">${r.available_now ?? 0}店</div>
              </div>
            </div>
            <a class="btn" href="area.html?region=${encodeURIComponent(r.key)}">詳細を見る</a>
          </article>
        `;
      })
      .join("");

    const maxMedian = Math.max(
      ...summary.regions.map((r) => r.price_median || 0),
      1
    );

    chartEl.innerHTML = summary.regions
      .map((r) => {
        const pct = r.price_median ? (r.price_median / maxMedian) * 100 : 0;
        return `
          <div class="bar-row">
            <div class="bar-label">${escapeHtml(r.label)}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
            <div class="bar-value">${yen(r.price_median)}</div>
          </div>
        `;
      })
      .join("");
  } catch (err) {
    updatedEl.textContent = "データの読込に失敗しました";
    cardsEl.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initIndex();
