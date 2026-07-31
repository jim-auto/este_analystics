function renderRankingTable(rows) {
  if (!rows.length) return "<p class='muted'>データなし</p>";
  return `
    <div class="table-scroll">
      <table>
        <thead><tr><th>順位</th><th>店舗</th><th>エリア</th><th>動向</th></tr></thead>
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
    </div>`;
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
    const couponInsights = data.insights.coupons;
    const price = shopInsights.price_90min;

    const rankingBlocks = Object.entries(data.insights.rankings.top_by_category)
      .map(
        ([cat, rows]) => `
        <section class="panel">
          <h2>${escapeHtml(cat)} TOP10</h2>
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
          <span>サンプル ${data.shop_meta.sampled_shops ?? "—"} / 全 ${data.shop_meta.total_shops?.toLocaleString("ja-JP") ?? "—"} 店</span>
          <a href="${escapeHtml(data.source_urls.ranking)}" target="_blank" rel="noopener">公式ランキング</a>
          <a href="${escapeHtml(data.source_urls.coupons)}" target="_blank" rel="noopener">公式クーポン</a>
          <a href="${escapeHtml(data.source_urls.shoplist)}" target="_blank" rel="noopener">公式店舗一覧</a>
        </div>
      </section>

      <section class="stat-banner">
        <div class="stat"><div class="label">90分 中央値</div><div class="value">${yen(price.median)}</div></div>
        <div class="stat"><div class="label">今すぐ案内可</div><div class="value">${shopInsights.available_now_count}店</div></div>
        <div class="stat"><div class="label">深夜営業</div><div class="value">${shopInsights.late_night_count}店</div></div>
        <div class="stat"><div class="label">クレカ対応</div><div class="value">${shopInsights.credit_card_rate}%</div></div>
        <div class="stat"><div class="label">クーポンあり</div><div class="value">${shopInsights.with_coupon_rate}%</div></div>
      </section>

      <section class="grid-2">
        <div class="panel">
          <h2>90分料金相場</h2>
          <div class="stat-grid">
            <div class="stat"><div class="label">中央値</div><div class="value">${yen(price.median)}</div></div>
            <div class="stat"><div class="label">平均</div><div class="value">${yen(price.avg)}</div></div>
            <div class="stat"><div class="label">最安</div><div class="value">${yen(price.min)}</div></div>
            <div class="stat"><div class="label">最高</div><div class="value">${yen(price.max)}</div></div>
          </div>
          <p class="section-note">料金データ ${price.count} 件（掲載のない店舗は「—」）</p>
        </div>
        <div class="panel">
          <h2>店舗型別の料金</h2>
          ${renderPriceByType(shopInsights.price_by_shop_type)}
        </div>
      </section>

      <section class="panel">
        <h2>サブエリア別 90分中央値</h2>
        <p class="section-note">サンプル内の店舗数が多いエリア順。行きたい場所の相場確認に。</p>
        ${renderPriceByArea(shopInsights.price_by_sub_area)}
      </section>

      <section class="panel">
        <h2>今すぐご案内可の店（最大20件）</h2>
        <p class="section-note">空き状況はリアルタイム変動。予約前に公式で再確認してください。</p>
        ${renderShopTable(shopInsights.available_now_shops, ["カード", "クーポン"])}
      </section>

      <section class="grid-2">
        <div class="panel">
          <h2>コスパ店（安め＋クーポンあり）</h2>
          ${renderShopTable(shopInsights.best_value_shops, ["クーポン"])}
        </div>
        <div class="panel">
          <h2>深夜営業（LAST・29時以降等）</h2>
          ${renderShopTable(shopInsights.late_night_shops, ["営業"])}
        </div>
      </section>

      ${rankingBlocks}

      <section class="panel">
        <h2>クーポン（カテゴリ別）</h2>
        <p class="section-note">全 ${couponInsights.total} 件（限定 ${couponInsights.limited_count} 件）</p>
        <div id="coupon-tabs">${renderCouponTabs(couponInsights.by_category)}</div>
      </section>

      <section class="panel">
        <h2>割引額が大きいクーポン</h2>
        <div class="coupon-list">
          ${(couponInsights.best_discounts || [])
            .map(
              (c) => `
            <article class="coupon-item">
              <div class="coupon-head">
                ${c.discount_yen ? `<span class="discount-badge">-${c.discount_yen.toLocaleString("ja-JP")}円</span>` : ""}
                <span class="tag tag-muted">${escapeHtml(c.category || "")}</span>
              </div>
              <h3>${escapeHtml(c.title)}</h3>
              <p><strong>${escapeHtml(c.shop_name)}</strong> — ${escapeHtml(c.area_raw)}</p>
              <p>${escapeHtml(c.description)}</p>
              <p><a href="${escapeHtml(c.coupon_url)}" target="_blank" rel="noopener">公式で確認</a></p>
            </article>`
            )
            .join("")}
        </div>
      </section>
    `;

    initTabs(document.getElementById("coupon-tabs"));
    document.title = `${data.region_label}エリア | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">読込エラー: ${escapeHtml(err.message)}</p>`;
  }
}

initArea();
