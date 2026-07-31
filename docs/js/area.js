function renderRankingTable(rows) {
  if (!rows.length) return "<p>データなし</p>";
  return `
    <table>
      <thead>
        <tr><th>順位</th><th>店舗</th><th>エリア</th><th>動向</th></tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (r) => `
          <tr>
            <td>${r.rank ?? "—"}</td>
            <td><a href="${escapeHtml(r.shop_url)}" target="_blank" rel="noopener">${escapeHtml(r.shop_name)}</a></td>
            <td>${escapeHtml(r.location)}</td>
            <td>${trendLabel(r.trend)}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderCoupons(coupons) {
  return coupons
    .slice(0, 12)
    .map(
      (c) => `
      <article class="coupon-item">
        <h3>${escapeHtml(c.title)}</h3>
        <p><strong>${escapeHtml(c.shop_name)}</strong> — ${escapeHtml(c.area_raw)}</p>
        <p>${escapeHtml(c.description)}</p>
        <p>${c.price_90min ? `90分 ${yen(c.price_90min)}` : ""} 
           <a href="${escapeHtml(c.coupon_url)}" target="_blank" rel="noopener">公式で確認</a></p>
      </article>`
    )
    .join("");
}

async function initArea() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const root = document.getElementById("area-root");

  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === region);
  });

  try {
    const data = await loadJson(`${region}.json`);
    const shopInsights = data.insights.shops;
    const price = shopInsights.price_90min;

    const rankingBlocks = Object.entries(data.insights.rankings.top_by_category)
      .map(
        ([cat, rows]) => `
        <section class="panel">
          <h2>${escapeHtml(cat)} TOP5</h2>
          ${renderRankingTable(rows)}
        </section>`
      )
      .join("");

    root.innerHTML = `
      <section class="area-header">
        <p class="eyebrow">${escapeHtml(data.region_subtitle)}</p>
        <h1>${escapeHtml(data.region_label)}エリア解析</h1>
        <p class="lead">${escapeHtml(data.region_description)}</p>
        <div class="meta-row">
          <span>更新対象: 店舗サンプル ${data.shop_meta.sampled_shops ?? "—"} / 全 ${data.shop_meta.total_shops?.toLocaleString("ja-JP") ?? "—"} 件</span>
          <a href="${escapeHtml(data.source_urls.ranking)}" target="_blank" rel="noopener">公式ランキング</a>
          <a href="${escapeHtml(data.source_urls.coupons)}" target="_blank" rel="noopener">公式クーポン</a>
        </div>
      </section>

      <section class="grid-2">
        <div class="panel">
          <h2>90分料金相場（サンプル集計）</h2>
          <div class="stat-grid">
            <div class="stat"><div class="label">中央値</div><div class="value">${yen(price.median)}</div></div>
            <div class="stat"><div class="label">平均</div><div class="value">${yen(price.avg)}</div></div>
            <div class="stat"><div class="label">最低</div><div class="value">${yen(price.min)}</div></div>
            <div class="stat"><div class="label">最高</div><div class="value">${yen(price.max)}</div></div>
          </div>
          <p class="lead">料金データ ${price.count} 件 / サンプル ${data.shop_meta.sampled_shops} 店舗</p>
        </div>
        <div class="panel">
          <h2>店舗タイプ内訳</h2>
          ${Object.entries(shopInsights.shop_types)
            .map(([k, v]) => `<p><span class="tag">${escapeHtml(k)}</span> ${v}店</p>`)
            .join("")}
          <h2 style="margin-top:1rem">主要サブエリア</h2>
          ${Object.entries(shopInsights.top_sub_areas)
            .slice(0, 6)
            .map(([k, v]) => `<p>${escapeHtml(k)} — ${v}店</p>`)
            .join("")}
        </div>
      </section>

      ${rankingBlocks}

      <section class="panel">
        <h2>クーポン一覧（上位12件）</h2>
        <div class="coupon-list">${renderCoupons(data.coupons)}</div>
      </section>
    `;

    document.title = `${data.region_label}エリア | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">読込エラー: ${escapeHtml(err.message)}</p>`;
  }
}

initArea();
