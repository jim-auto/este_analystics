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

const FLAG_LABELS = {
  value_hype: "割安訴求＋満点",
  price_mismatch: "料金と割安表現の不一致",
  short_perfect: "短文満点",
  first_visit_hype: "初回短文満点",
  superlative_stack: "褒め言葉の連発",
  generic_praise: "定型的な高評価",
  minimal_text: "極端に短い",
};

function renderRatingDistribution(dist, total) {
  if (!dist) return "";
  const items = [
    ["5.0", dist["5.0"], "var(--warn)"],
    ["4.5-4.9", dist["4.5-4.9"], "var(--accent)"],
    ["4.0-4.4", dist["4.0-4.4"], "var(--accent2)"],
    ["3.0-3.9", dist["3.0-3.9"], "var(--muted)"],
    ["3.0未満", dist.below_3, "var(--danger)"],
    ["評価なし", dist.none, "var(--muted)"],
  ];
  const max = Math.max(...items.map((i) => i[1] || 0), 1);
  return items
    .map(([label, count, color]) => {
      const pct = total ? Math.round((count / total) * 100) : 0;
      return `
        <div class="bar-row">
          <div class="bar-label">${label}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${((count || 0) / max) * 100}%;background:${color}"></div></div>
          <div class="bar-value">${count ?? 0}件 (${pct}%)</div>
        </div>`;
    })
    .join("");
}

function renderFlagBadges(flags) {
  return (flags || [])
    .map((f) => `<span class="warn-badge" title="${escapeHtml(FLAG_LABELS[f] || f)}">⚠ ${escapeHtml(FLAG_LABELS[f] || f)}</span>`)
    .join(" ");
}

function renderFlaggedReviews(reviews) {
  if (!reviews?.length) return "<p class='muted'>注意パターンは見つかりませんでした</p>";
  return `
    <div class="flagged-list">
      ${reviews
        .map(
          (r) => `
        <article class="flagged-item">
          <div class="flagged-head">
            <span class="tag">${escapeHtml(r.region || "")}</span>
            ${r.rating != null ? `<span class="rating-badge">${r.rating}</span>` : ""}
            ${renderFlagBadges(r.flags)}
          </div>
          <h3><a href="${escapeHtml(r.shop_url)}" target="_blank" rel="noopener">${escapeHtml(r.shop_name)}</a></h3>
          <p class="muted">${escapeHtml(r.shop_area || "")} ${r.price_90min ? `· 90分 ${yen(r.price_90min)}` : ""}</p>
          ${r.title ? `<p><strong>${escapeHtml(r.title)}</strong></p>` : ""}
          <p>${escapeHtml(r.excerpt)}${(r.excerpt || "").length >= 160 ? "…" : ""}</p>
          <ul class="reason-list">${(r.reasons || []).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
          <p><a href="${escapeHtml(r.review_url)}" target="_blank" rel="noopener">公式口コミを見る</a></p>
        </article>`
        )
        .join("")}
    </div>`;
}

function fmtCi(ci) {
  if (!ci) return "—";
  return `${ci.point}% [${ci.low}–${ci.high}]`;
}

function sigLabel(item) {
  if (!item) return "—";
  return item.significant_at_005
    ? `<span class="sig-yes">有意 (p&lt;0.05)</span>`
    : `<span class="sig-no">非有意</span>`;
}

function renderStatisticsBlock(stats) {
  if (!stats) return "";
  const rd = stats.rating_descriptive || {};
  const fs = stats.five_star_inference || {};
  const tl = stats.text_length || {};
  const pr = stats.price_rating || {};
  const vk = stats.value_keyword_effect || {};
  const si = stats.suspicious_inference || {};
  const ss = stats.sample_size || {};
  const sc = stats.shop_concentration || {};

  const visitRows = Object.entries(stats.visit_type || {})
    .map(
      ([, v]) => `
      <tr>
        <td>${escapeHtml(v.label || "")}</td>
        <td>${v.count}</td>
        <td>${v.mean ?? "—"}</td>
        <td>${v.five_star_rate ?? "—"}%</td>
      </tr>`
    )
    .join("");

  const tertileRows = pr.by_price_tertile
    ? Object.entries(pr.by_price_tertile)
        .map(
          ([tier, t]) => `
        <tr>
          <td>${tier === "low" ? "低価格帯" : tier === "mid" ? "中価格帯" : "高価格帯"}</td>
          <td>${yen(t.price_range?.[0])}–${yen(t.price_range?.[1])}</td>
          <td>${t.count}</td>
          <td>${t.mean_rating}</td>
          <td>${t.five_star_rate}%</td>
        </tr>`
        )
        .join("")
    : "";

  return `
    <section class="panel stats-panel">
      <h2>📊 統計解析レポート</h2>
      <p class="section-note">サンプル ${ss.reviews ?? "—"} 件（評価あり ${ss.rated ?? "—"} / 店舗 ${ss.unique_shops ?? "—"} / 店舗平均 ${ss.avg_reviews_per_shop ?? "—"} 件）</p>

      <h3>記述統計（評価点数）</h3>
      <div class="stat-grid four-col">
        <div class="stat"><div class="label">平均</div><div class="value">${rd.mean ?? "—"}</div></div>
        <div class="stat"><div class="label">中央値</div><div class="value">${rd.median ?? "—"}</div></div>
        <div class="stat"><div class="label">標準偏差</div><div class="value">${rd.std ?? "—"}</div></div>
        <div class="stat"><div class="label">歪度</div><div class="value">${rd.skewness ?? "—"}</div></div>
      </div>
      <p class="stat-detail">
        範囲 ${rd.min ?? "—"}〜${rd.max ?? "—"} ·
        エントロピー ${rd.entropy_bits ?? "—"} bit
        <span class="muted">（低いほど評価が偏っている）</span>
      </p>

      <h3>満点(5.0)比率の推定</h3>
      <div class="table-scroll">
        <table class="stats-table">
          <thead><tr><th>指標</th><th>値</th><th>95%信頼区間</th><th>検定</th></tr></thead>
          <tbody>
            <tr>
              <td>満点比率</td>
              <td>${fs.rate_pct ?? "—"}%</td>
              <td>${fs.ci_95_pct ? `${fs.ci_95_pct.low}–${fs.ci_95_pct.high}%` : "—"}</td>
              <td>—</td>
            </tr>
            <tr>
              <td> vs 中立50%</td>
              <td>${fs.vs_neutral_50pct?.observed_pct ?? "—"}%</td>
              <td>z=${fs.vs_neutral_50pct?.z_score ?? "—"}</td>
              <td>${sigLabel(fs.vs_neutral_50pct)}</td>
            </tr>
            <tr>
              <td> vs 基準70%</td>
              <td>${fs.vs_benchmark_70pct?.observed_pct ?? "—"}%</td>
              <td>z=${fs.vs_benchmark_70pct?.z_score ?? "—"}</td>
              <td>${sigLabel(fs.vs_benchmark_70pct)}</td>
            </tr>
            <tr>
              <td>注意パターン率</td>
              <td>${si.rate_pct ?? "—"}%</td>
              <td>${si.ci_95_pct ? `${si.ci_95_pct.low}–${si.ci_95_pct.high}%` : "—"}</td>
              <td>—</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3>利用回数別の評価</h3>
      <div class="table-scroll">
        <table class="stats-table">
          <thead><tr><th>区分</th><th>件数</th><th>平均評価</th><th>満点率</th></tr></thead>
          <tbody>${visitRows || "<tr><td colspan='4'>データなし</td></tr>"}</tbody>
        </table>
      </div>

      <h3>文章量と評価</h3>
      <div class="table-scroll">
        <table class="stats-table">
          <thead><tr><th>グループ</th><th>件数</th><th>平均文字数</th><th>中央値</th></tr></thead>
          <tbody>
            <tr><td>全体</td><td>${tl.all?.count ?? "—"}</td><td>${tl.all?.mean ?? "—"}</td><td>${tl.all?.median ?? "—"}</td></tr>
            <tr><td>満点(5.0)</td><td>${tl.rated_5_0?.count ?? "—"}</td><td>${tl.rated_5_0?.mean ?? "—"}</td><td>${tl.rated_5_0?.median ?? "—"}</td></tr>
            <tr><td>5.0未満</td><td>${tl.rated_below_5?.count ?? "—"}</td><td>${tl.rated_below_5?.mean ?? "—"}</td><td>${tl.rated_below_5?.median ?? "—"}</td></tr>
          </tbody>
        </table>
      </div>
      <p class="stat-detail">満点 vs 非満点の文字数差: ${tl.length_gap_5_vs_other ?? "—"} 文字
        <span class="muted">（満点ほど短文の傾向がある場合は要注意）</span></p>

      <h3>料金と評価の関係</h3>
      <p class="stat-detail">
        ピアソン相関 r = ${pr.pearson_r ?? "—"}（n=${pr.n ?? 0}）· ${escapeHtml(pr.interpretation || "")}
        ${pr.region_median_yen ? ` · エリア中央値 ${yen(pr.region_median_yen)}` : ""}
      </p>
      ${tertileRows ? `
      <div class="table-scroll">
        <table class="stats-table">
          <thead><tr><th>価格帯</th><th>90分レンジ</th><th>件数</th><th>平均評価</th><th>満点率</th></tr></thead>
          <tbody>${tertileRows}</tbody>
        </table>
      </div>` : "<p class='muted'>料金データが不足しています</p>"}

      <h3>「割安・コスパ」キーワードの効果</h3>
      <div class="table-scroll">
        <table class="stats-table">
          <thead><tr><th>グループ</th><th>件数</th><th>平均評価</th><th>満点率</th></tr></thead>
          <tbody>
            <tr><td>キーワードあり</td><td>${vk.with_keyword?.count ?? 0}</td><td>${vk.with_keyword?.mean ?? "—"}</td><td>${vk.with_keyword?.five_star_rate ?? "—"}%</td></tr>
            <tr><td>キーワードなし</td><td>${vk.without_keyword?.count ?? 0}</td><td>${vk.without_keyword?.mean ?? "—"}</td><td>${vk.without_keyword?.five_star_rate ?? "—"}%</td></tr>
          </tbody>
        </table>
      </div>
      <p class="stat-detail">
        満点×キーワード共起 χ²=${vk.perfect_score_chi2?.chi2 ?? "—"}
        · ${sigLabel(vk.perfect_score_chi2)}
      </p>

      <h3>店舗集中度</h3>
      <p class="stat-detail">
        2件以上口コミがある店舗: ${sc.shops_with_2plus_reviews ?? "—"} /
        サンプル内すべて満点の店舗: ${sc.shops_all_perfect_in_sample ?? "—"}
        (${sc.perfect_shop_rate_pct ?? "—"}%)
      </p>
    </section>`;
}

function renderCrossRegionStats(reviewSummary) {
  const regions = reviewSummary?.regions || [];
  if (!regions.length) return "";

  return `
    <section class="panel stats-panel">
      <h2>📊 3エリア 統計比較</h2>
      ${(reviewSummary.cross_region_notes || []).map((n) => `<p class="stat-detail">${escapeHtml(n)}</p>`).join("")}
      <div class="table-scroll">
        <table class="stats-table">
          <thead>
            <tr>
              <th>エリア</th><th>n</th><th>平均</th><th>中央値</th><th>σ</th>
              <th>歪度</th><th>満点率</th><th>満点95%CI</th><th>注意率</th><th>r(料金)</th>
            </tr>
          </thead>
          <tbody>
            ${regions
              .map(
                (r) => `
              <tr>
                <td><a href="reviews.html?region=${encodeURIComponent(r.key)}">${escapeHtml(r.label)}</a></td>
                <td>${r.parsed_count ?? "—"}</td>
                <td>${r.avg_rating ?? "—"}</td>
                <td>${r.median_rating ?? "—"}</td>
                <td>${r.rating_std ?? "—"}</td>
                <td>${r.skewness ?? "—"}</td>
                <td>${r.five_star_rate ?? "—"}%</td>
                <td>${r.five_star_ci ? `${r.five_star_ci.low}–${r.five_star_ci.high}` : "—"}</td>
                <td>${r.suspicious_rate ?? "—"}%</td>
                <td>${r.price_correlation ?? "—"}</td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>
      </div>
      <p class="section-note">CI=95%信頼区間（Wilson法）· σ=標準偏差 · r=料金と評価のピアソン相関</p>
    </section>`;
}

function renderReviewInsights(reviewInsights, reviewMeta, regionLabel) {
  const ri = reviewInsights || {};
  const total = ri.parsed_count || 0;
  return `
    <section class="panel review-panel">
      <h2>口コミ評価の分布</h2>
      <p class="section-note">
        ${escapeHtml(regionLabel)}の口コミ ${total} 件を解析
        ${reviewMeta?.review_total_official ? `（公式全体: ${reviewMeta.review_total_official.toLocaleString("ja-JP")}件）` : ""}
      </p>
      <div class="stat-banner">
        <div class="stat"><div class="label">平均 ± σ</div><div class="value">${ri.avg_rating ?? "—"} ± ${ri.rating_std ?? "—"}</div></div>
        <div class="stat"><div class="label">中央値</div><div class="value">${ri.median_rating ?? "—"}</div></div>
        <div class="stat"><div class="label">満点(5.0)比率</div><div class="value">${ri.five_star_rate ?? 0}%</div></div>
        <div class="stat"><div class="label">注意パターン</div><div class="value">${ri.suspicious_rate ?? 0}%</div></div>
      </div>
      ${renderRatingDistribution(ri.distribution, total)}
      ${(ri.trust_notes || []).length ? `<div class="trust-notes">${ri.trust_notes.map((n) => `<p>⚠ ${escapeHtml(n)}</p>`).join("")}</div>` : ""}
    </section>

    ${renderStatisticsBlock(ri.statistics)}

    <section class="grid-2">
      <div class="panel">
        <h2>口コミキーワード TOP</h2>
        ${Object.entries(ri.top_keywords || {})
          .map(([k, v]) => `<p><span class="tag">${escapeHtml(k)}</span> ${v}件</p>`)
          .join("") || "<p class='muted'>なし</p>"}
      </div>
      <div class="panel">
        <h2>利用回数の内訳</h2>
        ${Object.entries(ri.visit_types || {})
          .map(([k, v]) => {
            const labels = { first: "初めて", repeat: "2〜4回", loyal: "5回以上", unknown: "不明" };
            return `<p>${escapeHtml(labels[k] || k)} — ${v}件</p>`;
          })
          .join("") || "<p class='muted'>なし</p>"}
      </div>
    </section>

    <section class="panel">
      <h2>⚠ 注意パターンに該当する口コミ</h2>
      <p class="section-note">
        割安・コスパ訴求と満点の組み合わせ、料金との不一致、短文満点などを自動検出しています。
        参考情報であり、口コミの真偽を断定するものではありません。
      </p>
      ${renderFlaggedReviews(ri.flagged_reviews)}
    </section>`;
}
