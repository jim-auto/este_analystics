function renderShopTable(shops, extraCols = []) {
  if (!shops?.length) return "<p class='muted'>該当データなし</p>";
  const headers = ["店舗", "エリア", "90分", ...extraCols, ""];
  return `
    <div class="table-scroll">
      <table>
        <thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
        <tbody>
          ${shops
            .map((s) => {
              const extras = extraCols.map((col) => {
                if (col === "カード") return s.credit_card ? "OK" : "—";
                if (col === "クーポン") return s.coupon_count ? `${s.coupon_count}枚` : "—";
                if (col === "営業") return escapeHtml((s.hours || "—").slice(0, 24));
                return "—";
              });
              return `
              <tr>
                <td><a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.name)}</a></td>
                <td>${escapeHtml(s.sub_area || s.prefecture || "—")}</td>
                <td>${yen(s.price_90min)}</td>
                ${extras.map((e) => `<td>${e}</td>`).join("")}
                <td><span class="tag">${escapeHtml(s.shop_type || "")}</span></td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderPriceByArea(rows) {
  if (!rows?.length) return "<p class='muted'>料金データなし</p>";
  const max = Math.max(...rows.map((r) => r.price_median || 0), 1);
  return rows
    .map(
      (r) => `
    <div class="bar-row">
      <div class="bar-label">${escapeHtml(r.name)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${((r.price_median || 0) / max) * 100}%"></div></div>
      <div class="bar-value">${yen(r.price_median)} <small>(${r.shop_count}店)</small></div>
    </div>`
    )
    .join("");
}

function renderPriceByType(rows) {
  if (!rows?.length) return "<p class='muted'>データなし</p>";
  return `
    <table>
      <thead><tr><th>店舗型</th><th>店数</th><th>90分中央値</th><th>最安</th><th>最高</th></tr></thead>
      <tbody>
        ${rows
          .map(
            (r) => `
          <tr>
            <td>${escapeHtml(r.name)}</td>
            <td>${r.shop_count}</td>
            <td>${yen(r.price_median)}</td>
            <td>${yen(r.price_min)}</td>
            <td>${yen(r.price_max)}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>`;
}

function renderCouponTabs(byCategory) {
  const cats = Object.keys(byCategory || {});
  if (!cats.length) return "<p>クーポンなし</p>";

  const tabs = cats
    .map(
      (cat, i) =>
        `<button class="tab-btn${i === 0 ? " active" : ""}" data-tab="${escapeHtml(cat)}">${escapeHtml(cat)} (${byCategory[cat].length})</button>`
    )
    .join("");

  const panels = cats
    .map(
      (cat, i) => `
    <div class="tab-panel${i === 0 ? " active" : ""}" data-panel="${escapeHtml(cat)}">
      <div class="coupon-list">
        ${byCategory[cat]
          .map(
            (c) => `
          <article class="coupon-item">
            <h3>${escapeHtml(c.title)}</h3>
            <p><strong>${escapeHtml(c.shop_name)}</strong> — ${escapeHtml(c.area_raw)}</p>
            <p>${escapeHtml(c.description)}</p>
            <p>${c.price_90min ? `90分 ${yen(c.price_90min)} · ` : ""}<a href="${escapeHtml(c.coupon_url)}" target="_blank" rel="noopener">公式で確認</a></p>
          </article>`
          )
          .join("")}
      </div>
    </div>`
    )
    .join("");

  return `<div class="tabs">${tabs}</div>${panels}`;
}

function initTabs(root) {
  root.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cat = btn.dataset.tab;
      root.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
      root.querySelectorAll(".tab-panel").forEach((p) =>
        p.classList.toggle("active", p.dataset.panel === cat)
      );
    });
  });
}

function regionMap(regions) {
  const map = {};
  regions.forEach((r) => {
    map[r.key] = r;
  });
  return map;
}

function renderCompareRows(regions) {
  const byKey = regionMap(regions);
  const keys = ["kanto", "chubu", "kansai"];
  const cell = (key, val) => (byKey[key] ? val(byKey[key]) : "—");

  const rows = [
    ["掲載店舗数（公式）", (r) => r.total_shops?.toLocaleString("ja-JP") ?? "—"],
    ["90分 中央値", (r) => yen(r.price_median)],
    ["90分 最安", (r) => yen(r.price_min)],
    ["90分 最高", (r) => yen(r.price_max)],
    ["今すぐ案内可", (r) => `${r.available_now ?? 0}店`],
    ["深夜営業（LAST等）", (r) => `${r.late_night ?? 0}店`],
    ["クレカ対応率", (r) => `${r.credit_card_rate ?? 0}%`],
    ["クーポンあり", (r) => `${r.with_coupon_rate ?? 0}%`],
    ["クーポン掲載数", (r) => `${r.coupon_count ?? 0}件`],
  ];

  return rows
    .map(
      ([label, fn]) => `
    <tr>
      <th>${escapeHtml(label)}</th>
      ${keys.map((k) => `<td>${cell(k, fn)}</td>`).join("")}
    </tr>`
    )
    .join("");
}

function renderTypeChart(regions) {
  const types = ["マンション(個室)", "派遣・出張専門", "店舗型"];
  return types
    .map((type) => {
      const bars = regions
        .map((r) => {
          const match = (r.price_by_shop_type || []).find((t) => t.name === type);
          return { label: r.label, median: match?.price_median || 0 };
        })
        .filter((b) => b.median > 0);
      if (!bars.length) return "";

      const max = Math.max(...bars.map((b) => b.median));
      return `
        <div class="type-group">
          <h3>${escapeHtml(type)}</h3>
          ${bars
            .map(
              (b) => `
            <div class="bar-row">
              <div class="bar-label">${escapeHtml(b.label)}</div>
              <div class="bar-track"><div class="bar-fill bar-fill-alt" style="width:${(b.median / max) * 100}%"></div></div>
              <div class="bar-value">${yen(b.median)}</div>
            </div>`
            )
            .join("")}
        </div>`;
    })
    .join("");
}

function renderMovers(movers) {
  if (!movers?.length) return "<p class='muted'>UP店舗なし</p>";
  return `
    <div class="table-scroll">
      <table>
        <thead><tr><th>エリア</th><th>部門</th><th>順位</th><th>店舗</th><th>場所</th></tr></thead>
        <tbody>
          ${movers
            .map(
              (m) => `
            <tr>
              <td>${escapeHtml(m.region)}</td>
              <td>${escapeHtml(m.category?.replace("ランキング", ""))}</td>
              <td>${m.rank ?? "—"} <span class="trend-up">UP</span></td>
              <td><a href="${escapeHtml(m.shop_url)}" target="_blank" rel="noopener">${escapeHtml(m.shop_name)}</a></td>
              <td>${escapeHtml(m.location)}</td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderBestCoupons(coupons) {
  if (!coupons?.length) return "<p class='muted'>データなし</p>";
  return coupons
    .map(
      (c) => `
    <article class="coupon-item">
      <div class="coupon-head">
        <span class="tag">${escapeHtml(c.region)}</span>
        ${c.discount_yen ? `<span class="discount-badge">-${c.discount_yen.toLocaleString("ja-JP")}円</span>` : ""}
        <span class="tag tag-muted">${escapeHtml(c.category || "")}</span>
      </div>
      <h3>${escapeHtml(c.title)}</h3>
      <p><strong>${escapeHtml(c.shop_name)}</strong> — ${escapeHtml(c.area_raw)}</p>
      <p>${escapeHtml(c.description)}</p>
      <p>${c.price_90min ? `90分 ${yen(c.price_90min)} · ` : ""}<a href="${escapeHtml(c.coupon_url)}" target="_blank" rel="noopener">公式で確認</a></p>
    </article>`
    )
    .join("");
}

function renderBudgetPicks(picks) {
  if (!picks?.length) return "<p class='muted'>データなし</p>";
  return `
    <div class="table-scroll">
      <table>
        <thead><tr><th>エリア</th><th>店舗</th><th>サブエリア</th><th>90分</th><th>クーポン</th></tr></thead>
        <tbody>
          ${picks
            .map(
              (s) => `
            <tr>
              <td>${escapeHtml(s.region)}</td>
              <td><a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.name)}</a></td>
              <td>${escapeHtml(s.sub_area || "—")}</td>
              <td>${yen(s.price_90min)}</td>
              <td>${s.coupon_count ? `${s.coupon_count}枚` : "—"}</td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}
