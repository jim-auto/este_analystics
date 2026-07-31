async function initSubarea() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const areaName = params.get("area");
  const root = document.getElementById("subarea-root");

  if (!areaName) {
    root.innerHTML = "<p class='error'>エリアが指定されていません</p>";
    return;
  }

  try {
    const data = await loadJson(`subareas_${region}.json`);
    const area = (data.areas || []).find((a) => a.name === areaName);
    root.innerHTML = renderSubareaDetail(area, region, data.region_label);
    document.title = `${areaName} ${data.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initSubarea();
