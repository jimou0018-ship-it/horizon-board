// 共用脚本
const Toast = {
  show(msg, type = "info", ms = 2000) {
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    if (type === "error") el.style.background = "rgba(240, 68, 56, .95)";
    if (type === "success") el.style.background = "rgba(18, 183, 106, .95)";
    document.body.appendChild(el);
    setTimeout(() => el.remove(), ms);
  },
};

async function api(path, options = {}) {
  const opts = {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "same-origin",
  };
  if (options.body !== undefined) {
    opts.body = typeof options.body === "string" ? options.body : JSON.stringify(options.body);
  }
  if (options.raw) {
    opts.headers = options.headers || {};
    delete opts.headers["Content-Type"];
    opts.body = options.body;
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    let msg = "请求失败";
    try { msg = (await res.json()).detail || msg; } catch (e) {}
    throw new Error(msg);
  }
  const ct = res.headers.get("Content-Type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

function fmtNum(v) {
  const n = Number(v);
  if (!isFinite(n) || n === 0) return "0";
  if (n >= 100000000) return (n / 100000000).toFixed(2).replace(/\.?0+$/, "") + "亿";
  if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.?0+$/, "") + "万";
  return n.toLocaleString();
}

function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function todayISO() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}
function yesterdayISO() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

function renderTopbar(active) {
  return `
  <div class="topbar">
    <div class="brand"><span class="dot"></span>Horizon Board</div>
    <div class="nav">
      <a href="/" class="${active === 'dashboard' ? 'active' : ''}">看板</a>
      <a href="/sheet" class="${active === 'sheet' ? 'active' : ''}">数据表</a>
    </div>
    <div class="spacer"></div>
  </div>`;
}

function bindTopbar() {
  // 无登录版：保留为空函数，便于将来扩展
}
