async function initIndex() {
  const updatedEl = document.getElementById("updated-at");
  const cardsEl = document.getElementById("region-cards");
  const chartEl = document.getElementById("price-chart");
  const compareBody = document.querySelector("#compare-table tbody");

  try {
    const summary = await loadJson("summary.json");
    updatedEl.textContent = `最終更新: ${summary.updated_at}（店舗リスト先頭${summary.regions[0]?.sampled_shops ?? 300}件をサンプル集計）`;

    cardsEl.innerHTML = summary.regions
      .map(
        (r) => `
        <article class="card">
          <h2>${escapeHtml(r.label)}</h2>
          <p class="sub">${escapeHtml(r.subtitle)}</p>
          <div class="stat-grid">
            <div class="stat"><div class="label">90分 中央値</div><div class="value">${yen(r.price_median)}</div></div>
            <div class="stat"><div class="label">最安〜最高</div><div class="value">${yen(r.price_min)}〜${yen(r.price_max)}</div></div>
            <div class="stat"><div class="label">今すぐ案内可</div><div class="value">${r.available_now ?? 0}店</div></div>
            <div class="stat"><div class="label">クレカ対応</div><div class="value">${r.credit_card_rate ?? 0}%</div></div>
          </div>
          <a class="btn" href="area.html?region=${encodeURIComponent(r.key)}">詳細を見る</a>
        </article>`
      )
      .join("");

    compareBody.innerHTML = renderCompareRows(summary.regions);

    const maxMedian = Math.max(...summary.regions.map((r) => r.price_median || 0), 1);
    chartEl.innerHTML = summary.regions
      .map((r) => {
        const pct = r.price_median ? (r.price_median / maxMedian) * 100 : 0;
        return `
          <div class="bar-row">
            <div class="bar-label">${escapeHtml(r.label)}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
            <div class="bar-value">${yen(r.price_median)}</div>
          </div>`;
      })
      .join("");

    document.getElementById("type-chart").innerHTML = renderTypeChart(summary.regions);
    document.getElementById("ranking-movers").innerHTML = renderMovers(summary.highlights?.ranking_movers);
    document.getElementById("best-coupons").innerHTML = renderBestCoupons(summary.highlights?.best_coupons);
    document.getElementById("budget-picks").innerHTML = renderBudgetPicks(summary.highlights?.budget_picks);
  } catch (err) {
    updatedEl.textContent = "データの読込に失敗しました";
    cardsEl.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initIndex();
