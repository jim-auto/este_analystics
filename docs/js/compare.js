async function initCompare() {
  const root = document.getElementById("compare-root");

  try {
    const summary = await loadJson("summary.json");
    const regions = summary.regions;

    const subAreaBlocks = await Promise.all(
      regions.map(async (r) => {
        const data = await loadJson(`${r.key}.json`);
        return {
          label: r.label,
          rows: data.insights.shops.price_by_sub_area.slice(0, 8),
        };
      })
    );

    root.innerHTML = `
      <section class="area-header">
        <h1>東名阪 3エリア比較</h1>
        <p class="lead">料金・利便性・クーポンを横並びで比較。最終更新: ${escapeHtml(summary.updated_at)}</p>
      </section>

      <section class="panel">
        <h2>主要指標</h2>
        <div class="table-scroll">
          <table>
            <thead><tr><th>項目</th><th>東京</th><th>名古屋</th><th>大阪</th></tr></thead>
            <tbody>${renderCompareRows(regions)}</tbody>
          </table>
        </div>
      </section>

      <section class="grid-2">
        <div class="panel">
          <h2>90分 中央値</h2>
          <div class="chart-bars">
            ${regions
              .map((r) => {
                const max = Math.max(...regions.map((x) => x.price_median || 0), 1);
                const pct = ((r.price_median || 0) / max) * 100;
                return `
                <div class="bar-row">
                  <div class="bar-label">${escapeHtml(r.label)}</div>
                  <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
                  <div class="bar-value">${yen(r.price_median)}</div>
                </div>`;
              })
              .join("")}
          </div>
        </div>
        <div class="panel">
          <h2>店舗型別 中央値</h2>
          ${renderTypeChart(regions)}
        </div>
      </section>

      <section class="panel">
        <h2>主要サブエリア別 90分中央値</h2>
        <div class="grid-2">
          ${subAreaBlocks
            .map(
              (block) => `
            <div>
              <h3>${escapeHtml(block.label)}</h3>
              ${renderPriceByArea(block.rows)}
            </div>`
            )
            .join("")}
        </div>
      </section>

      <section class="panel">
        <h2>お得クーポン TOP</h2>
        <div class="coupon-list">${renderBestCoupons(summary.highlights?.best_coupons)}</div>
      </section>
    `;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initCompare();
