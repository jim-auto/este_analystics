async function initReviews() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const root = document.getElementById("reviews-root");

  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === region);
  });

  try {
    const data = await loadJson(`${region}.json`);
    root.innerHTML = `
      <section class="area-header">
        <p class="eyebrow">口コミ解析</p>
        <h1>${escapeHtml(data.region_label)}エリアの口コミ評価</h1>
        <p class="lead">
          エステ魂の口コミを評価分布・キーワード・注意パターンで再整理。
          「割安」「コスパ」と満点がセットの口コミなど、客目線で確認したい信号を可視化します。
        </p>
        <div class="meta-row">
          <a href="${escapeHtml(data.source_urls.reviews)}" target="_blank" rel="noopener">公式口コミ一覧</a>
          <a href="area.html?region=${encodeURIComponent(region)}">エリア詳細へ</a>
        </div>
      </section>
      ${renderReviewInsights(data.insights.reviews, data.review_meta, data.region_label)}
      <section class="panel">
        <h2>注意パターンの見方</h2>
        <ul class="reason-guide">
          <li><span class="warn-badge">⚠ 割安訴求＋満点</span> — 「激安」「コスパ最強」などと星5がセット</li>
          <li><span class="warn-badge">⚠ 料金と割安表現の不一致</span> — 割安と書いてあるが店舗料金はエリア相場より高め</li>
          <li><span class="warn-badge">⚠ 短文満点</span> — 具体描写が少ない短い文章で満点</li>
          <li><span class="warn-badge">⚠ 初回短文満点</span> — 初利用なのに詳細なく満点</li>
        </ul>
        <p class="section-note">あくまで参考指標です。最終判断は複数の口コミと公式情報で行ってください。</p>
      </section>
    `;
    document.title = `口コミ解析 ${data.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initReviews();
