const state = {
  selectedStock: null,
  level: "daily",
  analysis: null,
  hoverIndex: null,
  viewStart: 0,
  visibleCount: 120,
  isDragging: false,
  dragStartX: 0,
  dragStartViewStart: 0,
};

const els = {
  stockInput: document.querySelector("#stockInput"),
  suggestions: document.querySelector("#suggestions"),
  statusText: document.querySelector("#statusText"),
  levelTabs: document.querySelector("#levelTabs"),
  startDate: document.querySelector("#startDate"),
  endDate: document.querySelector("#endDate"),
  refreshBtn: document.querySelector("#refreshBtn"),
  errorBox: document.querySelector("#errorBox"),
  canvas: document.querySelector("#chartCanvas"),
  tooltip: document.querySelector("#tooltip"),
  signalList: document.querySelector("#signalList"),
  metaStats: document.querySelector("#metaStats"),
  centerList: document.querySelector("#centerList"),
  divergenceList: document.querySelector("#divergenceList"),
};

let searchTimer = null;
const MIN_VISIBLE_BARS = 24;
const MAX_VISIBLE_BARS = 220;

function debounceSearch() {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(searchStocks, 220);
}

async function searchStocks() {
  const q = els.stockInput.value.trim();
  if (!q) {
    hideSuggestions();
    return;
  }

  try {
    const data = await fetchJson(`/api/stocks/search?q=${encodeURIComponent(q)}&limit=12`);
    renderSuggestions(data.items || []);
  } catch (err) {
    showError(err.message);
  }
}

function renderSuggestions(items) {
  if (!items.length) {
    els.suggestions.innerHTML = `<button type="button" disabled><span>无匹配</span><small>换个名称或代码试试</small></button>`;
    els.suggestions.hidden = false;
    return;
  }

  els.suggestions.innerHTML = items
    .map(
      (item) => `
        <button type="button" data-code="${item.ts_code}">
          <span>${item.symbol}</span>
          <span>${item.name}<small>${item.ts_code} · ${item.industry || "行业未知"}</small></span>
        </button>
      `
    )
    .join("");
  els.suggestions.hidden = false;
}

function hideSuggestions() {
  els.suggestions.hidden = true;
  els.suggestions.innerHTML = "";
}

async function loadAnalysis() {
  const query = state.selectedStock?.ts_code || els.stockInput.value.trim();
  if (!query) {
    showError("请输入股票名称或代码。");
    return;
  }

  const params = new URLSearchParams({
    ts_code: query,
    level: state.level,
  });
  if (els.startDate.value) params.set("start_date", els.startDate.value);
  if (els.endDate.value) params.set("end_date", els.endDate.value);

  setLoading(true);
  try {
    const data = await fetchJson(`/api/analysis?${params.toString()}`);
    state.analysis = data;
    state.selectedStock = data.stock;
    resetChartView();
    els.stockInput.value = `${data.stock.name} ${data.stock.symbol}`;
    els.statusText.textContent = `${data.stock.name} ${data.stock.ts_code} · ${levelLabel(state.level)} · ${data.query.start_date} 至 ${data.query.end_date}`;
    hideError();
    renderAll();
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error?.message || `请求失败：${response.status}`);
  }
  return data;
}

function setLoading(isLoading) {
  els.refreshBtn.disabled = isLoading;
  els.refreshBtn.textContent = isLoading ? "分析中" : "分析";
}

function showError(message) {
  els.errorBox.textContent = message;
  els.errorBox.hidden = false;
}

function hideError() {
  els.errorBox.hidden = true;
  els.errorBox.textContent = "";
}

function renderAll() {
  renderChart();
  renderSignals();
  renderStats();
  renderCenters();
  renderDivergences();
}

function renderSignals() {
  const signals = state.analysis?.signals || [];
  if (!signals.length) {
    els.signalList.className = "empty";
    els.signalList.textContent = "当前周期暂无买卖点候选。";
    return;
  }

  els.signalList.className = "";
  els.signalList.innerHTML = signals
    .slice(-8)
    .reverse()
    .map(
      (item) => `
        <article class="signalCard ${item.side}">
          <strong>
            <span class="side-${item.side}">${signalLabel(item)}</span>
            <span>${formatDate(item.date)} · ${formatPrice(item.price)}</span>
          </strong>
          <p>${item.reason}</p>
        </article>
      `
    )
    .join("");
}

function renderStats() {
  const meta = state.analysis?.meta;
  if (!meta) {
    els.metaStats.innerHTML = "";
    return;
  }
  const counts = meta.counts || {};
  const rows = [
    ["原始K线", meta.raw_count],
    ["包含处理后", meta.merged_count],
    ["分型", counts.fractals || 0],
    ["笔", counts.strokes || 0],
    ["中枢", counts.centers || 0],
    ["背驰", counts.divergences || 0],
    ["买卖点", counts.signals || 0],
    ["成笔跨度", `${meta.min_raw_bars_per_stroke}根`],
  ];
  els.metaStats.innerHTML = rows.map(([key, value]) => `<dt>${key}</dt><dd>${value}</dd>`).join("");
}

function renderCenters() {
  const centers = (state.analysis?.centers || []).slice(-6).reverse();
  if (!centers.length) {
    els.centerList.innerHTML = `<div class="empty">暂无中枢</div>`;
    return;
  }
  els.centerList.innerHTML = `
    <table>
      <thead><tr><th>区间</th><th>低</th><th>高</th></tr></thead>
      <tbody>
        ${centers
          .map(
            (item) => `
              <tr>
                <td>${formatDate(item.start_date)}-${formatDate(item.end_date)}</td>
                <td>${formatPrice(item.low)}</td>
                <td>${formatPrice(item.high)}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderDivergences() {
  const divergences = (state.analysis?.divergences || []).slice(-6).reverse();
  if (!divergences.length) {
    els.divergenceList.innerHTML = `<div class="empty">暂无背驰候选</div>`;
    return;
  }
  els.divergenceList.innerHTML = divergences
    .map(
      (item) => `
        <article class="divergenceCard ${item.side}">
          <strong>
            <span class="side-${item.side}">${item.label}</span>
            <span>${formatDate(item.date)}</span>
          </strong>
          <p>${item.reason}</p>
          <small>${item.position} · 力度 ${formatMacd(item.current_strength)} / ${formatMacd(item.previous_strength)}</small>
        </article>
      `
    )
    .join("");
}

function renderChart() {
  const analysis = state.analysis;
  const canvas = els.canvas;
  const ctx = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rect.width, rect.height);

  if (!analysis?.klines?.length) {
    drawEmpty(ctx, rect);
    return;
  }

  clampChartView();
  const klines = analysis.klines;
  const view = visibleWindow();
  const visibleKlines = klines.slice(view.start, view.end);
  const plots = chartPlots(rect);
  const plot = plots.main;
  const macdPlot = plots.macd;
  const visibleCenters = (analysis.centers || []).filter((item) => overlapsWindow(item.start_index, item.end_index, view));
  const visibleMacd = (analysis.indicators?.macd || []).slice(view.start, view.end);
  const visibleBbi = (analysis.indicators?.bbi || []).slice(view.start, view.end);
  const range = priceRange(visibleKlines, visibleCenters, visibleBbi);
  const x = (idx) => plot.left + ((idx - view.start + 0.5) / view.count) * plot.width;
  const y = (price) => plot.top + ((range.high - price) / (range.high - range.low)) * plot.height;
  const candleW = Math.max(4, Math.min(13, (plot.width / view.count) * 0.62));

  drawGrid(ctx, rect, plot, range, visibleKlines, x, false);
  drawCenters(ctx, visibleCenters, x, y, plot);
  drawCandles(ctx, visibleKlines, x, y, candleW);
  drawBbi(ctx, visibleBbi, x, y);
  drawStrokes(ctx, visibleItems(analysis.strokes || [], "start_index", "end_index", view), x, y, view);
  drawFractals(ctx, visibleItems(analysis.fractals || [], "raw_index", "raw_index", view), x, y);
  drawSignals(ctx, visibleSignals(analysis.signals || [], view), x, y, plot);
  drawMacd(ctx, rect, macdPlot, visibleMacd, visibleDivergences(analysis.divergences || [], view), x, candleW);

  if (state.hoverIndex !== null && state.hoverIndex >= view.start && state.hoverIndex < view.end) {
    drawHover(ctx, klines[state.hoverIndex], x, plots, rect);
  }
}

function drawEmpty(ctx, rect) {
  ctx.fillStyle = "#68737d";
  ctx.font = "14px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("等待股票分析结果", rect.width / 2, rect.height / 2);
}

function drawGrid(ctx, rect, plot, range, klines, x, showDates = true) {
  ctx.strokeStyle = "#e5eaee";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#68737d";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  for (let i = 0; i <= 4; i += 1) {
    const py = plot.top + (plot.height / 4) * i;
    const price = range.high - ((range.high - range.low) / 4) * i;
    ctx.beginPath();
    ctx.moveTo(plot.left, py);
    ctx.lineTo(rect.width - plot.right, py);
    ctx.stroke();
    ctx.fillText(formatPrice(price), plot.left - 8, py);
  }

  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  if (!showDates) return;
  drawDateTicks(ctx, klines, x, plot);
}

function chartPlots(rect) {
  const left = 62;
  const right = 22;
  const top = 24;
  const bottom = 36;
  const gap = 28;
  const usableHeight = Math.max(320, rect.height - top - bottom - gap);
  const macdHeight = Math.max(92, Math.min(150, usableHeight * 0.28));
  const mainHeight = Math.max(220, usableHeight - macdHeight);
  const width = rect.width - left - right;
  return {
    main: { left, right, top, bottom: rect.height - top - mainHeight, width, height: mainHeight },
    macd: {
      left,
      right,
      top: top + mainHeight + gap,
      bottom,
      width,
      height: Math.max(72, rect.height - (top + mainHeight + gap) - bottom),
    },
  };
}

function drawCenters(ctx, centers, x, y, plot) {
  centers.forEach((item) => {
    const left = Math.max(plot.left, x(Math.min(item.start_index, item.end_index)));
    const right = Math.min(plot.left + plot.width, x(Math.max(item.start_index, item.end_index)));
    const top = y(item.high);
    const bottom = y(item.low);
    if (right < plot.left || left > plot.left + plot.width) return;
    ctx.fillStyle = "rgba(168, 111, 0, 0.13)";
    ctx.strokeStyle = "rgba(168, 111, 0, 0.62)";
    ctx.fillRect(left, top, Math.max(right - left, 4), Math.max(bottom - top, 2));
    ctx.strokeRect(left, top, Math.max(right - left, 4), Math.max(bottom - top, 2));
  });
}

function drawCandles(ctx, klines, x, y, candleW) {
  klines.forEach((bar) => {
    const up = bar.close >= bar.open;
    const color = up ? "#c24136" : "#14845f";
    const px = x(bar.index);
    const openY = y(bar.open);
    const closeY = y(bar.close);
    const highY = y(bar.high);
    const lowY = y(bar.low);
    ctx.strokeStyle = color;
    ctx.fillStyle = up ? "rgba(194, 65, 54, 0.22)" : "rgba(20, 132, 95, 0.22)";
    ctx.beginPath();
    ctx.moveTo(px, highY);
    ctx.lineTo(px, lowY);
    ctx.stroke();
    const top = Math.min(openY, closeY);
    const height = Math.max(Math.abs(closeY - openY), 1);
    ctx.fillRect(px - candleW / 2, top, candleW, height);
    ctx.strokeRect(px - candleW / 2, top, candleW, height);
  });
}

function drawBbi(ctx, bbiRows, x, y) {
  const validRows = bbiRows.filter((item) => item.value !== null && Number.isFinite(Number(item.value)));
  if (validRows.length < 2) return;

  ctx.strokeStyle = "#7c3aed";
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  validRows.forEach((item, idx) => {
    const px = x(item.index);
    const py = y(item.value);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.lineWidth = 1;

  const last = validRows[validRows.length - 1];
  ctx.fillStyle = "#7c3aed";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText("BBI", x(last.index) + 6, y(last.value));
}

function drawMacd(ctx, rect, plot, macdRows, divergences, x, candleW) {
  if (!macdRows.length) return;
  const range = macdRange(macdRows);
  const y = (value) => plot.top + ((range.high - value) / (range.high - range.low)) * plot.height;
  const zeroY = y(0);

  ctx.strokeStyle = "#e5eaee";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(plot.left, plot.top);
  ctx.lineTo(rect.width - plot.right, plot.top);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(plot.left, zeroY);
  ctx.lineTo(rect.width - plot.right, zeroY);
  ctx.stroke();

  ctx.fillStyle = "#68737d";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  ctx.fillText(formatMacd(range.high), plot.left - 8, plot.top + 2);
  ctx.fillText("0", plot.left - 8, zeroY);
  ctx.fillText(formatMacd(range.low), plot.left - 8, plot.top + plot.height - 2);

  macdRows.forEach((item) => {
    const px = x(item.index);
    const top = y(Math.max(item.hist, 0));
    const bottom = y(Math.min(item.hist, 0));
    const width = Math.max(2, candleW * 0.76);
    ctx.fillStyle = item.hist >= 0 ? "rgba(194, 65, 54, 0.72)" : "rgba(20, 132, 95, 0.72)";
    ctx.fillRect(px - width / 2, top, width, Math.max(bottom - top, 1));
  });

  drawMacdLine(ctx, macdRows, x, y, "dif", "#256f92");
  drawMacdLine(ctx, macdRows, x, y, "dea", "#a86f00");
  drawMacdDivergences(ctx, divergences, macdRows, x, y, plot);

  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillStyle = "#68737d";
  ctx.fillText("MACD", plot.left + 6, plot.top + 6);
  ctx.fillStyle = "#256f92";
  ctx.fillText("DIF", plot.left + 48, plot.top + 6);
  ctx.fillStyle = "#a86f00";
  ctx.fillText("DEA", plot.left + 78, plot.top + 6);

  drawDateTicks(ctx, macdRows, x, plot);
}

function drawDateTicks(ctx, rows, x, plot) {
  if (!rows.length) return;
  ctx.fillStyle = "#68737d";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const steps = Math.min(6, rows.length);
  for (let i = 0; i < steps; i += 1) {
    const idx = Math.floor((rows.length - 1) * (i / Math.max(steps - 1, 1)));
    const item = rows[idx];
    const label = formatDate(item.date);
    const halfWidth = ctx.measureText(label).width / 2;
    const px = clamp(x(item.index), plot.left + halfWidth + 2, plot.left + plot.width - halfWidth - 2);
    ctx.fillText(label, px, plot.top + plot.height + 10);
  }
}

function drawMacdDivergences(ctx, divergences, macdRows, x, y, plot) {
  const rowsByIndex = new Map(macdRows.map((item) => [item.index, item]));
  divergences.forEach((item) => {
    const idx = divergenceIndex(item);
    const row = rowsByIndex.get(idx);
    if (!row) return;

    const label = divergenceLabel(item);
    const width = Math.max(56, label.length * 13 + 14);
    const height = 20;
    const px = x(idx);
    const baseY = y(row.hist);
    const tagX = Math.max(plot.left + 2, Math.min(px - width / 2, plot.left + plot.width - width - 2));
    const tagY = item.side === "buy"
      ? Math.min(baseY + 8, plot.top + plot.height - height - 2)
      : Math.max(baseY - height - 8, plot.top + 2);
    const color = item.side === "buy" ? "#14845f" : "#c24136";

    ctx.strokeStyle = color;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(px, plot.top);
    ctx.lineTo(px, plot.top + plot.height);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = color;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
    roundedRect(ctx, tagX, tagY, width, height, 4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#fff";
    ctx.font = "600 12px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, tagX + width / 2, tagY + height / 2 + 0.5);
  });
}

function drawMacdLine(ctx, rows, x, y, key, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  rows.forEach((item, idx) => {
    const px = x(item.index);
    const py = y(item[key]);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.lineWidth = 1;
}

function macdRange(rows) {
  const values = rows.flatMap((item) => [item.dif, item.dea, item.hist]);
  const maxAbs = Math.max(...values.map((value) => Math.abs(value)), 0.01);
  return { high: maxAbs * 1.18, low: -maxAbs * 1.18 };
}

function drawStrokes(ctx, strokes, x, y, view) {
  ctx.lineWidth = 2;
  strokes.forEach((item) => {
    if (!overlapsWindow(item.start_index, item.end_index, view)) return;
    ctx.strokeStyle = item.direction === "up" ? "#a9352d" : "#0f6f52";
    ctx.beginPath();
    ctx.moveTo(x(item.start_index), y(item.start_price));
    ctx.lineTo(x(item.end_index), y(item.end_price));
    ctx.stroke();
  });
  ctx.lineWidth = 1;
}

function drawFractals(ctx, fractals, x, y) {
  fractals.forEach((item) => {
    const px = x(item.raw_index);
    const py = y(item.price);
    ctx.fillStyle = item.type === "top" ? "#c24136" : "#14845f";
    ctx.beginPath();
    if (item.type === "top") {
      ctx.moveTo(px, py - 8);
      ctx.lineTo(px - 5, py - 1);
      ctx.lineTo(px + 5, py - 1);
    } else {
      ctx.moveTo(px, py + 8);
      ctx.lineTo(px - 5, py + 1);
      ctx.lineTo(px + 5, py + 1);
    }
    ctx.closePath();
    ctx.fill();
  });
}

function drawSignals(ctx, signals, x, y, plot) {
  signals.forEach((item) => {
    const px = x(signalIndex(item));
    const py = y(item.price);
    const buy = item.side === "buy";
    drawSignalTag(ctx, {
      x: px,
      y: py,
      label: signalLabel(item),
      buy,
      plot,
    });
  });
}

function drawSignalTag(ctx, { x, y, label, buy, plot }) {
  const width = 34;
  const height = 20;
  const pointer = 6;
  const gap = 7;
  const tagX = Math.max(plot.left + 2, Math.min(x - width / 2, plot.left + plot.width - width - 2));
  const idealY = buy ? y + gap + pointer : y - gap - pointer - height;
  const tagY = Math.max(plot.top + 2, Math.min(idealY, plot.top + plot.height - height - 2));
  const color = buy ? "#14845f" : "#c24136";

  ctx.fillStyle = color;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.85)";
  roundedRect(ctx, tagX, tagY, width, height, 4);
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  if (buy) {
    const baseY = tagY;
    ctx.moveTo(x, Math.min(y + 1, plot.top + plot.height));
    ctx.lineTo(Math.max(tagX + 8, x - 5), baseY);
    ctx.lineTo(Math.min(tagX + width - 8, x + 5), baseY);
  } else {
    const baseY = tagY + height;
    ctx.moveTo(x, Math.max(y - 1, plot.top));
    ctx.lineTo(Math.max(tagX + 8, x - 5), baseY);
    ctx.lineTo(Math.min(tagX + width - 8, x + 5), baseY);
  }
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#fff";
  ctx.font = "600 12px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, tagX + width / 2, tagY + height / 2 + 0.5);

  ctx.fillStyle = color;
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(x, y, 3.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth = 1;
}

function roundedRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function signalLabel(signal) {
  const type = signal.type || "";
  const side = signal.side === "sell" ? "卖" : "买";
  if (type.includes("三类")) return `${side}3`;
  if (type.includes("二类")) return `${side}2`;
  if (type.includes("一类")) return `${side}1`;
  const match = type.match(/([一二三])类/);
  if (match) {
    return `${side}${{ 一: "1", 二: "2", 三: "3" }[match[1]]}`;
  }
  return side;
}

function indexFromSignal(signal) {
  const strokes = state.analysis?.strokes || [];
  const stroke = strokes[signal.stroke_index];
  return stroke ? stroke.end_index : 0;
}

function signalIndex(signal) {
  return signal.stroke_index < 0 ? 0 : indexFromSignal(signal);
}

function divergenceIndex(divergence) {
  const strokes = state.analysis?.strokes || [];
  const stroke = strokes[divergence.stroke_index];
  return stroke ? stroke.end_index : 0;
}

function divergenceLabel(divergence) {
  if (divergence.label === "线段内背驰") return "线段背驰";
  return divergence.label || "背驰";
}

function drawHover(ctx, bar, x, plots, rect) {
  if (!bar) return;
  const px = x(bar.index);
  const bottom = plots.macd.top + plots.macd.height;
  ctx.strokeStyle = "rgba(32, 39, 45, 0.32)";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(px, plots.main.top);
  ctx.lineTo(px, bottom);
  ctx.stroke();
  ctx.setLineDash([]);
}

function priceRange(klines, centers, bbiRows = []) {
  const bbiValues = bbiRows
    .map((item) => item.value)
    .filter((value) => value !== null && Number.isFinite(Number(value)));
  const highs = klines.map((item) => item.high).concat(centers.map((item) => item.high), bbiValues);
  const lows = klines.map((item) => item.low).concat(centers.map((item) => item.low), bbiValues);
  const high = Math.max(...highs);
  const low = Math.min(...lows);
  const padding = Math.max((high - low) * 0.08, high * 0.005, 0.01);
  return { high: high + padding, low: low - padding };
}

function clamp(value, min, max) {
  if (max < min) return min;
  return Math.max(min, Math.min(value, max));
}

function resetChartView() {
  const total = state.analysis?.klines?.length || 0;
  state.visibleCount = Math.min(total || defaultVisibleCount(), defaultVisibleCount());
  state.viewStart = Math.max(0, total - state.visibleCount);
  state.hoverIndex = null;
}

function defaultVisibleCount() {
  if (state.level === "monthly") return 72;
  if (state.level === "weekly") return 104;
  return 120;
}

function clampChartView() {
  const total = state.analysis?.klines?.length || 0;
  if (!total) {
    state.viewStart = 0;
    state.visibleCount = defaultVisibleCount();
    return;
  }
  const maxVisible = Math.min(MAX_VISIBLE_BARS, total);
  const minVisible = Math.min(MIN_VISIBLE_BARS, total);
  state.visibleCount = Math.max(minVisible, Math.min(Math.round(state.visibleCount), maxVisible));
  state.viewStart = Math.max(0, Math.min(Math.round(state.viewStart), total - state.visibleCount));
}

function visibleWindow() {
  clampChartView();
  const total = state.analysis?.klines?.length || 0;
  const start = state.viewStart;
  const end = Math.min(total, start + state.visibleCount);
  return { start, end, count: Math.max(end - start, 1) };
}

function overlapsWindow(startIndex, endIndex, view) {
  const start = Math.min(startIndex, endIndex);
  const end = Math.max(startIndex, endIndex);
  return end >= view.start && start < view.end;
}

function visibleItems(items, startKey, endKey, view) {
  return items.filter((item) => overlapsWindow(item[startKey], item[endKey], view));
}

function visibleSignals(signals, view) {
  return signals.filter((item) => {
    const idx = signalIndex(item);
    return idx >= view.start && idx < view.end;
  });
}

function visibleDivergences(divergences, view) {
  return divergences.filter((item) => {
    const idx = divergenceIndex(item);
    return idx >= view.start && idx < view.end;
  });
}

function indexFromPointer(event) {
  const analysis = state.analysis;
  if (!analysis?.klines?.length) return null;
  const rect = els.canvas.getBoundingClientRect();
  const plotLeft = 62;
  const plotWidth = rect.width - 84;
  const relative = event.clientX - rect.left - plotLeft;
  const ratio = Math.max(0, Math.min(0.999999, relative / plotWidth));
  const view = visibleWindow();
  return Math.max(0, Math.min(analysis.klines.length - 1, view.start + Math.floor(ratio * view.count)));
}

function chartRegionFromPointer(event) {
  const rect = els.canvas.getBoundingClientRect();
  const plots = chartPlots(rect);
  const y = event.clientY - rect.top;
  if (y >= plots.main.top && y <= plots.main.top + plots.main.height) return "main";
  if (y >= plots.macd.top && y <= plots.macd.top + plots.macd.height) return "macd";
  return "gap";
}

function positionTooltip(event, width = 220) {
  const rect = els.canvas.getBoundingClientRect();
  els.tooltip.style.left = `${clamp(event.clientX - rect.left + 12, 8, rect.width - width)}px`;
  els.tooltip.style.top = `${clamp(event.clientY - rect.top - 20, 12, rect.height - 130)}px`;
}

function showMainTooltip(event, analysis, idx) {
  const bar = analysis.klines[idx];
  const macd = analysis.indicators?.macd?.[idx];
  const bbi = analysis.indicators?.bbi?.[idx];
  const divergences = (analysis.divergences || []).filter((item) => divergenceIndex(item) === idx);
  const divergenceText = divergences.length
    ? `<br>${divergences.map((item) => `${divergenceLabel(item)}：${item.reason}`).join("<br>")}`
    : "";

  els.tooltip.hidden = false;
  positionTooltip(event, 220);
  els.tooltip.innerHTML = `
    <strong>${formatDate(bar.date)}</strong><br>
    开 ${formatPrice(bar.open)} 高 ${formatPrice(bar.high)}<br>
    低 ${formatPrice(bar.low)} 收 ${formatPrice(bar.close)}<br>
    BBI ${bbi?.value !== null && bbi?.value !== undefined ? formatPrice(bbi.value) : "-"}<br>
    量 ${Math.round(bar.vol).toLocaleString()}<br>
    MACD ${macd ? formatMacd(macd.hist) : "-"} · DIF ${macd ? formatMacd(macd.dif) : "-"} · DEA ${macd ? formatMacd(macd.dea) : "-"}${divergenceText}
  `;
}

function showMacdTooltip(event, analysis) {
  const divergence = divergenceFromMacdPointer(event, analysis);
  if (!divergence) {
    els.tooltip.hidden = true;
    return;
  }
  const idx = divergenceIndex(divergence);
  const macd = analysis.indicators?.macd?.[idx];

  els.tooltip.hidden = false;
  positionTooltip(event, 220);
  els.tooltip.innerHTML = `
    <strong>${divergenceLabel(divergence)} · ${formatDate(divergence.date)}</strong><br>
    ${divergence.reason}<br>
    MACD ${macd ? formatMacd(macd.hist) : "-"} · DIF ${macd ? formatMacd(macd.dif) : "-"} · DEA ${macd ? formatMacd(macd.dea) : "-"}
  `;
}

function divergenceFromMacdPointer(event, analysis) {
  const rect = els.canvas.getBoundingClientRect();
  const plots = chartPlots(rect);
  const xPos = event.clientX - rect.left;
  const yPos = event.clientY - rect.top;
  if (yPos < plots.macd.top || yPos > plots.macd.top + plots.macd.height) return null;

  const view = visibleWindow();
  const x = (idx) => plots.macd.left + ((idx - view.start + 0.5) / view.count) * plots.macd.width;
  const hitRadius = Math.max(8, plots.macd.width / view.count);
  let best = null;
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const item of analysis.divergences || []) {
    const idx = divergenceIndex(item);
    if (idx < view.start || idx >= view.end) continue;
    const distance = Math.abs(x(idx) - xPos);
    if (distance <= hitRadius && distance < bestDistance) {
      best = item;
      bestDistance = distance;
    }
  }
  return best;
}

function panByPixels(deltaX) {
  const rect = els.canvas.getBoundingClientRect();
  const view = visibleWindow();
  const plotWidth = Math.max(rect.width - 84, 1);
  const barsDelta = Math.round((-deltaX / plotWidth) * view.count);
  state.viewStart = state.dragStartViewStart + barsDelta;
  clampChartView();
}

function zoomAtPointer(event) {
  const analysis = state.analysis;
  if (!analysis?.klines?.length) return;
  event.preventDefault();
  const rect = els.canvas.getBoundingClientRect();
  const plotLeft = 62;
  const plotWidth = rect.width - 84;
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left - plotLeft) / plotWidth));
  const view = visibleWindow();
  const anchorIndex = view.start + ratio * view.count;
  const scale = event.deltaY > 0 ? 1.16 : 0.86;
  const nextCount = Math.round(view.count * scale);
  state.visibleCount = nextCount;
  clampChartView();
  state.viewStart = Math.round(anchorIndex - ratio * state.visibleCount);
  clampChartView();
}

function levelLabel(level) {
  return { daily: "日线", weekly: "周线", monthly: "月线" }[level] || level;
}

function formatDate(value) {
  const text = String(value || "");
  if (text.length !== 8) return text;
  return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6)}`;
}

function formatPrice(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return num >= 100 ? num.toFixed(2) : num.toFixed(3).replace(/0$/, "");
}

function formatMacd(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return num.toFixed(3);
}

function bindEvents() {
  els.stockInput.addEventListener("input", () => {
    state.selectedStock = null;
    debounceSearch();
  });
  els.stockInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      hideSuggestions();
      state.selectedStock = null;
      loadAnalysis();
    }
  });

  els.suggestions.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-code]");
    if (!button) return;
    const code = button.dataset.code;
    const text = button.innerText.split("\n");
    state.selectedStock = { ts_code: code };
    els.stockInput.value = text[1] ? `${text[1].trim()} ${text[0].trim()}` : code;
    hideSuggestions();
    loadAnalysis();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".searchBox")) hideSuggestions();
  });

  els.levelTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-level]");
    if (!button) return;
    state.level = button.dataset.level;
    els.levelTabs.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item === button));
    if (state.analysis || state.selectedStock) loadAnalysis();
  });

  els.refreshBtn.addEventListener("click", loadAnalysis);

  els.canvas.addEventListener("pointerdown", (event) => {
    if (!state.analysis?.klines?.length) return;
    state.isDragging = true;
    state.dragStartX = event.clientX;
    state.dragStartViewStart = state.viewStart;
    els.canvas.classList.add("dragging");
    els.canvas.setPointerCapture(event.pointerId);
  });

  els.canvas.addEventListener("pointermove", (event) => {
    const analysis = state.analysis;
    if (!analysis?.klines?.length) return;
    if (state.isDragging) {
      panByPixels(event.clientX - state.dragStartX);
      state.hoverIndex = indexFromPointer(event);
      els.tooltip.hidden = true;
      renderChart();
      return;
    }

    const idx = indexFromPointer(event);
    if (idx === null) return;
    state.hoverIndex = idx;
    const region = chartRegionFromPointer(event);
    if (region === "main") {
      showMainTooltip(event, analysis, idx);
    } else if (region === "macd") {
      showMacdTooltip(event, analysis);
    } else {
      els.tooltip.hidden = true;
    }
    renderChart();
  });

  els.canvas.addEventListener("pointerup", (event) => {
    state.isDragging = false;
    els.canvas.classList.remove("dragging");
    if (els.canvas.hasPointerCapture(event.pointerId)) {
      els.canvas.releasePointerCapture(event.pointerId);
    }
  });

  els.canvas.addEventListener("pointercancel", (event) => {
    state.isDragging = false;
    els.canvas.classList.remove("dragging");
    if (els.canvas.hasPointerCapture(event.pointerId)) {
      els.canvas.releasePointerCapture(event.pointerId);
    }
  });

  els.canvas.addEventListener("mouseleave", () => {
    if (state.isDragging) return;
    state.hoverIndex = null;
    els.tooltip.hidden = true;
    renderChart();
  });

  els.canvas.addEventListener("wheel", zoomAtPointer, { passive: false });

  window.addEventListener("resize", renderChart);
}

bindEvents();
renderChart();
