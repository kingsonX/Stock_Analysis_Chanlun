const state = {
  selectedStock: null,
  level: "daily",
  currentPage: "analysisPage",
  analysis: null,
  mxSummary: null,
  mxRequestId: 0,
  hoverIndex: null,
  viewStart: 0,
  visibleCount: 120,
  showStrokes: true,
  showSegments: true,
  replayEnabled: false,
  replayIndex: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartViewStart: 0,
  smartPicker: {
    overview: null,
    screen: null,
    detail: null,
    watchlist: null,
    ai: null,
    selectedTsCode: "",
    overviewRequestId: 0,
    screenRequestId: 0,
    detailRequestId: 0,
    watchlistRequestId: 0,
    aiRequestId: 0,
    focusReadyOnly: false,
    structureFilter: "all",
    emotionFilter: "all",
    overallFilter: "all",
    sortBy: "overall_score",
    sortDirection: "desc",
    loaded: false,
  },
};

const els = {
  mainMenu: document.querySelector("#mainMenu"),
  stockInput: document.querySelector("#stockInput"),
  suggestions: document.querySelector("#suggestions"),
  statusText: document.querySelector("#statusText"),
  levelTabs: document.querySelector("#levelTabs"),
  startDate: document.querySelector("#startDate"),
  endDate: document.querySelector("#endDate"),
  showStrokes: document.querySelector("#showStrokes"),
  showSegments: document.querySelector("#showSegments"),
  replayToggle: document.querySelector("#replayToggle"),
  replaySlider: document.querySelector("#replaySlider"),
  replayLabel: document.querySelector("#replayLabel"),
  refreshBtn: document.querySelector("#refreshBtn"),
  errorBox: document.querySelector("#errorBox"),
  canvas: document.querySelector("#chartCanvas"),
  tooltip: document.querySelector("#tooltip"),
  sideTabs: document.querySelector("#sideTabs"),
  levelContext: document.querySelector("#levelContext"),
  structureDetail: document.querySelector("#structureDetail"),
  riskList: document.querySelector("#riskList"),
  backtestBox: document.querySelector("#backtestBox"),
  metaStats: document.querySelector("#metaStats"),
  centerList: document.querySelector("#centerList"),
  mxDataBox: document.querySelector("#mxDataBox"),
  pages: document.querySelectorAll(".appPage"),
  pickerStatusText: document.querySelector("#pickerStatusText"),
  pickerOverviewBtn: document.querySelector("#pickerOverviewBtn"),
  pickerWatchlistBtn: document.querySelector("#pickerWatchlistBtn"),
  pickerQueryInput: document.querySelector("#pickerQueryInput"),
  pickerLevel: document.querySelector("#pickerLevel"),
  pickerLimit: document.querySelector("#pickerLimit"),
  pickerRunBtn: document.querySelector("#pickerRunBtn"),
  pickerStructureFilter: document.querySelector("#pickerStructureFilter"),
  pickerEmotionFilter: document.querySelector("#pickerEmotionFilter"),
  pickerOverallFilter: document.querySelector("#pickerOverallFilter"),
  pickerSortBy: document.querySelector("#pickerSortBy"),
  pickerSortDirection: document.querySelector("#pickerSortDirection"),
  pickerFocusReadyBtn: document.querySelector("#pickerFocusReadyBtn"),
  pickerClearFiltersBtn: document.querySelector("#pickerClearFiltersBtn"),
  pickerErrorBox: document.querySelector("#pickerErrorBox"),
  pickerSideTabs: document.querySelector("#pickerSideTabs"),
  pickerMarketBox: document.querySelector("#pickerMarketBox"),
  pickerNewsBox: document.querySelector("#pickerNewsBox"),
  pickerWatchlistBox: document.querySelector("#pickerWatchlistBox"),
  pickerTableBox: document.querySelector("#pickerTableBox"),
  pickerTableStatus: document.querySelector("#pickerTableStatus"),
  pickerResultMeta: document.querySelector("#pickerResultMeta"),
  pickerDetailBox: document.querySelector("#pickerDetailBox"),
};

let searchTimer = null;
let chartRenderFrame = null;
const MIN_VISIBLE_BARS = 12;
const MAX_VISIBLE_BARS = 420;
const WHEEL_ZOOM_SPEED = 0.0028;

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
  state.mxRequestId += 1;
  state.mxSummary = null;
  try {
    const data = await fetchJson(`/api/analysis?${params.toString()}`);
    state.analysis = data;
    state.selectedStock = data.stock;
    resetChartView();
    els.stockInput.value = `${data.stock.name} ${data.stock.symbol}`;
    els.statusText.textContent = `${data.stock.name} ${data.stock.ts_code} · ${levelLabel(state.level)} · ${formatDate(data.query.start_date)} 至 ${formatDate(data.query.end_date)}`;
    hideError();
    renderAll();
    loadMxSummary(data.stock);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error?.message || `请求失败：${response.status}`);
  }
  return data;
}

async function loadMxSummary(stock) {
  if (!stock) return;
  const requestId = ++state.mxRequestId;
  state.mxSummary = { status: "loading" };
  renderMxData();

  try {
    const data = await fetchJson("/api/trading-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        stock,
        analysis: state.analysis,
      }),
    });
    if (requestId !== state.mxRequestId) return;
    state.mxSummary = { status: "ok", data };
  } catch (err) {
    if (requestId !== state.mxRequestId) return;
    state.mxSummary = { status: "error", message: err.message };
  }
  renderMxData();
}

function setLoading(isLoading) {
  els.refreshBtn.disabled = isLoading;
  els.refreshBtn.textContent = isLoading ? "分析中" : "分析";
}

function switchMainPage(targetId) {
  state.currentPage = targetId;
  els.mainMenu?.querySelectorAll("button[data-page]").forEach((item) => {
    item.classList.toggle("active", item.dataset.page === targetId);
  });
  els.pages.forEach((page) => {
    page.classList.toggle("active", page.id === targetId);
  });
  if (targetId === "analysisPage") {
    window.setTimeout(() => {
      scheduleChartRender();
    }, 0);
    return;
  }

  if (targetId === "smartPickerPage") {
    ensureSmartPickerLoaded();
  }
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
  updateReplayControls();
  renderChart();
  renderLevelContext();
  renderStructureDetail();
  renderRiskCards();
  renderBacktest();
  renderStats();
  renderCenters();
  renderMxData();
}

function renderLevelContext() {
  const items = state.analysis?.level_context?.items || [];
  if (!items.length) {
    els.levelContext.className = "empty";
    els.levelContext.textContent = "暂无级别结构";
    return;
  }

  els.levelContext.className = "levelStack";
  els.levelContext.innerHTML = items
    .map((item) => {
      if (item.status === "error") {
        return `
          <article class="levelCard error">
            <strong>${item.label || item.level}</strong>
            <p>${item.error || "级别数据获取失败"}</p>
          </article>
        `;
      }

      const trend = item.trend || {};
      const signal = item.last_signal;
      const center = item.last_center;
      return `
        <article class="levelCard ${item.level === state.level ? "active" : ""}">
          <strong>
            <span>${item.label}</span>
            <span>${trend.label || "结构不足"}</span>
          </strong>
          <p>${trend.position_label || "无位次"} · ${trend.active_center_status || "无中枢"}</p>
          <small>${center ? `${center.id} ${formatDate(center.end_date)} · ${center.status_label}` : "无中枢"}${signal ? ` · ${signalLabel(signal)} ${signal.status_label}` : ""}</small>
        </article>
      `;
    })
    .join("");
}

function renderStructureDetail() {
  const trend = state.analysis?.trend;
  if (!trend) {
    els.structureDetail.className = "empty";
    els.structureDetail.textContent = "暂无走势结构";
    return;
  }

  const segments = replayItemsByEnd(state.analysis?.segments || [], "end_index");
  const lastSegment = segments[segments.length - 1];
  els.structureDetail.className = "structureBox";
  els.structureDetail.innerHTML = `
    <div class="structureHeadline">
      <strong>${trend.label || "结构不足"}</strong>
      <span>${trend.position_label || "无位次"}</span>
    </div>
    <p>${trend.reason || ""}</p>
    <dl class="miniStats">
      <dt>当前线段</dt><dd>${lastSegment ? `${lastSegment.id} · ${lastSegment.status_label}` : "无"}</dd>
      <dt>线段方向</dt><dd>${lastSegment ? directionLabel(lastSegment.direction) : "-"}</dd>
      <dt>中枢状态</dt><dd>${trend.active_center_status || "无中枢"}</dd>
      <dt>最后收盘</dt><dd>${trend.last_close !== null && trend.last_close !== undefined ? formatPrice(trend.last_close) : "-"}</dd>
    </dl>
  `;
}

function renderRiskCards() {
  const cards = state.analysis?.risk_cards || [];
  const visibleSignalIds = new Set(replayFilteredSignals(state.analysis?.signals || []).map((item) => item.id));
  const visibleCards = cards.filter((item) => !state.replayEnabled || visibleSignalIds.has(item.signal_id));
  if (!visibleCards.length) {
    els.riskList.className = "empty";
    els.riskList.textContent = "暂无风险卡";
    return;
  }

  els.riskList.className = "";
  els.riskList.innerHTML = visibleCards
    .slice(-6)
    .reverse()
    .map(
      (item) => `
        <article class="riskCard ${item.side}">
          <strong>
            <span class="side-${item.side}">${item.label}</span>
            <span>${formatPct(item.risk_pct)}</span>
          </strong>
          <dl class="miniStats">
            <dt>日期</dt><dd>${formatDate(item.date)}</dd>
            <dt>价格</dt><dd>${formatPrice(item.entry_price)}</dd>
            <dt>失效</dt><dd>${formatPrice(item.invalidation_price)}</dd>
            <dt>状态</dt><dd>${item.status_label || "-"}</dd>
          </dl>
          <p>${item.discipline || ""}</p>
        </article>
      `
    )
    .join("");
}

function renderBacktest() {
  const backtest = state.analysis?.backtest;
  if (!backtest) {
    els.backtestBox.className = "empty";
    els.backtestBox.textContent = "暂无复盘统计";
    return;
  }

  const visibleSignalIds = new Set(replayFilteredSignals(state.analysis?.signals || []).map((item) => item.id));
  const trades = (backtest.trades || []).filter((item) => !state.replayEnabled || visibleSignalIds.has(item.signal_id));
  const summary = summarizeTradesForReplay(backtest.summary || {}, trades);
  els.backtestBox.className = "backtestBox";
  els.backtestBox.innerHTML = `
    <dl class="miniStats">
      <dt>信号</dt><dd>${summary.signals}</dd>
      <dt>已观察</dt><dd>${summary.observed}</dd>
      <dt>平均顺向</dt><dd>${formatPct(summary.avg_favorable_pct)}</dd>
      <dt>平均逆向</dt><dd>${formatPct(summary.avg_adverse_pct)}</dd>
    </dl>
    <div class="tradeList">
      ${trades
        .slice(-5)
        .reverse()
        .map(
          (item) => `
            <div class="tradeRow ${item.side}">
              <span>${item.label} ${formatDate(item.date)}</span>
              <strong>${item.outcome}</strong>
              <small>顺 ${formatPct(item.max_favorable_pct)} / 逆 ${formatPct(item.max_adverse_pct)}</small>
            </div>
          `
        )
        .join("") || `<div class="empty">暂无可复盘信号</div>`}
    </div>
  `;
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
    ["线段", counts.segments || 0],
    ["中枢", counts.centers || 0],
    ["背驰", counts.divergences || 0],
    ["买卖点", counts.signals || 0],
    ["成笔跨度", `${meta.min_raw_bars_per_stroke}根`],
  ];
  els.metaStats.innerHTML = rows.map(([key, value]) => `<dt>${key}</dt><dd>${value}</dd>`).join("");
}

function renderCenters() {
  const centers = replayItemsByEnd(state.analysis?.centers || [], "end_index").slice(-6).reverse();
  if (!centers.length) {
    els.centerList.innerHTML = `<div class="empty">暂无中枢</div>`;
    return;
  }
  els.centerList.innerHTML = `
    <table>
      <thead><tr><th>区间</th><th>低</th><th>高</th><th>状态</th></tr></thead>
      <tbody>
        ${centers
          .map(
            (item) => `
              <tr>
                <td>${formatDate(item.start_date)}-${formatDate(item.end_date)}</td>
                <td>${formatPrice(item.low)}</td>
                <td>${formatPrice(item.high)}</td>
                <td>${item.status_label || "-"}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderMxData() {
  if (!els.mxDataBox) return;
  const summary = state.mxSummary;
  if (!state.analysis) {
    els.mxDataBox.className = "empty";
    els.mxDataBox.textContent = "分析完成后加载行情、资金、估值、财务和公司资料。";
    return;
  }

  if (!summary || summary.status === "loading") {
    els.mxDataBox.className = "mxStack";
    els.mxDataBox.innerHTML = ["综合画像", "市场扫描", "资讯催化", "行情", "资金", "估值"]
      .map(
        (label) => `
          <article class="mxCard loading">
            <div class="mxCardHeader">
              <strong>${label}</strong>
              <small>加载中</small>
            </div>
            <div class="mxSkeleton"></div>
            <div class="mxSkeleton short"></div>
          </article>
        `
      )
      .join("");
    return;
  }

  if (summary.status === "error") {
    els.mxDataBox.className = "mxError";
    els.mxDataBox.textContent = summary.message || "妙想数据加载失败。";
    return;
  }

  els.mxDataBox.className = "mxStack";
  els.mxDataBox.innerHTML = [
    renderProfileCard(summary.data?.profile),
    renderMarketScan(summary.data?.market_scan),
    renderNewsDigest(summary.data?.news),
    ...((summary.data?.mx_summary?.data?.cards || []).map(renderMxCard)),
  ]
    .filter(Boolean)
    .join("");
}

function renderMxCard(card) {
  const statusText = card.status === "ok" ? "已更新" : card.status === "empty" ? "无数据" : "失败";
  const body = card.status === "ok" ? renderMxTable(card) : `<p class="mxCardMessage">${escapeHtml(card.error || "暂无有效数据。")}</p>`;
  const title = card.title || card.query_text || card.label;
  const entity = (card.entities || [])
    .map((item) => `${item.name || ""}${item.code ? ` ${item.code}` : ""}`.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(" · ");

  return `
    <article class="mxCard status-${escapeHtml(card.status || "empty")}">
      <div class="mxCardHeader">
        <strong>${escapeHtml(card.label || "数据")}</strong>
        <small>${escapeHtml(statusText)}</small>
      </div>
      <p class="mxCardTitle">${escapeHtml(title)}</p>
      ${entity ? `<p class="mxEntity">${escapeHtml(entity)}</p>` : ""}
      ${body}
    </article>
  `;
}

function renderProfileCard(profile) {
  if (!profile) return "";
  const sections = [profile.structure, profile.emotion, profile.capacity, profile.risk]
    .filter(Boolean)
    .map(
      (item) => `
        <div class="profileBlock tone-${escapeHtml(item.tone || "neutral")}">
          <div class="profileBlockHeader">
            <strong>${escapeHtml(item.title || "")}</strong>
            ${item.verdict ? `<span class="profileVerdict tone-${escapeHtml(item.tone || "neutral")}">${escapeHtml(item.verdict)}</span>` : ""}
          </div>
          ${item.summary ? `<p class="profileSummary">${escapeHtml(item.summary)}</p>` : ""}
          ${item.action ? `<p class="profileAction">${escapeHtml(item.action)}</p>` : ""}
          ${item.detail ? `<small>${escapeHtml(item.detail)}</small>` : ""}
          ${Array.isArray(item.basis) && item.basis.length ? `
            <div class="profileList">
              <span>判断依据</span>
              <ul>${item.basis.map((basis) => `<li>${escapeHtml(basis)}</li>`).join("")}</ul>
            </div>
          ` : ""}
          ${Array.isArray(item.conditions) && item.conditions.length ? `
            <div class="profileList">
              <span>观察条件</span>
              <ul>${item.conditions.map((condition) => `<li>${escapeHtml(condition)}</li>`).join("")}</ul>
            </div>
          ` : ""}
        </div>
      `
    )
    .join("");

  return `
    <article class="profileCard stance-${escapeHtml(profile.stance || "neutral")}">
      <div class="profileHero">
        <div>
          <span class="profileEyebrow">综合交易画像</span>
          <h3>${escapeHtml(profile.stance_label || "先观察")}</h3>
        </div>
        <div class="profileTags">
          ${(profile.tags || []).slice(0, 4).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
        </div>
      </div>
      <p class="profileHeadline">${escapeHtml(profile.headline || "")}</p>
      ${profile.decision ? `<p class="profileDecisionLine">${escapeHtml(profile.decision)}</p>` : ""}
      <p class="profileConclusion">${escapeHtml(profile.conclusion || "")}</p>
      <div class="profileGrid">${sections}</div>
    </article>
  `;
}

function renderMarketScan(scan) {
  if (!scan) return "";
  if (scan.status === "error") {
    return `<article class="mxCard status-error"><div class="mxCardHeader"><strong>市场扫描</strong><small>失败</small></div><p class="mxCardMessage">${escapeHtml(scan.message || "市场扫描加载失败。")}</p></article>`;
  }

  const cards = scan.cards || [];
  const body = cards.length
    ? cards
        .map(
          (card) => `
            <div class="scanCard ${escapeHtml(card.status || "empty")}">
              <strong>${escapeHtml(card.label || "扫描")}</strong>
              <span>${card.status === "ok" ? `${escapeHtml(String(card.total || 0))} 只` : escapeHtml(card.status === "empty" ? "无结果" : "失败")}</span>
              <p>${escapeHtml(card.description || card.query_text || card.error || "")}</p>
              ${card.hit_current_stock ? `<small>当前股票出现在该扫描结果中</small>` : ""}
            </div>
          `
        )
        .join("")
    : `<p class="mxCardMessage">暂无市场扫描结果。</p>`;

  return `
    <article class="mxCard status-ok">
      <div class="mxCardHeader">
        <strong>市场扫描</strong>
        <small>${escapeHtml(scan.industry || "全市场")}</small>
      </div>
      <div class="scanGrid">${body}</div>
    </article>
  `;
}

function renderNewsDigest(news) {
  if (!news) return "";
  if (news.status === "error") {
    return `<article class="mxCard status-error"><div class="mxCardHeader"><strong>资讯催化</strong><small>失败</small></div><p class="mxCardMessage">${escapeHtml(news.message || "资讯加载失败。")}</p></article>`;
  }

  const items = news.items || [];
  return `
    <article class="mxCard status-${items.length ? "ok" : "empty"}">
      <div class="mxCardHeader">
        <strong>资讯催化</strong>
        <small>${items.length ? `最近 ${items.length} 条` : "暂无"}</small>
      </div>
      ${
        items.length
          ? `<div class="newsList">
              ${items
                .map(
                  (item) => `
                    <article class="newsItem">
                      <strong>${escapeHtml(item.title || "")}</strong>
                      <span>${escapeHtml([item.type, formatDate(item.date), item.source].filter(Boolean).join(" · "))}</span>
                      <p>${escapeHtml(item.summary || "")}</p>
                    </article>
                  `
                )
                .join("")}
            </div>`
          : `<p class="mxCardMessage">未检索到近期公告、研报或机构观点。</p>`
      }
    </article>
  `;
}

function renderMxTable(card) {
  const columns = (card.columns || []).slice(0, 5);
  const rows = (card.rows || []).slice(0, 6);
  if (!columns.length || !rows.length) {
    return `<p class="mxCardMessage">MX 返回为空表。</p>`;
  }
  return `
    <div class="mxTableWrap">
      <table class="mxTable">
        <thead>
          <tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  ${columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function ensureSmartPickerLoaded() {
  if (state.smartPicker.loaded) return;
  state.smartPicker.loaded = true;
  syncPickerFiltersFromControls();
  loadPickerOverview();
  loadPickerWatchlist();
}

function syncPickerFiltersFromControls() {
  state.smartPicker.structureFilter = els.pickerStructureFilter?.value || "all";
  state.smartPicker.emotionFilter = els.pickerEmotionFilter?.value || "all";
  state.smartPicker.overallFilter = els.pickerOverallFilter?.value || "all";
  state.smartPicker.sortBy = els.pickerSortBy?.value || "overall_score";
  state.smartPicker.sortDirection = els.pickerSortDirection?.value || "desc";
}

async function loadPickerOverview() {
  const requestId = ++state.smartPicker.overviewRequestId;
  state.smartPicker.overview = { status: "loading" };
  renderPickerOverview();
  renderPickerNews();
  setPickerStatus("正在刷新市场环境和催化摘要...");
  hidePickerError();

  try {
    const data = await fetchJson("/api/smart-picker/overview");
    if (requestId !== state.smartPicker.overviewRequestId) return;
    state.smartPicker.overview = data;
    setPickerStatus(data.stage?.action || "市场环境已更新，可以继续筛候选股。");
  } catch (err) {
    if (requestId !== state.smartPicker.overviewRequestId) return;
    state.smartPicker.overview = { status: "error", message: err.message };
    showPickerError(err.message);
  }

  renderPickerOverview();
  renderPickerNews();
}

async function loadPickerWatchlist() {
  const requestId = ++state.smartPicker.watchlistRequestId;
  state.smartPicker.watchlist = { status: "loading" };
  renderPickerWatchlist();
  hidePickerError();

  try {
    const data = await fetchJson("/api/smart-picker/watchlist");
    if (requestId !== state.smartPicker.watchlistRequestId) return;
    state.smartPicker.watchlist = data;
  } catch (err) {
    if (requestId !== state.smartPicker.watchlistRequestId) return;
    state.smartPicker.watchlist = { status: "error", message: err.message, items: [] };
    showPickerError(err.message);
  }

  renderPickerWatchlist();
  renderPickerDetail();
}

async function runSmartPicker() {
  const queryText = els.pickerQueryInput?.value.trim() || "";
  if (!queryText) {
    showPickerError("请输入智能选股条件。");
    return;
  }

  syncPickerFiltersFromControls();
  const requestId = ++state.smartPicker.screenRequestId;
  state.smartPicker.screen = { status: "loading" };
  state.smartPicker.detail = null;
  state.smartPicker.ai = null;
  state.smartPicker.selectedTsCode = "";
  renderPickerTable();
  renderPickerDetail();
  hidePickerError();
  setPickerStatus("正在根据条件筛选股票，并结合缠论结构生成候选池...");

  try {
    const data = await fetchJson("/api/smart-picker/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_text: queryText,
        level: els.pickerLevel?.value || "daily",
        limit: Number(els.pickerLimit?.value || 20),
      }),
    });
    if (requestId !== state.smartPicker.screenRequestId) return;
    state.smartPicker.screen = data;
    const count = (data.candidates || []).length;
    const marketTotal = data.universe?.total ? `全市场 ${data.universe.total} 只股票里` : "全市场里";
    setPickerStatus(count ? `已从 ${marketTotal} 生成 ${count} 只结构候选，先按排序和筛选缩小观察范围。` : "筛选已完成，但当前条件下没有生成可用候选。");
  } catch (err) {
    if (requestId !== state.smartPicker.screenRequestId) return;
    state.smartPicker.screen = { status: "error", message: err.message };
    showPickerError(err.message);
  }

  renderPickerTable();
}

async function loadPickerCandidateDetail(stock) {
  if (!stock) return;
  const requestId = ++state.smartPicker.detailRequestId;
  state.smartPicker.selectedTsCode = stock.ts_code || stock.symbol || stock.name || "";
  state.smartPicker.detail = { status: "loading", stock };
  state.smartPicker.ai = null;
  renderPickerTable();
  renderPickerDetail();
  hidePickerError();

  try {
    const data = await fetchJson("/api/smart-picker/candidate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        stock,
        level: els.pickerLevel?.value || "daily",
      }),
    });
    if (requestId !== state.smartPicker.detailRequestId) return;
    state.smartPicker.detail = data;
  } catch (err) {
    if (requestId !== state.smartPicker.detailRequestId) return;
    state.smartPicker.detail = { status: "error", message: err.message, stock };
    showPickerError(err.message);
  }

  renderPickerTable();
  renderPickerDetail();
}

async function loadPickerAiBrief() {
  const detail = state.smartPicker.detail;
  if (!detail || detail.status !== "ok") return;
  const requestId = ++state.smartPicker.aiRequestId;
  state.smartPicker.ai = { status: "loading" };
  renderPickerDetail();
  hidePickerError();

  try {
    const data = await fetchJson("/api/smart-picker/ai-brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        stock: detail.stock,
        analysis: detail.analysis,
        profile: detail.profile,
      }),
    });
    if (requestId !== state.smartPicker.aiRequestId) return;
    state.smartPicker.ai = data;
  } catch (err) {
    if (requestId !== state.smartPicker.aiRequestId) return;
    state.smartPicker.ai = { status: "error", message: err.message };
  }

  renderPickerDetail();
}

async function managePickerWatchlist(action, target) {
  if (!target) return;
  hidePickerError();
  try {
    await fetchJson("/api/smart-picker/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, target }),
    });
    await loadPickerWatchlist();
    if (state.smartPicker.detail?.stock) {
      await loadPickerCandidateDetail(state.smartPicker.detail.stock);
    }
  } catch (err) {
    showPickerError(err.message);
  }
}

function openCandidateInAnalysis(stock) {
  if (!stock) return;
  state.selectedStock = { ts_code: stock.ts_code };
  els.stockInput.value = `${stock.name} ${stock.symbol}`;
  setAnalysisLevel(els.pickerLevel?.value || "daily");
  switchMainPage("analysisPage");
  loadAnalysis();
}

function setAnalysisLevel(level) {
  state.level = level;
  els.levelTabs?.querySelectorAll("button[data-level]").forEach((item) => {
    item.classList.toggle("active", item.dataset.level === level);
  });
}

function setPickerStatus(message) {
  if (els.pickerStatusText) {
    els.pickerStatusText.textContent = message;
  }
}

function showPickerError(message) {
  if (!els.pickerErrorBox) return;
  els.pickerErrorBox.textContent = message;
  els.pickerErrorBox.hidden = false;
}

function hidePickerError() {
  if (!els.pickerErrorBox) return;
  els.pickerErrorBox.hidden = true;
  els.pickerErrorBox.textContent = "";
}

function renderPickerOverview() {
  const overview = state.smartPicker.overview;
  if (!els.pickerMarketBox) return;

  if (!overview || overview.status === "loading") {
    els.pickerMarketBox.className = "pickerSummaryGrid";
    els.pickerMarketBox.innerHTML = `
      <article class="pickerSummaryCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="pickerSummaryCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
    `;
    return;
  }

  if (overview.status === "error") {
    els.pickerMarketBox.className = "mxError";
    els.pickerMarketBox.textContent = overview.message || "市场环境加载失败。";
    return;
  }

  const stage = overview.stage || {};
  const cards = overview.market_cards || [];
  const universe = overview.universe || {};
  els.pickerMarketBox.className = "pickerSummaryGrid";
  els.pickerMarketBox.innerHTML = `
    <article class="pickerStageCard tone-${escapeHtml(stage.tone || "neutral")}">
      <div class="profileBlockHeader">
        <strong>养家市场温度</strong>
        <span class="profileVerdict tone-${escapeHtml(stage.tone || "neutral")}">${escapeHtml(stage.label || "未判断")}</span>
      </div>
      <p class="profileSummary">${escapeHtml(stage.summary || "")}</p>
      <p class="profileAction">${escapeHtml(stage.action || "")}</p>
      ${
        Array.isArray(stage.basis) && stage.basis.length
          ? `<div class="profileList"><span>判断依据</span><ul>${stage.basis.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`
          : ""
      }
    </article>
    <article class="pickerSummaryCard">
      <div class="profileBlockHeader">
        <strong>${escapeHtml(universe.label || "全市场范围")}</strong>
        <span class="profileVerdict tone-neutral">${escapeHtml(universe.total ? `${universe.total} 只` : "待同步")}</span>
      </div>
      <p class="profileSummary">${escapeHtml(universe.summary || "智能选股条件默认以全 A 股为范围执行。")}</p>
    </article>
    <div class="pickerMiniCards">
      ${cards
        .map(
          (card) => `
            <article class="scanCard ${escapeHtml(card.status || "empty")}">
              <strong>${escapeHtml(card.label || "")}</strong>
              <span>${card.status === "ok" ? `${escapeHtml(String(card.total || 0))} 只` : escapeHtml(card.status === "empty" ? "无结果" : "失败")}</span>
              <p>${escapeHtml(card.description || card.query_text || card.error || "")}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderPickerNews() {
  const overview = state.smartPicker.overview;
  if (!els.pickerNewsBox) return;

  if (!overview || overview.status === "loading") {
    els.pickerNewsBox.className = "mxStack";
    els.pickerNewsBox.innerHTML = `
      <article class="mxCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
    `;
    return;
  }

  if (overview.status === "error") {
    els.pickerNewsBox.className = "mxError";
    els.pickerNewsBox.textContent = overview.message || "资讯催化加载失败。";
    return;
  }

  els.pickerNewsBox.className = "mxStack";
  els.pickerNewsBox.innerHTML = renderNewsDigest(overview.news);
}

function renderPickerWatchlist() {
  const watchlist = state.smartPicker.watchlist;
  if (!els.pickerWatchlistBox) return;

  if (!watchlist || watchlist.status === "loading") {
    els.pickerWatchlistBox.className = "mxStack";
    els.pickerWatchlistBox.innerHTML = `
      <article class="mxCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
    `;
    return;
  }

  if (watchlist.status === "error") {
    els.pickerWatchlistBox.className = "mxError";
    els.pickerWatchlistBox.textContent = watchlist.message || "自选同步失败。";
    return;
  }

  const items = watchlist.items || [];
  els.pickerWatchlistBox.className = "mxStack";
  els.pickerWatchlistBox.innerHTML = `
    <article class="mxCard status-${items.length ? "ok" : "empty"}">
      <div class="mxCardHeader">
        <strong>东方财富自选</strong>
        <small>${items.length ? `共 ${items.length} 只` : "空列表"}</small>
      </div>
      ${
        items.length
          ? `<div class="newsList">
              ${items
                .slice(0, 6)
                .map(
                  (item) => `
                    <article class="newsItem">
                      <strong>${escapeHtml(item.name || "")} ${escapeHtml(item.code || "")}</strong>
                      <span>${escapeHtml(
                        [item.latest_price ? `最新价 ${item.latest_price}` : "", item.change_pct ? `涨跌幅 ${item.change_pct}` : ""]
                          .filter(Boolean)
                          .join(" · ")
                      )}</span>
                      <p>${escapeHtml(
                        [item.turnover ? `换手率 ${item.turnover}` : "", item.volume_ratio ? `量比 ${item.volume_ratio}` : ""]
                          .filter(Boolean)
                          .join(" · ") || "已同步到本地观察页"
                      )}</p>
                    </article>
                  `
                )
                .join("")}
            </div>`
          : `<p class="mxCardMessage">当前没有自选股，可以从候选详情里一键加入。</p>`
      }
    </article>
  `;
}

function renderPickerTable() {
  const screen = state.smartPicker.screen;
  if (!els.pickerTableBox) return;

  if (!screen || screen.status === "loading") {
    els.pickerTableStatus.textContent = "正在生成候选池...";
    if (els.pickerResultMeta) {
      els.pickerResultMeta.textContent = "默认从全 A 股范围执行条件筛选。";
    }
    els.pickerTableBox.innerHTML = `
      <div class="pickerLoadingTable">
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton short"></div>
      </div>
    `;
    return;
  }

  if (screen.status === "error") {
    els.pickerTableStatus.textContent = "候选池加载失败。";
    if (els.pickerResultMeta) {
      els.pickerResultMeta.textContent = "候选池请求失败，请调整条件后重试。";
    }
    els.pickerTableBox.innerHTML = `<div class="mxError">${escapeHtml(screen.message || "智能选股失败。")}</div>`;
    return;
  }

  const rawCandidates = screen.candidates || [];
  const candidates = filterAndSortPickerCandidates(rawCandidates);
  const universe = screen.universe || {};
  const filterSummary = buildPickerFilterSummary(rawCandidates.length, candidates.length);
  els.pickerTableStatus.textContent = screen.description || screen.parser_text || `候选总数 ${screen.total || 0}`;
  if (els.pickerResultMeta) {
    els.pickerResultMeta.textContent = universe.total
      ? `全 A 股 ${universe.total} 只股票中，条件命中 ${screen.total || rawCandidates.length} 只；当前展示 ${candidates.length} 只。${filterSummary}`
      : `条件命中 ${screen.total || rawCandidates.length} 只；当前展示 ${candidates.length} 只。${filterSummary}`;
  }
  if (!candidates.length) {
    els.pickerTableBox.innerHTML = `<div class="empty">当前条件下没有筛出可用候选，可以放宽条件再试一次。</div>`;
    return;
  }

  els.pickerTableBox.innerHTML = `
    <table class="pickerTable">
      <thead>
        <tr>
          <th>股票</th>
          <th>缠论结构</th>
          <th>养家环境</th>
          <th>章盟主容量</th>
          <th>综合结论</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        ${candidates
          .map((item) => {
            const selected = state.smartPicker.selectedTsCode === item.stock.ts_code;
            return `
              <tr class="${selected ? "is-selected" : ""}">
                <td>
                  <div class="pickerStockCell">
                    <strong>${escapeHtml(item.stock.name)}</strong>
                    <small>${escapeHtml(item.stock.symbol)} · ${escapeHtml(item.stock.industry || "行业待定")}</small>
                    <small>${escapeHtml(
                      [item.quote.latest_price ? `最新价 ${item.quote.latest_price}` : "", item.quote.change_pct ? `涨跌幅 ${item.quote.change_pct}` : ""]
                        .filter(Boolean)
                        .join(" · ")
                    )}</small>
                  </div>
                </td>
                <td>
                  <span class="profileVerdict tone-${escapeHtml(item.structure.tone || "neutral")}">${escapeHtml(item.structure.label || "")}</span>
                  <p class="pickerCellText">${escapeHtml(item.structure.signal || item.structure.summary || "")}</p>
                </td>
                <td>
                  <span class="profileVerdict tone-${escapeHtml(item.emotion.tone || "neutral")}">${escapeHtml(item.emotion.label || "")}</span>
                  <p class="pickerCellText">${escapeHtml(item.emotion.summary || "")}</p>
                </td>
                <td>
                  <span class="profileVerdict tone-${escapeHtml(item.capacity.tone || "neutral")}">${escapeHtml(item.capacity.label || "")}</span>
                  <p class="pickerCellText">${escapeHtml(item.capacity.summary || "")}</p>
                </td>
                <td>
                  <strong class="pickerOverall tone-${escapeHtml(item.overall.tone || "neutral")}">${escapeHtml(item.overall.label || "")}</strong>
                  <p class="pickerCellText">${escapeHtml(item.overall.decision || "")}</p>
                </td>
                <td>
                  <div class="pickerRowActions">
                    <button type="button" class="miniButton" data-picker-action="detail" data-ts-code="${escapeHtml(item.stock.ts_code)}">详情</button>
                    <button type="button" class="miniButton ghostButton" data-picker-action="analysis" data-ts-code="${escapeHtml(item.stock.ts_code)}">去分析</button>
                  </div>
                </td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    </table>
    ${
      screen.errors?.length
        ? `<div class="pickerHint">有 ${screen.errors.length} 条结果因股票匹配或数据缺失被跳过，当前优先展示可用候选。</div>`
        : ""
    }
  `;
}

function buildPickerFilterSummary(rawCount, visibleCount) {
  const parts = [];
  if (state.smartPicker.focusReadyOnly) {
    parts.push("已启用“结构可看 + 主流活跃”快捷筛选");
  }
  if (state.smartPicker.structureFilter !== "all") {
    parts.push(`结构=${state.smartPicker.structureFilter}`);
  }
  if (state.smartPicker.emotionFilter !== "all") {
    parts.push(`情绪=${state.smartPicker.emotionFilter}`);
  }
  if (state.smartPicker.overallFilter !== "all") {
    parts.push(`综合=${state.smartPicker.overallFilter}`);
  }
  parts.push(`排序=${pickerSortLabel(state.smartPicker.sortBy)}${state.smartPicker.sortDirection === "asc" ? "升序" : "降序"}`);
  if (visibleCount !== rawCount) {
    parts.unshift(`筛掉 ${rawCount - visibleCount} 只`);
  }
  return parts.length ? `（${parts.join("，")}）` : "";
}

function pickerSortLabel(sortBy) {
  const mapping = {
    overall_score: "综合分",
    structure_score: "结构分",
    change_pct: "涨跌幅",
    amount: "成交额",
    turnover: "换手率",
    name: "股票名称",
  };
  return mapping[sortBy] || "综合分";
}

function filterAndSortPickerCandidates(candidates) {
  let items = [...(candidates || [])];
  if (state.smartPicker.focusReadyOnly) {
    items = items.filter((item) => item.structure?.label === "结构可看" && item.emotion?.label === "主流活跃");
  }
  if (state.smartPicker.structureFilter !== "all") {
    items = items.filter((item) => item.structure?.label === state.smartPicker.structureFilter);
  }
  if (state.smartPicker.emotionFilter !== "all") {
    items = items.filter((item) => item.emotion?.label === state.smartPicker.emotionFilter);
  }
  if (state.smartPicker.overallFilter !== "all") {
    items = items.filter((item) => item.overall?.label === state.smartPicker.overallFilter);
  }

  const direction = state.smartPicker.sortDirection === "asc" ? 1 : -1;
  const sortBy = state.smartPicker.sortBy;
  items.sort((left, right) => comparePickerCandidate(left, right, sortBy) * direction);
  return items;
}

function comparePickerCandidate(left, right, sortBy) {
  if (sortBy === "name") {
    return String(left.stock?.name || "").localeCompare(String(right.stock?.name || ""), "zh-Hans-CN");
  }

  const valueOf = (item) => {
    switch (sortBy) {
      case "structure_score":
        return Number(item.structure?.score || 0);
      case "change_pct":
        return Number(item.quote?.change_pct_value || 0);
      case "amount":
        return Number(item.quote?.amount_value || 0);
      case "turnover":
        return Number(item.quote?.turnover_value || 0);
      case "overall_score":
      default:
        return Number(item.overall?.score || 0);
    }
  };

  return valueOf(left) - valueOf(right);
}

function renderPickerDetail() {
  const detail = state.smartPicker.detail;
  if (!els.pickerDetailBox) return;

  if (!detail) {
    els.pickerDetailBox.className = "empty";
    els.pickerDetailBox.textContent = "点击候选池中的股票，这里会展开三视角交易画像和自选操作。";
    return;
  }

  if (detail.status === "loading") {
    els.pickerDetailBox.className = "mxStack";
    els.pickerDetailBox.innerHTML = `
      <article class="mxCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="mxCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
    `;
    return;
  }

  if (detail.status === "error") {
    els.pickerDetailBox.className = "mxError";
    els.pickerDetailBox.textContent = detail.message || "候选详情加载失败。";
    return;
  }

  const stock = detail.stock || {};
  const profilePayload = detail.profile || {};
  const watchlist = detail.watchlist || {};
  const activeAction = watchlist.in_watchlist ? "delete" : "add";
  const activeLabel = watchlist.in_watchlist ? "移出自选" : "加入自选";
  const mxCards = (profilePayload.mx_summary?.data?.cards || []).slice(0, 3).map(renderMxCard).join("");
  const analysis = detail.analysis || {};
  const latestSignal = (analysis.signals || []).slice(-1)[0];
  const latestDivergence = (analysis.divergences || []).slice(-1)[0];
  const aiCard = renderPickerAiCard(state.smartPicker.ai);

  els.pickerDetailBox.className = "pickerDetailStack";
  els.pickerDetailBox.innerHTML = `
    <div class="pickerDetailHero">
      <div>
        <strong>${escapeHtml(stock.name || "")} ${escapeHtml(stock.symbol || "")}</strong>
        <p>${escapeHtml(stock.ts_code || "")} · ${escapeHtml(stock.industry || "行业待定")}</p>
      </div>
      <div class="pickerDetailActions">
        <button type="button" class="miniButton" data-picker-detail-action="ai">AI 研究解读</button>
        <button type="button" class="miniButton" data-picker-detail-action="${escapeHtml(activeAction)}" data-picker-target="${escapeHtml(stock.symbol || stock.name || "")}">${escapeHtml(activeLabel)}</button>
        <button type="button" class="miniButton ghostButton" data-picker-detail-action="analysis" data-ts-code="${escapeHtml(stock.ts_code || "")}">打开图表</button>
      </div>
    </div>
    ${renderProfileCard(profilePayload.profile)}
    ${aiCard}
    <article class="mxCard status-ok">
      <div class="mxCardHeader">
        <strong>结构摘要</strong>
        <small>${escapeHtml(analysis.trend?.label || "结构不足")}</small>
      </div>
      <p class="mxCardTitle">${escapeHtml(
        [analysis.trend?.position_label || "", latestSignal ? `${signalLabel(latestSignal)} ${latestSignal.status_label || ""}` : "", latestDivergence?.label || ""]
          .filter(Boolean)
          .join(" · ")
      )}</p>
      <p class="mxCardMessage">${escapeHtml(analysis.trend?.reason || "暂无补充结构说明。")}</p>
    </article>
    ${renderMarketScan(profilePayload.market_scan)}
    ${renderNewsDigest(profilePayload.news)}
    ${mxCards}
  `;
}

function renderPickerAiCard(ai) {
  if (!ai) {
    return `
      <article class="mxCard status-empty">
        <div class="mxCardHeader">
          <strong>AI 研究解读</strong>
          <small>未生成</small>
        </div>
        <p class="mxCardMessage">这里会把缠论、养家、章盟主三视角，改写成更像研究员写给交易员看的结论。点击上方“AI 研究解读”后生成。</p>
      </article>
    `;
  }

  if (ai.status === "loading") {
    return `
      <article class="mxCard loading">
        <div class="mxCardHeader">
          <strong>AI 研究解读</strong>
          <small>生成中</small>
        </div>
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton short"></div>
      </article>
    `;
  }

  if (ai.status === "error") {
    return `
      <article class="mxCard status-error">
        <div class="mxCardHeader">
          <strong>AI 研究解读</strong>
          <small>失败</small>
        </div>
        <p class="mxCardMessage">${escapeHtml(ai.message || "AI 解读生成失败。")}</p>
      </article>
    `;
  }

  const note = ai.analysis || {};
  return `
    <article class="mxCard status-ok aiResearchCard">
      <div class="mxCardHeader">
        <strong>AI 研究解读</strong>
        <small>${escapeHtml(ai.model || "")}</small>
      </div>
      <p class="mxCardTitle">${escapeHtml(note.summary || "")}</p>
      <p class="profileAction">${escapeHtml(note.buy_judgement || "")}</p>
      <div class="aiMetaRow">
        <span class="profileVerdict tone-neutral">${escapeHtml(note.overall_verdict || "候选观察")}</span>
        <span class="aiMetaText">置信度 ${escapeHtml(note.confidence || "中")}</span>
      </div>
      ${renderAiViewBlock("缠中说禅视角", note.chan_view)}
      ${renderAiViewBlock("炒股养家视角", note.yangjia_view)}
      ${renderAiViewBlock("章盟主视角", note.zhang_view)}
      ${renderAiListBlock("主要风险", note.risks)}
      ${renderAiListBlock("观察重点", note.watch_points)}
    </article>
  `;
}

function renderAiViewBlock(title, item) {
  if (!item) return "";
  return `
    <section class="aiViewBlock">
      <div class="profileBlockHeader">
        <strong>${escapeHtml(title)}</strong>
        <span class="profileVerdict tone-neutral">${escapeHtml(item.verdict || "先观察")}</span>
      </div>
      <p>${escapeHtml(item.reason || "")}</p>
      <p class="profileAction">${escapeHtml(item.buyable || "")}</p>
      ${renderAiListBlock("判断依据", item.basis)}
      ${renderAiListBlock("后续条件", item.conditions)}
    </section>
  `;
}

function renderAiListBlock(title, items) {
  if (!Array.isArray(items) || !items.length) return "";
  return `
    <div class="profileList">
      <span>${escapeHtml(title)}</span>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function renderDivergenceEvidence(item) {
  const evidence = item.evidence || {};
  if (!Object.keys(evidence).length) return "";
  return `
    <dl class="evidenceGrid">
      <dt>比较</dt><dd>${evidence.previous_stroke_id || "-"} / ${evidence.current_stroke_id || "-"}</dd>
      <dt>价格力度</dt><dd>${formatMacd(evidence.previous_price_strength)} / ${formatMacd(evidence.current_price_strength)}</dd>
      <dt>红柱面积</dt><dd>${formatMacd(evidence.previous_macd_red_area)} / ${formatMacd(evidence.current_macd_red_area)}</dd>
      <dt>绿柱面积</dt><dd>${formatMacd(evidence.previous_macd_green_area)} / ${formatMacd(evidence.current_macd_green_area)}</dd>
      <dt>DIF</dt><dd>${formatMacd(evidence.previous_dif_end)} / ${formatMacd(evidence.current_dif_end)}</dd>
      <dt>DEA</dt><dd>${formatMacd(evidence.previous_dea_end)} / ${formatMacd(evidence.current_dea_end)}</dd>
      <dt>零轴位置</dt><dd>${zeroLabel(evidence.previous_zero_position)} / ${zeroLabel(evidence.current_zero_position)}</dd>
      <dt>阈值</dt><dd>${Math.round((evidence.threshold || 0) * 100)}%</dd>
    </dl>
  `;
}

function renderChart() {
  const analysis = state.analysis;
  const canvas = els.canvas;
  const ctx = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const nextWidth = Math.max(1, Math.floor(rect.width * dpr));
  const nextHeight = Math.max(1, Math.floor(rect.height * dpr));
  if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
    canvas.width = nextWidth;
    canvas.height = nextHeight;
  }
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
  const visibleCenters = replayItemsByEnd(analysis.centers || [], "end_index").filter((item) => overlapsWindow(item.start_index, item.end_index, view));
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
  if (state.showStrokes) {
    drawStrokes(ctx, visibleItems(replayItemsByEnd(analysis.strokes || [], "end_index"), "start_index", "end_index", view), x, y, view);
  }
  if (state.showSegments) {
    drawSegments(ctx, visibleItems(replayItemsByEnd(analysis.segments || [], "end_index"), "start_index", "end_index", view), x, y, view);
  }
  drawFractals(ctx, visibleItems(replayItemsByEnd(analysis.fractals || [], "raw_index"), "raw_index", "raw_index", view), x, y);
  drawSignals(ctx, visibleSignals(replayFilteredSignals(analysis.signals || []), view), x, y, plot);
  drawMacd(ctx, rect, macdPlot, visibleMacd, visibleDivergences(replayFilteredDivergences(analysis.divergences || []), view), x, candleW);

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

function drawSegments(ctx, segments, x, y, view) {
  ctx.lineWidth = 3.2;
  ctx.setLineDash([8, 5]);
  segments.forEach((item) => {
    if (!overlapsWindow(item.start_index, item.end_index, view)) return;
    ctx.strokeStyle = item.direction === "up" ? "rgba(169, 53, 45, 0.62)" : "rgba(15, 111, 82, 0.62)";
    ctx.beginPath();
    ctx.moveTo(x(item.start_index), y(item.start_price));
    ctx.lineTo(x(item.end_index), y(item.end_price));
    ctx.stroke();
  });
  ctx.setLineDash([]);
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
  const { tagX, tagY, width, height } = signalTagBounds(x, y, buy, plot);
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

function signalTagBounds(x, y, buy, plot) {
  const width = 34;
  const height = 20;
  const pointer = 6;
  const gap = 7;
  const tagX = Math.max(plot.left + 2, Math.min(x - width / 2, plot.left + plot.width - width - 2));
  const idealY = buy ? y + gap + pointer : y - gap - pointer - height;
  const tagY = Math.max(plot.top + 2, Math.min(idealY, plot.top + plot.height - height - 2));
  return { tagX, tagY, width, height };
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

function scheduleChartRender() {
  if (chartRenderFrame !== null) return;
  chartRenderFrame = window.requestAnimationFrame(() => {
    chartRenderFrame = null;
    renderChart();
  });
}

function resetChartView() {
  const total = state.analysis?.klines?.length || 0;
  state.replayIndex = Math.max(0, total - 1);
  state.visibleCount = Math.min(total || defaultVisibleCount(), defaultVisibleCount());
  state.viewStart = Math.max(0, total - state.visibleCount);
  state.hoverIndex = null;
  updateReplayControls();
}

function defaultVisibleCount() {
  if (state.level === "min30") return 160;
  if (state.level === "min60") return 140;
  if (state.level === "monthly") return 72;
  if (state.level === "weekly") return 104;
  return 120;
}

function clampChartView() {
  const total = effectiveTotal();
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

function clampVisibleCount(count) {
  const total = effectiveTotal();
  if (!total) return defaultVisibleCount();
  const maxVisible = Math.min(MAX_VISIBLE_BARS, total);
  const minVisible = Math.min(MIN_VISIBLE_BARS, total);
  return Math.max(minVisible, Math.min(Math.round(count), maxVisible));
}

function visibleWindow() {
  clampChartView();
  const total = effectiveTotal();
  const start = state.viewStart;
  const end = Math.min(total, start + state.visibleCount);
  return { start, end, count: Math.max(end - start, 1) };
}

function effectiveTotal() {
  const total = state.analysis?.klines?.length || 0;
  if (!total) return 0;
  if (!state.replayEnabled) return total;
  return clamp(state.replayIndex + 1, 1, total);
}

function replayCutoffIndex() {
  const total = state.analysis?.klines?.length || 0;
  if (!total) return -1;
  return state.replayEnabled ? clamp(state.replayIndex, 0, total - 1) : total - 1;
}

function replayItemsByEnd(items, endKey) {
  const cutoff = replayCutoffIndex();
  if (cutoff < 0) return [];
  return items.filter((item) => Number(item[endKey]) <= cutoff);
}

function replayFilteredSignals(signals) {
  const cutoff = replayCutoffIndex();
  if (cutoff < 0) return [];
  return signals.filter((item) => signalIndex(item) <= cutoff);
}

function replayFilteredDivergences(divergences) {
  const cutoff = replayCutoffIndex();
  if (cutoff < 0) return [];
  return divergences.filter((item) => divergenceIndex(item) <= cutoff);
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
  return Math.max(0, Math.min(effectiveTotal() - 1, view.start + Math.floor(ratio * view.count)));
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

function signalFromMainPointer(event, analysis) {
  const rect = els.canvas.getBoundingClientRect();
  const plots = chartPlots(rect);
  const plot = plots.main;
  const pointerX = event.clientX - rect.left;
  const pointerY = event.clientY - rect.top;
  if (pointerY < plot.top || pointerY > plot.top + plot.height) return null;

  const view = visibleWindow();
  const visibleKlines = analysis.klines.slice(view.start, view.end);
  const visibleCenters = replayItemsByEnd(analysis.centers || [], "end_index").filter((item) => overlapsWindow(item.start_index, item.end_index, view));
  const visibleBbi = (analysis.indicators?.bbi || []).slice(view.start, view.end);
  const range = priceRange(visibleKlines, visibleCenters, visibleBbi);
  const x = (idx) => plot.left + ((idx - view.start + 0.5) / view.count) * plot.width;
  const y = (price) => plot.top + ((range.high - price) / (range.high - range.low)) * plot.height;
  const candidates = visibleSignals(replayFilteredSignals(analysis.signals || []), view);
  const barHit = Math.max(10, plot.width / view.count);

  let best = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const item of candidates) {
    const px = x(signalIndex(item));
    const py = y(item.price);
    const buy = item.side === "buy";
    const bounds = signalTagBounds(px, py, buy, plot);
    const insideTag =
      pointerX >= bounds.tagX - 4 &&
      pointerX <= bounds.tagX + bounds.width + 4 &&
      pointerY >= bounds.tagY - 4 &&
      pointerY <= bounds.tagY + bounds.height + 4;
    const nearAnchor = Math.abs(pointerX - px) <= barHit && Math.abs(pointerY - py) <= 18;
    if (!insideTag && !nearAnchor) continue;

    const distance = Math.hypot(pointerX - px, pointerY - py);
    if (distance < bestDistance) {
      best = item;
      bestDistance = distance;
    }
  }
  return best;
}

function showSignalTooltip(event, signal) {
  els.tooltip.hidden = false;
  positionTooltip(event, 280);
  els.tooltip.innerHTML = `
    <strong>${signalLabel(signal)} · ${formatDate(signal.date)}</strong><br>
    状态 ${signal.status_label || "候选"} · 价格 ${formatPrice(signal.price)}<br>
    失效 ${formatPrice(signal.invalidation_price)}<br>
    ${signal.reason || ""}<br>
    <span class="tooltipNote">${signal.confirmation || ""}</span>
    ${signal.observation ? `<br><span class="tooltipNote">${signal.observation}</span>` : ""}
  `;
}

function showMainTooltip(event, analysis, idx) {
  const bar = analysis.klines[idx];
  const macd = analysis.indicators?.macd?.[idx];
  const bbi = analysis.indicators?.bbi?.[idx];

  els.tooltip.hidden = false;
  positionTooltip(event, 220);
  els.tooltip.innerHTML = `
    <strong>${formatDate(bar.date)}</strong><br>
    开 ${formatPrice(bar.open)} 高 ${formatPrice(bar.high)}<br>
    低 ${formatPrice(bar.low)} 收 ${formatPrice(bar.close)}<br>
    BBI ${bbi?.value !== null && bbi?.value !== undefined ? formatPrice(bbi.value) : "-"}<br>
    量 ${Math.round(bar.vol).toLocaleString()}<br>
    MACD ${macd ? formatMacd(macd.hist) : "-"} · DIF ${macd ? formatMacd(macd.dif) : "-"} · DEA ${macd ? formatMacd(macd.dea) : "-"}
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
  positionTooltip(event, 360);
  els.tooltip.innerHTML = `
    <strong>${divergenceLabel(divergence)} · ${formatDate(divergence.date)}</strong><br>
    <span class="tooltipNote">${divergence.position || "背驰候选"} · 力度 ${formatMacd(divergence.current_strength)} / ${formatMacd(divergence.previous_strength)}</span><br>
    ${divergence.reason}<br>
    MACD ${macd ? formatMacd(macd.hist) : "-"} · DIF ${macd ? formatMacd(macd.dif) : "-"} · DEA ${macd ? formatMacd(macd.dea) : "-"}
    ${renderDivergenceEvidence(divergence)}
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
  const plotWidth = Math.max(rect.width - 84, 1);
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left - plotLeft) / plotWidth));
  const view = visibleWindow();
  const anchorIndex = view.start + ratio * view.count;
  const normalizedDelta = event.deltaMode === WheelEvent.DOM_DELTA_LINE ? event.deltaY * 16 : event.deltaY;
  const scale = Math.exp(clamp(normalizedDelta, -240, 240) * WHEEL_ZOOM_SPEED);
  state.visibleCount = clampVisibleCount(view.count * scale);
  state.viewStart = Math.round(anchorIndex - ratio * state.visibleCount);
  clampChartView();
  state.hoverIndex = indexFromPointer(event);
  els.tooltip.hidden = true;
  scheduleChartRender();
}

function levelLabel(level) {
  return { min30: "30分钟", min60: "60分钟", daily: "日线", weekly: "周线", monthly: "月线" }[level] || level;
}

function directionLabel(direction) {
  if (direction === "up") return "向上";
  if (direction === "down") return "向下";
  return "未定";
}

function zeroLabel(position) {
  if (position === "above") return "零轴上";
  if (position === "below") return "零轴下";
  if (position === "crossing") return "穿越零轴";
  return "-";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatDate(value) {
  const text = String(value || "");
  if (text.length >= 12 && /^\d+$/.test(text)) {
    return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)} ${text.slice(8, 10)}:${text.slice(10, 12)}`;
  }
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

function formatPct(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return `${(num * 100).toFixed(2)}%`;
}

function summarizeTradesForReplay(summary, trades) {
  if (!state.replayEnabled) return summary;
  const observed = trades.filter((item) => item.bars > 0);
  const favorable = observed.map((item) => Number(item.max_favorable_pct)).filter(Number.isFinite);
  const adverse = observed.map((item) => Number(item.max_adverse_pct)).filter(Number.isFinite);
  return {
    signals: trades.length,
    observed: observed.length,
    avg_favorable_pct: average(favorable),
    avg_adverse_pct: average(adverse),
  };
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function updateReplayControls() {
  const total = state.analysis?.klines?.length || 0;
  els.replayToggle.checked = state.replayEnabled;
  els.replaySlider.disabled = !state.replayEnabled || total <= 1;
  els.replaySlider.max = String(Math.max(total - 1, 0));
  els.replaySlider.value = String(clamp(state.replayIndex, 0, Math.max(total - 1, 0)));
  const bar = total ? state.analysis.klines[Number(els.replaySlider.value)] : null;
  els.replayLabel.textContent = state.replayEnabled && bar ? formatDate(bar.date) : "--";
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

  els.mainMenu?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-page]");
    if (!button) return;
    switchMainPage(button.dataset.page);
  });

  els.pickerOverviewBtn?.addEventListener("click", loadPickerOverview);
  els.pickerWatchlistBtn?.addEventListener("click", loadPickerWatchlist);
  els.pickerRunBtn?.addEventListener("click", runSmartPicker);
  [els.pickerStructureFilter, els.pickerEmotionFilter, els.pickerOverallFilter, els.pickerSortBy, els.pickerSortDirection].forEach((input) => {
    input?.addEventListener("change", () => {
      syncPickerFiltersFromControls();
      renderPickerTable();
    });
  });
  els.pickerFocusReadyBtn?.addEventListener("click", () => {
    state.smartPicker.focusReadyOnly = !state.smartPicker.focusReadyOnly;
    els.pickerFocusReadyBtn.classList.toggle("active", state.smartPicker.focusReadyOnly);
    renderPickerTable();
  });
  els.pickerClearFiltersBtn?.addEventListener("click", () => {
    state.smartPicker.focusReadyOnly = false;
    if (els.pickerFocusReadyBtn) {
      els.pickerFocusReadyBtn.classList.remove("active");
    }
    if (els.pickerStructureFilter) els.pickerStructureFilter.value = "all";
    if (els.pickerEmotionFilter) els.pickerEmotionFilter.value = "all";
    if (els.pickerOverallFilter) els.pickerOverallFilter.value = "all";
    if (els.pickerSortBy) els.pickerSortBy.value = "overall_score";
    if (els.pickerSortDirection) els.pickerSortDirection.value = "desc";
    syncPickerFiltersFromControls();
    renderPickerTable();
  });
  els.pickerQueryInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      runSmartPicker();
    }
  });

  els.pickerTableBox?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-picker-action]");
    if (!button) return;
    const tsCode = button.dataset.tsCode;
    const candidate = (state.smartPicker.screen?.candidates || []).find((item) => item.stock.ts_code === tsCode);
    if (!candidate) return;
    if (button.dataset.pickerAction === "detail") {
      loadPickerCandidateDetail(candidate.stock);
      return;
    }
    if (button.dataset.pickerAction === "analysis") {
      openCandidateInAnalysis(candidate.stock);
    }
  });

  els.pickerDetailBox?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-picker-detail-action]");
    if (!button) return;
    const action = button.dataset.pickerDetailAction;
    if (action === "ai") {
      loadPickerAiBrief();
      return;
    }
    if (action === "analysis") {
      const stock = state.smartPicker.detail?.stock;
      if (stock) openCandidateInAnalysis(stock);
      return;
    }
    const target = button.dataset.pickerTarget;
    managePickerWatchlist(action, target);
  });

  els.levelTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-level]");
    if (!button) return;
    state.level = button.dataset.level;
    els.levelTabs.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item === button));
    if (state.analysis || state.selectedStock) loadAnalysis();
  });

  els.refreshBtn.addEventListener("click", loadAnalysis);

  els.showStrokes.addEventListener("change", () => {
    state.showStrokes = els.showStrokes.checked;
    renderChart();
  });

  els.showSegments.addEventListener("change", () => {
    state.showSegments = els.showSegments.checked;
    renderChart();
  });

  els.replayToggle.addEventListener("change", () => {
    state.replayEnabled = els.replayToggle.checked;
    clampChartView();
    updateReplayControls();
    renderAll();
  });

  els.replaySlider.addEventListener("input", () => {
    state.replayIndex = Number(els.replaySlider.value);
    clampChartView();
    renderAll();
  });

  els.sideTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-side-panel]");
    if (!button) return;
    const targetId = button.dataset.sidePanel;
    els.sideTabs.querySelectorAll("button[data-side-panel]").forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    document.querySelectorAll(".sidePane").forEach((panel) => {
      panel.classList.toggle("active", panel.id === targetId);
    });
  });

  els.pickerSideTabs?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-picker-side-panel]");
    if (!button) return;
    const targetId = button.dataset.pickerSidePanel;
    els.pickerSideTabs.querySelectorAll("button[data-picker-side-panel]").forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    document.querySelectorAll(".pickerSidePane").forEach((panel) => {
      panel.classList.toggle("active", panel.id === targetId);
    });
  });

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
      scheduleChartRender();
      return;
    }

    const idx = indexFromPointer(event);
    if (idx === null) return;
    state.hoverIndex = idx;
    const region = chartRegionFromPointer(event);
    if (region === "main") {
      const signal = signalFromMainPointer(event, analysis);
      if (signal) showSignalTooltip(event, signal);
      else showMainTooltip(event, analysis, idx);
    } else if (region === "macd") {
      showMacdTooltip(event, analysis);
    } else {
      els.tooltip.hidden = true;
    }
    scheduleChartRender();
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
    scheduleChartRender();
  });

  els.canvas.addEventListener("wheel", zoomAtPointer, { passive: false });

  window.addEventListener("resize", scheduleChartRender);
}

bindEvents();
renderChart();
