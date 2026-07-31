const DATA_BASE = "data";

function yen(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return `¥${Number(value).toLocaleString("ja-JP")}`;
}

function trendLabel(trend) {
  if (trend === "up") return '<span class="trend-up">UP</span>';
  if (trend === "down") return '<span class="trend-down">DOWN</span>';
  return '<span class="trend-same">—</span>';
}

async function loadJson(path) {
  const res = await fetch(`${DATA_BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json();
}

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
