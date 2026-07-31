async function initSubareas() {
  const params = new URLSearchParams(location.search);
  const region = params.get("region") || "kanto";
  const root = document.getElementById("subareas-root");

  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === region);
  });

  try {
    const data = await loadJson(`subareas_${region}.json`);
    root.innerHTML = renderSubareaList(data.areas || [], region, data.region_label);
    document.title = `サブエリア ${data.region_label} | este_analystics`;
  } catch (err) {
    root.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

initSubareas();
