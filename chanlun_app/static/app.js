const state = {
  selectedStock: null,
  level: "daily",
  currentPage: "analysisPage",
  analysis: null,
  mxSummary: null,
  profileSummary: null,
  mxRequestId: 0,
  eventNews: null,
  eventNewsRequestId: 0,
  analysisWatchlist: { status: "idle", message: "" },
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
    aiRequestId: 0,
    focusReadyOnly: false,
    marketScopeFilter: "all",
    structureFilter: "all",
    emotionFilter: "all",
    leaderFilter: "all",
    overallFilter: "all",
    sortBy: "overall_score",
    sortDirection: "desc",
    boardType: "all",
    boardMatches: [],
    selectedBoard: null,
    boardSearchRequestId: 0,
    tdxType: "all",
    tdxMatches: [],
    selectedTdxBoard: null,
    tdxSearchRequestId: 0,
    thsType: "all",
    thsMatches: [],
    selectedThsBoard: null,
    thsSearchRequestId: 0,
    screenFilters: {},
    loaded: false,
  },
  review: {
    overview: null,
    requestId: 0,
    aiRequestId: 0,
    loaded: false,
    modalKey: "",
    modalSearch: "",
    hotMoneyPage: 1,
    modalPage: 1,
  },
  themeBoard: {
    overview: null,
    detail: null,
    requestId: 0,
    detailRequestId: 0,
    loaded: false,
    modalTsCode: "",
    modalName: "",
  },
  themeResearch: {
    loaded: false,
    loading: false,
    historyLoaded: false,
    historyPage: 1,
    historyPageSize: 6,
    historyTotal: 0,
    historyTotalPages: 1,
    currentTaskId: "",
    currentThemeName: "",
    events: [],
    history: [],
    reportPayload: null,
    historyRequestId: 0,
    reportRequestId: 0,
    stream: null,
  },
  systemConfig: {
    list: [],
    loaded: false,
    requestId: 0,
    saving: false,
    editingKey: "",
  },
  watchtower: {
    overview: null,
    requestId: 0,
    loaded: false,
    query: "",
    page: 1,
    modalDetail: null,
    modalRequestId: 0,
    syncingEastmoneyTsCode: "",
    lastEastmoneyTsCode: "",
    lastEastmoneyMessage: "",
  },
};

const els = {
  mainMenu: document.querySelector("#mainMenu"),
  stockInput: document.querySelector("#stockInput"),
  analysisWatchlistBtn: document.querySelector("#analysisWatchlistBtn"),
  analysisWatchlistHint: document.querySelector("#analysisWatchlistHint"),
  suggestions: document.querySelector("#suggestions"),
  statusText: document.querySelector("#statusText"),
  stockBasics: document.querySelector("#stockBasics"),
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
  eventNewsBox: document.querySelector("#eventNewsBox"),
  centerList: document.querySelector("#centerList"),
  mxDataBox: document.querySelector("#mxDataBox"),
  leaderAnalysisBox: document.querySelector("#leaderAnalysisBox"),
  pages: document.querySelectorAll(".appPage"),
  pickerStatusText: document.querySelector("#pickerStatusText"),
  pickerOverviewBtn: document.querySelector("#pickerOverviewBtn"),
  pickerWatchlistBtn: document.querySelector("#pickerWatchlistBtn"),
  pickerQueryInput: document.querySelector("#pickerQueryInput"),
  pickerRunConditionBtn: document.querySelector("#pickerRunConditionBtn"),
  pickerBoardType: document.querySelector("#pickerBoardType"),
  pickerBoardInput: document.querySelector("#pickerBoardInput"),
  pickerBoardOptions: document.querySelector("#pickerBoardOptions"),
  pickerBoardSelection: document.querySelector("#pickerBoardSelection"),
  pickerRunDcBtn: document.querySelector("#pickerRunDcBtn"),
  pickerTdxType: document.querySelector("#pickerTdxType"),
  pickerTdxInput: document.querySelector("#pickerTdxInput"),
  pickerTdxOptions: document.querySelector("#pickerTdxOptions"),
  pickerTdxSelection: document.querySelector("#pickerTdxSelection"),
  pickerRunTdxBtn: document.querySelector("#pickerRunTdxBtn"),
  pickerThsType: document.querySelector("#pickerThsType"),
  pickerThsInput: document.querySelector("#pickerThsInput"),
  pickerThsOptions: document.querySelector("#pickerThsOptions"),
  pickerThsSelection: document.querySelector("#pickerThsSelection"),
  pickerRunThsBtn: document.querySelector("#pickerRunThsBtn"),
  pickerLevel: document.querySelector("#pickerLevel"),
  pickerLimit: document.querySelector("#pickerLimit"),
  pickerTechnicalShape: document.querySelector("#pickerTechnicalShape"),
  pickerScreenMarket: document.querySelector("#pickerScreenMarket"),
  pickerTurnoverMin: document.querySelector("#pickerTurnoverMin"),
  pickerTurnoverMax: document.querySelector("#pickerTurnoverMax"),
  pickerMarketCapMin: document.querySelector("#pickerMarketCapMin"),
  pickerMarketCapMax: document.querySelector("#pickerMarketCapMax"),
  pickerRunBtn: document.querySelector("#pickerRunBtn"),
  pickerEastmoneyBatchBtn: document.querySelector("#pickerEastmoneyBatchBtn"),
  pickerMarketScopeFilter: document.querySelector("#pickerMarketScopeFilter"),
  pickerStructureFilter: document.querySelector("#pickerStructureFilter"),
  pickerEmotionFilter: document.querySelector("#pickerEmotionFilter"),
  pickerLeaderFilter: document.querySelector("#pickerLeaderFilter"),
  pickerOverallFilter: document.querySelector("#pickerOverallFilter"),
  pickerSortBy: document.querySelector("#pickerSortBy"),
  pickerSortDirection: document.querySelector("#pickerSortDirection"),
  pickerFocusReadyBtn: document.querySelector("#pickerFocusReadyBtn"),
  pickerClearFiltersBtn: document.querySelector("#pickerClearFiltersBtn"),
  pickerErrorBox: document.querySelector("#pickerErrorBox"),
  pickerSideTabs: document.querySelector("#pickerSideTabs"),
  pickerMarketBox: document.querySelector("#pickerMarketBox"),
  pickerNewsBox: document.querySelector("#pickerNewsBox"),
  pickerTableBox: document.querySelector("#pickerTableBox"),
  pickerTableStatus: document.querySelector("#pickerTableStatus"),
  pickerResultMeta: document.querySelector("#pickerResultMeta"),
  pickerDetailBox: document.querySelector("#pickerDetailBox"),
  reviewStatusText: document.querySelector("#reviewStatusText"),
  reviewDate: document.querySelector("#reviewDate"),
  reviewRefreshBtn: document.querySelector("#reviewRefreshBtn"),
  reviewErrorBox: document.querySelector("#reviewErrorBox"),
  reviewSummaryBox: document.querySelector("#reviewSummaryBox"),
  reviewDragonBox: document.querySelector("#reviewDragonBox"),
  reviewInstBox: document.querySelector("#reviewInstBox"),
  reviewLimitBox: document.querySelector("#reviewLimitBox"),
  reviewLadderBox: document.querySelector("#reviewLadderBox"),
  reviewSideTabs: document.querySelector("#reviewSideTabs"),
  reviewFocusBox: document.querySelector("#reviewFocusBox"),
  reviewEmotionCycleBox: document.querySelector("#reviewEmotionCycleBox"),
  reviewBoardsBox: document.querySelector("#reviewBoardsBox"),
  reviewStocksBox: document.querySelector("#reviewStocksBox"),
  reviewModal: document.querySelector("#reviewModal"),
  reviewModalTitle: document.querySelector("#reviewModalTitle"),
  reviewModalMeta: document.querySelector("#reviewModalMeta"),
  reviewModalBody: document.querySelector("#reviewModalBody"),
  reviewModalCloseBtn: document.querySelector("#reviewModalCloseBtn"),
  themeBoardStatusText: document.querySelector("#themeBoardStatusText"),
  themeBoardDate: document.querySelector("#themeBoardDate"),
  themeBoardRefreshBtn: document.querySelector("#themeBoardRefreshBtn"),
  themeBoardErrorBox: document.querySelector("#themeBoardErrorBox"),
  themeBoardSummaryBox: document.querySelector("#themeBoardSummaryBox"),
  themeBoardListBox: document.querySelector("#themeBoardListBox"),
  themeBoardInsightBox: document.querySelector("#themeBoardInsightBox"),
  themeBoardModal: document.querySelector("#themeBoardModal"),
  themeBoardModalTitle: document.querySelector("#themeBoardModalTitle"),
  themeBoardModalMeta: document.querySelector("#themeBoardModalMeta"),
  themeBoardModalBody: document.querySelector("#themeBoardModalBody"),
  themeBoardModalCloseBtn: document.querySelector("#themeBoardModalCloseBtn"),
  themeResearchStatusText: document.querySelector("#themeResearchStatusText"),
  themeResearchInput: document.querySelector("#themeResearchInput"),
  themeResearchStartBtn: document.querySelector("#themeResearchStartBtn"),
  themeResearchMarket: document.querySelector("#themeResearchMarket"),
  themeResearchDepth: document.querySelector("#themeResearchDepth"),
  themeResearchHorizon: document.querySelector("#themeResearchHorizon"),
  themeResearchErrorBox: document.querySelector("#themeResearchErrorBox"),
  themeResearchProgressBox: document.querySelector("#themeResearchProgressBox"),
  themeResearchPreviewBox: document.querySelector("#themeResearchPreviewBox"),
  themeResearchReportBox: document.querySelector("#themeResearchReportBox"),
  themeResearchHistoryMeta: document.querySelector("#themeResearchHistoryMeta"),
  themeResearchHistoryBox: document.querySelector("#themeResearchHistoryBox"),
  systemConfigStatusText: document.querySelector("#systemConfigStatusText"),
  systemConfigRefreshBtn: document.querySelector("#systemConfigRefreshBtn"),
  systemConfigCreateBtn: document.querySelector("#systemConfigCreateBtn"),
  systemConfigErrorBox: document.querySelector("#systemConfigErrorBox"),
  systemConfigListMeta: document.querySelector("#systemConfigListMeta"),
  systemConfigTableBox: document.querySelector("#systemConfigTableBox"),
  systemConfigModal: document.querySelector("#systemConfigModal"),
  systemConfigModalCloseBtn: document.querySelector("#systemConfigModalCloseBtn"),
  systemConfigForm: document.querySelector("#systemConfigForm"),
  systemConfigFormTitle: document.querySelector("#systemConfigFormTitle"),
  systemConfigFormMeta: document.querySelector("#systemConfigFormMeta"),
  systemConfigKeyInput: document.querySelector("#systemConfigKeyInput"),
  systemConfigLabelInput: document.querySelector("#systemConfigLabelInput"),
  systemConfigCategoryInput: document.querySelector("#systemConfigCategoryInput"),
  systemConfigDescriptionInput: document.querySelector("#systemConfigDescriptionInput"),
  systemConfigValueInput: document.querySelector("#systemConfigValueInput"),
  systemConfigSecretInput: document.querySelector("#systemConfigSecretInput"),
  systemConfigEnabledInput: document.querySelector("#systemConfigEnabledInput"),
  systemConfigDeleteBtn: document.querySelector("#systemConfigDeleteBtn"),
  systemConfigResetBtn: document.querySelector("#systemConfigResetBtn"),
  watchtowerStatusText: document.querySelector("#watchtowerStatusText"),
  watchtowerQueryInput: document.querySelector("#watchtowerQueryInput"),
  watchtowerSearchBtn: document.querySelector("#watchtowerSearchBtn"),
  watchtowerRefreshBtn: document.querySelector("#watchtowerRefreshBtn"),
  watchtowerErrorBox: document.querySelector("#watchtowerErrorBox"),
  watchtowerSummaryBox: document.querySelector("#watchtowerSummaryBox"),
  watchtowerTableStatus: document.querySelector("#watchtowerTableStatus"),
  watchtowerResultMeta: document.querySelector("#watchtowerResultMeta"),
  watchtowerTableBox: document.querySelector("#watchtowerTableBox"),
  watchtowerGuideBox: document.querySelector("#watchtowerGuideBox"),
  watchtowerModal: document.querySelector("#watchtowerModal"),
  watchtowerModalTitle: document.querySelector("#watchtowerModalTitle"),
  watchtowerModalMeta: document.querySelector("#watchtowerModalMeta"),
  watchtowerModalBody: document.querySelector("#watchtowerModalBody"),
  watchtowerModalCloseBtn: document.querySelector("#watchtowerModalCloseBtn"),
  pickerEastmoneyModal: document.querySelector("#pickerEastmoneyModal"),
  pickerEastmoneyModalTitle: document.querySelector("#pickerEastmoneyModalTitle"),
  pickerEastmoneyModalMeta: document.querySelector("#pickerEastmoneyModalMeta"),
  pickerEastmoneyForm: document.querySelector("#pickerEastmoneyForm"),
  pickerEastmoneyGroupInput: document.querySelector("#pickerEastmoneyGroupInput"),
  pickerEastmoneyTargetsInput: document.querySelector("#pickerEastmoneyTargetsInput"),
  pickerEastmoneyFeedback: document.querySelector("#pickerEastmoneyFeedback"),
  analysisJumpLoading: document.querySelector("#analysisJumpLoading"),
  analysisJumpLoadingText: document.querySelector("#analysisJumpLoadingText"),
};

let searchTimer = null;
let pickerBoardTimer = null;
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

async function loadAnalysis(options = {}) {
  const showJumpLoading = options.showJumpLoading === true;
  const jumpLoadingText = options.jumpLoadingText || "智能分析中";
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

  if (showJumpLoading) {
    setAnalysisJumpLoading(true, jumpLoadingText);
  }
  setLoading(true);
  state.mxRequestId += 1;
  state.mxSummary = null;
  state.profileSummary = null;
  state.eventNewsRequestId += 1;
  state.eventNews = null;
  state.analysisWatchlist = { status: "idle", message: "" };
  try {
    const data = await fetchJson(`/api/analysis?${params.toString()}`);
    state.analysis = data;
    state.selectedStock = data.stock;
    resetChartView();
    els.stockInput.value = `${data.stock.name} ${data.stock.symbol}`;
    els.statusText.textContent = `${levelLabel(state.level)} · ${formatDate(data.query.start_date)} 至 ${formatDate(data.query.end_date)}`;
    hideError();
    loadMxSummary(data.stock);
    loadEventNews(data.stock);
    renderAll();
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
    if (showJumpLoading) {
      setAnalysisJumpLoading(false);
    }
  }
}

async function fetchJson(url, options = {}) {
  const { timeoutMs = 0, timeoutMessage = "请求超时，请稍后重试。", ...fetchOptions } = options;
  let controller = null;
  let timeoutId = null;
  if (timeoutMs > 0 && typeof AbortController !== "undefined") {
    controller = new AbortController();
    fetchOptions.signal = controller.signal;
    timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  }

  try {
    const response = await fetch(url, fetchOptions);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error?.message || `请求失败：${response.status}`);
    }
    return data;
  } catch (err) {
    if (err?.name === "AbortError") {
      throw new Error(timeoutMessage);
    }
    throw err;
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
}

async function loadMxSummary(stock) {
  if (!stock) return;
  const requestId = ++state.mxRequestId;
  state.mxSummary = { status: "loading" };
  state.profileSummary = { status: "loading" };
  renderMxData();
  renderLeaderAnalysis();

  const profilePromise = fetchJson("/api/trading-profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    timeoutMs: 12000,
    timeoutMessage: "龙头分析加载超时，请稍后重试。",
    body: JSON.stringify({
      stock,
      analysis: state.analysis,
      include_mx_summary: false,
      include_ai_summary: false,
    }),
  });
  const mxCardsPromise = fetchJson(`/api/mx/summary?ts_code=${encodeURIComponent(stock.ts_code || "")}&name=${encodeURIComponent(stock.name || "")}`, {
    timeoutMs: 18000,
    timeoutMessage: "妙想数据加载超时，请稍后重试。",
  });

  const [profileResult, mxCardsResult] = await Promise.allSettled([profilePromise, mxCardsPromise]);
  if (requestId !== state.mxRequestId) return;

  if (profileResult.status === "fulfilled") {
    state.profileSummary = { status: "ok", data: profileResult.value };
  } else {
    state.profileSummary = { status: "error", message: profileResult.reason?.message || "龙头分析加载失败。" };
  }

  if (mxCardsResult.status === "fulfilled") {
    state.mxSummary = { status: "ok", data: mxCardsResult.value };
  } else {
    state.mxSummary = { status: "error", message: mxCardsResult.reason?.message || "妙想数据加载失败。" };
  }

  renderMxData();
  renderLeaderAnalysis();
}

async function loadEventNews(stock) {
  if (!stock) return;
  const requestId = ++state.eventNewsRequestId;
  state.eventNews = { status: "loading" };
  renderEventCatalyst();
  try {
    const data = await fetchJson(`/api/mx/news?ts_code=${encodeURIComponent(stock.ts_code || "")}&name=${encodeURIComponent(stock.name || "")}`, {
      timeoutMs: 8000,
      timeoutMessage: "妙想事件加载超时，请稍后重试。",
    });
    if (requestId !== state.eventNewsRequestId) return;
    state.eventNews = data;
  } catch (err) {
    if (requestId !== state.eventNewsRequestId) return;
    state.eventNews = { status: "error", message: err.message };
  }
  renderEventCatalyst();
}

function setLoading(isLoading) {
  els.refreshBtn.disabled = isLoading;
  els.refreshBtn.textContent = isLoading ? "分析中" : "分析";
}

function setAnalysisJumpLoading(isVisible, text = "智能分析中") {
  if (!els.analysisJumpLoading) return;
  if (els.analysisJumpLoadingText) {
    els.analysisJumpLoadingText.textContent = text;
  }
  els.analysisJumpLoading.hidden = !isVisible;
  document.body.classList.toggle("hasAnalysisJumpLoading", isVisible);
}

function startAnalysisFlow(options = {}) {
  const loadingText = options.loadingText || "智能分析中";
  setAnalysisJumpLoading(true, loadingText);
  loadAnalysis({ showJumpLoading: true, jumpLoadingText: loadingText });
}

async function withPageLoading(loadingText, task) {
  setAnalysisJumpLoading(true, loadingText);
  try {
    return await task();
  } finally {
    setAnalysisJumpLoading(false);
  }
}

function startSmartPickerFlow(task) {
  return withPageLoading("智能选股中", task);
}

function startReviewFlow(task) {
  return withPageLoading("智能复盘中", task);
}

function startThemeBoardFlow(task) {
  return withPageLoading("题材榜单加载中", task);
}

function startThemeResearchFlow(task) {
  return withPageLoading("题材研究中", task);
}

function startSystemConfigFlow(task) {
  return withPageLoading("系统配置加载中", task);
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
    return;
  }

  if (targetId === "watchtowerPage") {
    ensureWatchtowerLoaded();
    return;
  }

  if (targetId === "reviewPage") {
    ensureReviewLoaded();
    return;
  }

  if (targetId === "themeResearchPage") {
    ensureThemeResearchLoaded();
    return;
  }

  if (targetId === "themeBoardPage") {
    ensureThemeBoardLoaded();
    return;
  }

  if (targetId === "systemConfigPage") {
    ensureSystemConfigLoaded();
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
  renderAnalysisWatchlistAction();
  renderChart();
  renderLevelContext();
  renderStructureDetail();
  renderRiskCards();
  renderBacktest();
  renderEventCatalyst();
  renderCenters();
  renderMxData();
  renderLeaderAnalysis();
}

function renderAnalysisWatchlistAction() {
  if (!els.analysisWatchlistBtn || !els.analysisWatchlistHint) return;
  const stock = state.analysis?.stock || null;
  const watch = state.analysisWatchlist || { status: "idle", message: "" };
  const stockName = stock?.name || stock?.symbol || "";

  els.analysisWatchlistBtn.disabled = !stock || watch.status === "loading" || watch.status === "ok";
  els.analysisWatchlistBtn.classList.toggle("active", watch.status === "ok");

  if (!stock) {
    els.analysisWatchlistBtn.textContent = "加入自选";
    els.analysisWatchlistHint.textContent = "加入后会同步当前股票基础资料到 MySQL 缓存。";
    return;
  }

  if (watch.status === "loading") {
    els.analysisWatchlistBtn.textContent = "加入中";
    els.analysisWatchlistHint.textContent = `正在把 ${stockName} 加入自选，并同步基础资料缓存。`;
    return;
  }

  if (watch.status === "ok") {
    els.analysisWatchlistBtn.textContent = "已在自选";
    const cache = watch.cache || {};
    if (cache.status === "ok") {
      els.analysisWatchlistHint.textContent = `${stockName} 已加入自选，基础资料已写入 MySQL 缓存。`;
    } else if (cache.status === "disabled") {
      els.analysisWatchlistHint.textContent = `${stockName} 已加入自选；当前环境未配置 MySQL 缓存。`;
    } else if (cache.status === "error") {
      els.analysisWatchlistHint.textContent = `${stockName} 已加入自选，但基础资料缓存写入失败：${cache.message || "未知错误"}`;
    } else {
      els.analysisWatchlistHint.textContent = `${stockName} 已加入自选。`;
    }
    return;
  }

  if (watch.status === "error") {
    els.analysisWatchlistBtn.textContent = "加入自选";
    els.analysisWatchlistHint.textContent = watch.message || "加入自选失败，请稍后重试。";
    return;
  }

  els.analysisWatchlistBtn.textContent = "加入自选";
  els.analysisWatchlistHint.textContent = `${stockName} 分析完成后，可以直接加入自选并同步基础资料缓存。`;
}

async function addCurrentAnalysisToWatchlist() {
  const stock = state.analysis?.stock;
  if (!stock || state.analysisWatchlist?.status === "loading" || state.analysisWatchlist?.status === "ok") {
    return;
  }

  state.analysisWatchlist = { status: "loading", message: "" };
  renderAnalysisWatchlistAction();
  try {
    const data = await fetchJson("/api/analysis/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "add",
        stock,
        bak_basic: stock.bak_basic || {},
      }),
    });
    state.analysisWatchlist = {
      status: "ok",
      message: data.message || "操作成功",
      cache: data.cache || {},
    };
    if (state.watchtower.loaded || state.currentPage === "watchtowerPage") {
      loadWatchtowerOverview(state.watchtower.page || 1);
    }
  } catch (err) {
    state.analysisWatchlist = { status: "error", message: err.message };
  }
  renderAnalysisWatchlistAction();
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

function renderEventCatalyst() {
  if (!els.eventNewsBox) return;
  if (!state.analysis) {
    els.eventNewsBox.className = "empty";
    els.eventNewsBox.textContent = "分析完成后通过妙想检索这只股票的公告、研报和机构观点。";
    return;
  }

  const news = state.eventNews;
  if (!news || news.status === "loading") {
    els.eventNewsBox.className = "mxStack";
    els.eventNewsBox.innerHTML = `
      <article class="mxCard loading">
        <div class="mxCardHeader">
          <strong>事件</strong>
          <small>加载中</small>
        </div>
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton short"></div>
      </article>
    `;
    return;
  }

  if (news.status === "error") {
    els.eventNewsBox.className = "mxError";
    els.eventNewsBox.textContent = news.message || "妙想事件加载失败。";
    return;
  }

  els.eventNewsBox.className = "mxStack";
  els.eventNewsBox.innerHTML = renderNewsDigest(news) || `<div class="empty">未检索到相关事件。</div>`;
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
  renderAnalysisBasics();
  if (!els.mxDataBox) return;
  const profileSummary = state.profileSummary;
  const mxSummary = state.mxSummary;
  if (!state.analysis) {
    els.mxDataBox.className = "empty";
    els.mxDataBox.textContent = "分析完成后加载行情、资金、估值、财务和公司资料。";
    return;
  }

  const profileLoading = !profileSummary || profileSummary.status === "loading";
  const mxLoading = !mxSummary || mxSummary.status === "loading";
  if (profileLoading && mxLoading) {
    els.mxDataBox.className = "mxStack";
    els.mxDataBox.innerHTML = ["综合画像", "市场扫描", "行情", "资金", "估值", "财务"]
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

  const blocks = [];
  if (profileSummary?.status === "ok") {
    blocks.push(renderProfileCard(profileSummary.data?.profile));
    blocks.push(renderMarketScan(profileSummary.data?.market_scan));
  } else if (profileSummary?.status === "error") {
    blocks.push(renderInlineMxErrorCard("综合画像", profileSummary.message || "综合画像加载失败。"));
    blocks.push(renderInlineMxErrorCard("市场扫描", profileSummary.message || "市场扫描加载失败。"));
  }

  if (mxSummary?.status === "ok") {
    blocks.push(...((mxSummary.data?.cards || []).map(renderMxCard)));
  } else if (mxSummary?.status === "error") {
    blocks.push(renderInlineMxErrorCard("妙想数据", mxSummary.message || "妙想数据加载失败。"));
  }

  els.mxDataBox.className = "mxStack";
  els.mxDataBox.innerHTML = blocks
    .filter(Boolean)
    .join("") || `<div class="empty">当前没有可展示的妙想数据。</div>`;
}

function renderLeaderAnalysis() {
  if (!els.leaderAnalysisBox) return;
  if (!state.analysis) {
    els.leaderAnalysisBox.className = "empty";
    els.leaderAnalysisBox.textContent = "分析完成后结合养家视角、结构、容量和 AI 补充判断是否属于龙头候选。";
    return;
  }

  const summary = state.profileSummary;
  if (!summary || summary.status === "loading") {
    els.leaderAnalysisBox.className = "mxStack";
    els.leaderAnalysisBox.innerHTML = `
      <article class="profileCard stance-neutral">
        <div class="profileHero">
          <div>
            <span class="profileEyebrow">龙头分析</span>
            <h3>加载中</h3>
          </div>
        </div>
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton short"></div>
      </article>
    `;
    return;
  }

  if (summary.status === "error") {
    els.leaderAnalysisBox.className = "mxError";
    els.leaderAnalysisBox.textContent = summary.message || "龙头分析加载失败。";
    return;
  }

  const leader = summary.data?.leader_profile;
  if (!leader) {
    els.leaderAnalysisBox.className = "empty";
    els.leaderAnalysisBox.textContent = "当前没有可用的龙头分析结果。";
    return;
  }

  const checklist = Array.isArray(leader.checklist) ? leader.checklist : [];
  const tags = Array.isArray(leader.tags) ? leader.tags.filter(Boolean).slice(0, 4) : [];
  const aiSection = leader.ai_section || null;

  els.leaderAnalysisBox.className = "leaderStack";
  els.leaderAnalysisBox.innerHTML = `
    <article class="profileCard stance-${escapeHtml(toneToStance(leader.tone))}">
      <div class="profileHero">
        <div>
          <span class="profileEyebrow">龙头分析</span>
          <h3>${escapeHtml(leader.label || "先观察")}</h3>
        </div>
        <div class="profileTags">
          ${tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
        </div>
      </div>
      <p class="profileHeadline">${escapeHtml(leader.headline || "")}</p>
      ${leader.action ? `<p class="profileDecisionLine">${escapeHtml(leader.action)}</p>` : ""}
      ${leader.summary ? `<p class="profileConclusion">${escapeHtml(leader.summary)}</p>` : ""}
      <div class="profileGrid">
        ${renderLeaderBlock({
          title: "龙头定位",
          verdict: leader.verdict,
          tone: leader.tone,
          summary: leader.detail,
          action: "",
          basis: leader.basis,
          conditions: [],
        })}
        ${renderLeaderBlock({
          title: "退潮判断",
          verdict: leader.retreat_label,
          tone: toneFromRetreatLabel(leader.retreat_label),
          summary: `龙头分 ${leader.score ?? "-"} · 退潮分 ${leader.topping_score ?? "-"}`,
          action: "",
          basis: [],
          conditions: leader.conditions,
        })}
        ${
          checklist.length
            ? `
              <div class="profileBlock tone-${escapeHtml(leader.tone || "neutral")}">
                <div class="profileBlockHeader">
                  <strong>龙头条件清单</strong>
                  <span class="profileVerdict tone-${escapeHtml(leader.tone || "neutral")}">养家口径</span>
                </div>
                <div class="leaderChecklist">
                  ${checklist
                    .map(
                      (item) => `
                        <article class="leaderCheckItem status-${escapeHtml(item.status || "watch")}">
                          <div class="leaderCheckHeader">
                            <strong>${escapeHtml(item.label || "")}</strong>
                            <span>${escapeHtml(item.status_label || "")}</span>
                          </div>
                          <p>${escapeHtml(item.detail || "")}</p>
                        </article>
                      `
                    )
                    .join("")}
                </div>
              </div>
            `
            : ""
        }
        ${aiSection ? renderLeaderBlock(aiSection) : ""}
      </div>
    </article>
  `;
}

function renderLeaderBlock(item) {
  if (!item) return "";
  return `
    <div class="profileBlock tone-${escapeHtml(item.tone || "neutral")}">
      <div class="profileBlockHeader">
        <strong>${escapeHtml(item.title || "")}</strong>
        ${item.verdict ? `<span class="profileVerdict tone-${escapeHtml(item.tone || "neutral")}">${escapeHtml(item.verdict)}</span>` : ""}
      </div>
      ${item.summary ? `<p>${escapeHtml(item.summary)}</p>` : ""}
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
  `;
}

function toneToStance(tone) {
  if (tone === "positive") return "positive";
  if (tone === "caution") return "caution";
  return "neutral";
}

function toneFromRetreatLabel(label) {
  if (label === "疑似退潮见顶") return "caution";
  if (label === "退潮观察") return "neutral";
  return "positive";
}

function renderInlineMxErrorCard(title, message) {
  return `
    <article class="mxCard status-error">
      <div class="mxCardHeader">
        <strong>${escapeHtml(title || "数据异常")}</strong>
        <small>加载失败</small>
      </div>
      <p class="mxCardMessage">${escapeHtml(message || "请求失败，请稍后重试。")}</p>
    </article>
  `;
}

function renderAnalysisBasics() {
  if (!els.stockBasics) return;
  const stock = state.analysis?.stock;
  if (!stock) {
    els.stockBasics.hidden = true;
    els.stockBasics.innerHTML = "";
    return;
  }

  const quoteRow = mxSummaryRow("quote");
  const valuationRow = mxSummaryRow("valuation");
  const companyRow = mxSummaryRow("company_profile");
  const bakBasic = stock?.bak_basic || {};
  const loading = !!state.analysis && (
    !state.mxSummary
    || state.mxSummary.status === "loading"
    || !state.profileSummary
    || state.profileSummary.status === "loading"
  );
  const area = stock.area || bakBasic.area || "待补充";
  const inCoreRegion = isYangtzeDeltaArea(area);

  const compactMetrics = [
    ["换手率", metricValue(quoteRow, ["换手率"]) || loadingText(loading)],
    ["总市值", metricValue(valuationRow, ["总市值"]) || loadingText(loading)],
    ["PE / PB", buildPePbText(bakBasic)],
    ["股东人数", buildHolderText(companyRow, bakBasic, loading)],
    ["总股本", buildTotalShareText(bakBasic)],
    ["营收 / 利润同比", buildGrowthText(bakBasic)],
  ];

  const industryText = buildIndustryConceptText(stock, currentProfilePayload(), companyRow);
  const businessText = buildBusinessText(companyRow, stock);

  els.stockBasics.hidden = false;
  els.stockBasics.innerHTML = `
    <section class="stockHeaderRibbon">
      <div class="stockIdentity">
        <strong>${escapeHtml(stock.name || "")}</strong>
        <span>${escapeHtml(stock.ts_code || stock.symbol || "")}</span>
      </div>
      <div class="stockTagGroup">
        <span class="stockTag ${inCoreRegion ? "alert" : ""}">${escapeHtml(area)}${inCoreRegion ? " · 江浙沪" : ""}</span>
        <span class="stockTag">${escapeHtml(stock.market || "市场待补充")}</span>
        <span class="stockTag">${escapeHtml(industryText)}</span>
      </div>
    </section>
    <section class="stockMetricRibbon">
      ${compactMetrics
        .map(
          ([label, value]) => `
            <article class="stockMetricChip">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </article>
          `
        )
        .join("")}
    </section>
    <section class="stockFactRibbon">
      <article class="stockFactChip">
        <span>行业 / 题材</span>
        <strong>${escapeHtml(industryText)}</strong>
      </article>
      <article class="stockFactChip wide">
        <span>主营业务</span>
        <strong>${escapeHtml(businessText)}</strong>
      </article>
    </section>
  `;
}

function isYangtzeDeltaArea(area) {
  const text = String(area || "").trim();
  return ["上海", "江苏", "浙江"].some((item) => text.includes(item));
}

function loadingText(loading) {
  return loading ? "加载中" : "待补充";
}

function currentProfilePayload() {
  return state.profileSummary?.status === "ok" ? state.profileSummary.data : null;
}

function mxSummaryRow(cardKey) {
  const cards = state.mxSummary?.status === "ok" ? (state.mxSummary.data?.cards || []) : [];
  const card = cards.find((item) => item.key === cardKey);
  return card?.rows?.[0] || null;
}

function metricValue(row, labels) {
  if (!row) return "";
  const keys = Object.keys(row);
  for (const label of labels) {
    const key = keys.find((item) => String(item).includes(label));
    const value = key ? row[key] : "";
    if (value !== null && value !== undefined && String(value).trim()) {
      return String(value).trim();
    }
  }
  return "";
}

function buildIndustryConceptText(stock, payload, companyRow) {
  const industry = stock?.industry || "待补充";
  const tushareConcepts = Array.isArray(stock?.dc_concepts) ? stock.dc_concepts : [];
  const themeNames = tushareConcepts
    .map((item) => item.theme_name || "")
    .filter((value) => value && !/^[0-9]{6}\.DC$/i.test(value))
    .slice(0, 2);
  if (themeNames.length) return `${industry} · ${themeNames.join(" / ")}`;
  const concept = metricValue(companyRow, ["所属概念", "题材", "概念"]);
  if (concept) return `${industry} · ${concept}`;
  const emotionLabel = payload?.profile?.emotion?.label || "";
  if (!emotionLabel) return industry;
  return `${industry} · ${emotionLabel}`;
}

function buildBusinessText(companyRow, stock) {
  const business = metricValue(companyRow, ["主营业务", "主营"]);
  if (business) return business;
  const tushareConcepts = Array.isArray(stock?.dc_concepts) ? stock.dc_concepts : [];
  const reason = tushareConcepts.map((item) => item.reason || "").find(Boolean);
  return reason || "待补充";
}

function buildPePbText(bakBasic) {
  const pe = formatBakMetric(bakBasic?.pe, "");
  const pb = formatBakMetric(bakBasic?.pb, "");
  if (pe && pb) return `${pe} / ${pb}`;
  if (pe) return `${pe} / -`;
  if (pb) return `- / ${pb}`;
  return "待补充";
}

function buildHolderText(companyRow, bakBasic, loading) {
  const rowValue = metricValue(companyRow, ["股东户数", "股东数", "股东人数"]);
  if (rowValue) return rowValue;
  const holderNum = formatBakMetric(bakBasic?.holder_num, "户", 0);
  return holderNum || loadingText(loading);
}

function buildTotalShareText(bakBasic) {
  return formatBakMetric(bakBasic?.total_share, "亿股", 2) || "待补充";
}

function buildGrowthText(bakBasic) {
  const rev = formatBakMetric(bakBasic?.rev_yoy, "%", 1);
  const profit = formatBakMetric(bakBasic?.profit_yoy, "%", 1);
  if (rev && profit) return `${rev} / ${profit}`;
  if (rev) return `${rev} / -`;
  if (profit) return `- / ${profit}`;
  return "待补充";
}

function formatBakMetric(value, suffix = "", digits = 2) {
  if (value === null || value === undefined || value === "") return "";
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return String(value).trim();
  const text = digits <= 0 ? `${Math.round(parsed)}` : trimZeroes(parsed.toFixed(digits));
  return `${text}${suffix}`;
}

function trimZeroes(value) {
  return String(value).replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1");
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
  const aiSummary = profile.ai_summary || null;
  const sections = (Array.isArray(profile.ai_sections) && profile.ai_sections.length
    ? profile.ai_sections
    : [profile.structure, profile.emotion, profile.capacity, profile.risk])
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
      ${
        aiSummary
          ? `<p class="mxEntity">${escapeHtml(
              [aiSummary.provider || "AI", aiSummary.model || "", aiSummary.confidence ? `置信度 ${aiSummary.confidence}` : ""]
                .filter(Boolean)
                .join(" · ")
            )}</p>`
          : ""
      }
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
  renderAllBoardSelections();
  loadPickerOverview();
}

function ensureReviewLoaded() {
  if (!els.reviewDate?.value) {
    els.reviewDate.value = todayInputValue();
  }
  if (state.review.loaded) return;
  state.review.loaded = true;
  startReviewFlow(() => loadReviewOverview());
}

function ensureThemeBoardLoaded() {
  if (!els.themeBoardDate?.value) {
    els.themeBoardDate.value = todayInputValue();
  }
  if (state.themeBoard.loaded) {
    renderThemeBoard();
    return;
  }
  state.themeBoard.loaded = true;
  startThemeBoardFlow(() => loadThemeBoardOverview());
}

function ensureThemeResearchLoaded() {
  if (state.themeResearch.loaded) {
    renderThemeResearch();
    return;
  }
  state.themeResearch.loaded = true;
  renderThemeResearch();
  startThemeResearchFlow(() => loadThemeResearchHistory());
}

function ensureSystemConfigLoaded() {
  if (state.systemConfig.loaded) {
    renderSystemConfigList();
    return;
  }
  state.systemConfig.loaded = true;
  startSystemConfigFlow(() => loadSystemConfigs());
}

async function loadSystemConfigs(options = {}) {
  const requestId = ++state.systemConfig.requestId;
  toggleSystemConfigError("");
  if (els.systemConfigStatusText) {
    els.systemConfigStatusText.textContent = "正在读取系统配置表，新的接口请求会优先使用这里的启用配置。";
  }
  const data = await fetchJson("/api/system-configs");
  if (requestId !== state.systemConfig.requestId) return;
  state.systemConfig.list = Array.isArray(data.items) ? data.items : [];
  renderSystemConfigList();
  if (els.systemConfigStatusText) {
    els.systemConfigStatusText.textContent = data.enabled
      ? "数据库配置已接管 Tushare、东方财富、DeepSeek 等密钥读取。"
      : "当前未配置 MySQL，系统配置页暂时只能显示空状态。";
  }
  if (!options.keepEditing) {
    state.systemConfig.editingKey = "";
    renderSystemConfigList();
  }
}

async function loadSystemConfigDetail(configKey, options = {}) {
  const key = String(configKey || "").trim();
  if (!key) return;
  if (!options.silent) {
    toggleSystemConfigError("");
  }
  const data = await fetchJson(`/api/system-configs/${encodeURIComponent(key)}`);
  const item = data.item || null;
  if (!item) return;
  state.systemConfig.editingKey = item.config_key || key.toUpperCase();
  fillSystemConfigForm(item);
  renderSystemConfigList();
  if (options.openModal !== false) {
    openSystemConfigModal();
  }
}

function openSystemConfigModal() {
  if (!els.systemConfigModal) return;
  toggleSystemConfigError("");
  els.systemConfigModal.hidden = false;
}

function closeSystemConfigModal() {
  if (!els.systemConfigModal) return;
  els.systemConfigModal.hidden = true;
  toggleSystemConfigError("");
}

function renderSystemConfigList() {
  if (!els.systemConfigTableBox) return;
  const items = Array.isArray(state.systemConfig.list) ? state.systemConfig.list : [];
  if (els.systemConfigListMeta) {
    els.systemConfigListMeta.textContent = items.length
      ? `当前共 ${items.length} 条配置，启用项会优先覆盖环境变量；点击“编辑配置”再弹窗修改。`
      : "当前还没有系统配置，可先新建 Tushare、东方财富或 DeepSeek 密钥。";
  }
  if (!items.length) {
    els.systemConfigTableBox.innerHTML = `<div class="empty">当前还没有系统配置。</div>`;
    return;
  }
  els.systemConfigTableBox.innerHTML = `
    <table class="pickerTable systemConfigTable">
      <thead>
        <tr>
          <th>配置键</th>
          <th>分类</th>
          <th>预览</th>
          <th>状态</th>
          <th>更新时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        ${items
          .map((item) => {
            const active = state.systemConfig.editingKey && state.systemConfig.editingKey === item.config_key;
            return `
              <tr class="${active ? "is-active" : ""}">
                <td>
                  <strong>${escapeHtml(item.label || item.config_key)}</strong>
                  <p class="pickerCellSub">${escapeHtml(item.config_key || "")}</p>
                </td>
                <td>${escapeHtml(item.category || "custom")}</td>
                <td><p class="pickerCellText">${escapeHtml(item.value_preview || "-")}</p></td>
                <td>${item.is_enabled ? `<span class="pickerToneTag positive">启用</span>` : `<span class="pickerToneTag neutral">停用</span>`}</td>
                <td>${escapeHtml(item.updated_at || item.created_at || "-")}</td>
                <td>
                  <div class="pickerRowActions">
                    <button type="button" class="miniButton ghostButton" data-system-config-edit="${escapeHtml(item.config_key || "")}">编辑配置</button>
                  </div>
                </td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    </table>
  `;
}

function fillSystemConfigForm(item) {
  if (!item) {
    resetSystemConfigForm();
    return;
  }
  if (els.systemConfigFormTitle) {
    els.systemConfigFormTitle.textContent = `编辑配置 · ${item.config_key || ""}`;
  }
  if (els.systemConfigFormMeta) {
    els.systemConfigFormMeta.textContent = item.description
      ? item.description
      : "修改并保存后，新的接口请求会优先读取这条数据库配置。";
  }
  if (els.systemConfigKeyInput) {
    els.systemConfigKeyInput.value = item.config_key || "";
    els.systemConfigKeyInput.readOnly = !!item.config_key;
  }
  if (els.systemConfigLabelInput) els.systemConfigLabelInput.value = item.label || "";
  if (els.systemConfigCategoryInput) els.systemConfigCategoryInput.value = item.category || "custom";
  if (els.systemConfigDescriptionInput) els.systemConfigDescriptionInput.value = item.description || "";
  if (els.systemConfigValueInput) els.systemConfigValueInput.value = item.config_value || "";
  if (els.systemConfigSecretInput) els.systemConfigSecretInput.checked = !!item.is_secret;
  if (els.systemConfigEnabledInput) els.systemConfigEnabledInput.checked = item.is_enabled !== false;
  if (els.systemConfigDeleteBtn) {
    els.systemConfigDeleteBtn.disabled = !(item.config_key && item.source === "mysql");
  }
}

function resetSystemConfigForm() {
  state.systemConfig.editingKey = "";
  if (els.systemConfigFormTitle) els.systemConfigFormTitle.textContent = "新建配置";
  if (els.systemConfigFormMeta) els.systemConfigFormMeta.textContent = "支持新增、修改、删除系统密钥与运行参数。";
  if (els.systemConfigKeyInput) {
    els.systemConfigKeyInput.value = "";
    els.systemConfigKeyInput.readOnly = false;
  }
  if (els.systemConfigLabelInput) els.systemConfigLabelInput.value = "";
  if (els.systemConfigCategoryInput) els.systemConfigCategoryInput.value = "tushare";
  if (els.systemConfigDescriptionInput) els.systemConfigDescriptionInput.value = "";
  if (els.systemConfigValueInput) els.systemConfigValueInput.value = "";
  if (els.systemConfigSecretInput) els.systemConfigSecretInput.checked = true;
  if (els.systemConfigEnabledInput) els.systemConfigEnabledInput.checked = true;
  if (els.systemConfigDeleteBtn) els.systemConfigDeleteBtn.disabled = true;
  renderSystemConfigList();
}

function toggleSystemConfigError(message) {
  if (!els.systemConfigErrorBox) return;
  const text = String(message || "").trim();
  els.systemConfigErrorBox.hidden = !text;
  els.systemConfigErrorBox.textContent = text;
}

async function submitSystemConfigForm() {
  const configKey = String(els.systemConfigKeyInput?.value || "").trim().toUpperCase();
  if (!configKey) {
    toggleSystemConfigError("配置键不能为空。");
    return;
  }
  state.systemConfig.saving = true;
  toggleSystemConfigError("");
  try {
    const data = await fetchJson("/api/system-configs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        config_key: configKey,
        label: String(els.systemConfigLabelInput?.value || "").trim(),
        category: String(els.systemConfigCategoryInput?.value || "custom").trim(),
        description: String(els.systemConfigDescriptionInput?.value || "").trim(),
        config_value: String(els.systemConfigValueInput?.value || ""),
        is_secret: !!els.systemConfigSecretInput?.checked,
        is_enabled: !!els.systemConfigEnabledInput?.checked,
      }),
    });
    state.systemConfig.editingKey = data.item?.config_key || configKey;
    await loadSystemConfigs({ keepEditing: true });
    closeSystemConfigModal();
  } catch (err) {
    toggleSystemConfigError(err.message || "保存系统配置失败。");
  } finally {
    state.systemConfig.saving = false;
  }
}

async function deleteCurrentSystemConfig() {
  const configKey = String(state.systemConfig.editingKey || els.systemConfigKeyInput?.value || "").trim().toUpperCase();
  if (!configKey) {
    toggleSystemConfigError("当前没有可删除的配置。");
    return;
  }
  toggleSystemConfigError("");
  try {
    await fetchJson(`/api/system-configs/${encodeURIComponent(configKey)}`, { method: "DELETE" });
    resetSystemConfigForm();
    await loadSystemConfigs({ keepEditing: false });
    closeSystemConfigModal();
  } catch (err) {
    toggleSystemConfigError(err.message || "删除系统配置失败。");
  }
}

function syncPickerFiltersFromControls() {
  state.smartPicker.marketScopeFilter = els.pickerMarketScopeFilter?.value || "all";
  state.smartPicker.structureFilter = els.pickerStructureFilter?.value || "all";
  state.smartPicker.emotionFilter = els.pickerEmotionFilter?.value || "all";
  state.smartPicker.leaderFilter = els.pickerLeaderFilter?.value || "all";
  state.smartPicker.overallFilter = els.pickerOverallFilter?.value || "all";
  state.smartPicker.sortBy = els.pickerSortBy?.value || "overall_score";
  state.smartPicker.sortDirection = els.pickerSortDirection?.value || "desc";
}

function pickerOptionalNumber(input) {
  const text = String(input?.value || "").trim();
  if (!text) return "";
  const value = Number(text);
  return Number.isFinite(value) ? value : "";
}

function readPickerScreenFilters() {
  return {
    technical_shape: els.pickerTechnicalShape?.value || "all",
    market_scope: els.pickerScreenMarket?.value || "all",
    turnover_min: pickerOptionalNumber(els.pickerTurnoverMin),
    turnover_max: pickerOptionalNumber(els.pickerTurnoverMax),
    market_cap_min: pickerOptionalNumber(els.pickerMarketCapMin),
    market_cap_max: pickerOptionalNumber(els.pickerMarketCapMax),
  };
}

function pickerScreenFilterPayload() {
  const filters = readPickerScreenFilters();
  return {
    technical_shape: filters.technical_shape,
    market_scope: filters.market_scope,
    turnover_min: filters.turnover_min,
    turnover_max: filters.turnover_max,
    market_cap_min: filters.market_cap_min,
    market_cap_max: filters.market_cap_max,
  };
}

function pickerScreenFilterSummary(filters = state.smartPicker.screenFilters || {}) {
  const parts = [];
  const technicalLabels = {
    ma_bullish: "均线多头",
    laoyatou: "老鸭头",
    boll_open: "布林开口",
  };
  if (filters.technical_shape && filters.technical_shape !== "all") {
    parts.push(`技术=${technicalLabels[filters.technical_shape] || "已限定"}`);
  }
  if (filters.market_scope && filters.market_scope !== "all") {
    parts.push(`市场=${pickerMarketScopeLabel(filters.market_scope)}`);
  }
  if (filters.turnover_min !== "" && filters.turnover_min !== null && filters.turnover_min !== undefined) {
    parts.push(`换手≥${filters.turnover_min}%`);
  }
  if (filters.turnover_max !== "" && filters.turnover_max !== null && filters.turnover_max !== undefined) {
    parts.push(`换手≤${filters.turnover_max}%`);
  }
  if (filters.market_cap_min !== "" && filters.market_cap_min !== null && filters.market_cap_min !== undefined) {
    parts.push(`市值≥${filters.market_cap_min}亿`);
  }
  if (filters.market_cap_max !== "" && filters.market_cap_max !== null && filters.market_cap_max !== undefined) {
    parts.push(`市值≤${filters.market_cap_max}亿`);
  }
  return parts.join("，");
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
  const requestId = ++state.smartPicker.screenRequestId;
  const level = els.pickerLevel?.value || "daily";
  const screenFilters = pickerScreenFilterPayload();
  state.smartPicker.screenFilters = screenFilters;
  state.smartPicker.screen = { status: "loading", source_type: "watchlist" };
  state.smartPicker.detail = null;
  state.smartPicker.ai = null;
  state.smartPicker.selectedTsCode = "";
  renderPickerTable();
  renderPickerDetail();
  hidePickerError();
  setPickerStatus("正在查询东财自选，并逐只生成结构候选池...");

  try {
    const data = await fetchJson("/api/smart-picker/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_type: "watchlist",
        level,
        limit_all: true,
        ...screenFilters,
      }),
    });
    if (requestId !== state.smartPicker.screenRequestId) return;
    state.smartPicker.screen = data;
    state.smartPicker.screenFilters = data.filters || screenFilters;
    state.smartPicker.watchlist = data.watchlist || null;
    const count = (data.candidates || []).length;
    const total = data.total || data.source_total || count;
    const filterText = pickerScreenFilterSummary(data.filters || screenFilters);
    setPickerStatus(
      count
        ? `已把 ${total} 只东财自选同步到候选池，当前生成 ${count} 只结构分析${filterText ? `（${filterText}）` : ""}。`
        : `东财自选已同步，但当前没有生成可用候选${filterText ? `（${filterText}）` : ""}。`
    );
  } catch (err) {
    if (requestId !== state.smartPicker.screenRequestId) return;
    state.smartPicker.screen = { status: "error", source_type: "watchlist", message: err.message };
    state.smartPicker.watchlist = { status: "error", message: err.message, items: [] };
    showPickerError(err.message);
  }

  renderPickerTable();
  renderPickerDetail();
}

function pickerScopeSummary(boardFilters = []) {
  return boardFilters
    .filter((item) => item?.name)
    .map((item) => `${item.source_label || "板块"}${item.idx_type || "板块"}“${item.name}”`)
    .join(" + ");
}

function pickerModeSummary(mode, boardFilters = []) {
  const labels = {
    condition: "条件筛选",
    dc: "东方财富板块",
    tdx: "通达信板块",
    ths: "同花顺板块",
    combined: "组合筛选",
  };
  const scope = pickerScopeSummary(boardFilters);
  if (scope && mode === "combined") {
    return `${labels[mode]}：${scope}`;
  }
  if (scope) {
    return `${labels[mode]}：${scope}`;
  }
  return labels[mode] || "智能选股";
}

async function normalizePickerBoardSource(source, silent = false) {
  const dom = pickerBoardDom(source);
  if (!dom) return null;
  const query = dom.input?.value.trim() || "";
  const selected = state.smartPicker[dom.stateKey];
  if (!query && !selected) {
    state.smartPicker[dom.stateKey] = null;
    renderPickerBoardSelection(source);
    return null;
  }
  if (query && !(state.smartPicker[dom.matchesKey] || []).length) {
    await searchPickerBoards(source, query, silent);
  }
  const picked = ensurePickerBoardSelection(source, query || selected?.name || selected?.ts_code || "");
  if (!picked && !silent) {
    showPickerError(`请输入有效的${dom.label}板块或概念。`);
  }
  return picked;
}

function pickerBoardRequestPayload(source, board) {
  if (!board) return {};
  if (source === "dc") {
    return {
      board_ts_code: board.ts_code || "",
      board_name: board.name || "",
      board_type: board.type_key || boardTypeApiValue("dc", els.pickerBoardType?.value || "all"),
    };
  }
  if (source === "tdx") {
    return {
      tdx_board_ts_code: board.ts_code || "",
      tdx_board_name: board.name || "",
      tdx_board_type: board.type_key || boardTypeApiValue("tdx", els.pickerTdxType?.value || "all"),
    };
  }
  return {
    ths_board_ts_code: board.ts_code || "",
    ths_board_name: board.name || "",
    ths_board_type: board.type_key || boardTypeApiValue("ths", els.pickerThsType?.value || "all"),
  };
}

async function runSmartPicker(mode = "combined") {
  const queryText = els.pickerQueryInput?.value.trim() || "";
  const screenFilters = pickerScreenFilterPayload();
  state.smartPicker.screenFilters = screenFilters;
  const payload = {
    query_text: "",
    level: els.pickerLevel?.value || "daily",
    limit: Number(els.pickerLimit?.value || 20),
    ...screenFilters,
  };
  const selectedBoards = [];

  if (mode === "condition" || mode === "combined") {
    if (queryText) {
      payload.query_text = queryText;
    } else if (mode === "condition") {
      hidePickerError();
      setPickerStatus("条件查询未填写时不会执行。你也可以单独使用东方财富、通达信或同花顺板块查询。");
      return;
    }
  }

  for (const source of ["dc", "tdx", "ths"]) {
    const shouldHandle = mode === "combined" || mode === source;
    if (!shouldHandle) continue;
    const board = await normalizePickerBoardSource(source, false);
    if (mode === source && !board) {
      return;
    }
    if (board) {
      selectedBoards.push(board);
      Object.assign(payload, pickerBoardRequestPayload(source, board));
    }
  }

  const hasQuery = Boolean(payload.query_text);
  const hasBoard = selectedBoards.length > 0;
  if (!hasQuery && !hasBoard) {
    hidePickerError();
    setPickerStatus("当前还没有选择任何查询来源。条件、东方财富、通达信、同花顺都可以单独查询，也可以组合筛选。");
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
  setPickerStatus(`正在执行${pickerModeSummary(mode, selectedBoards)}，并结合缠论结构生成候选池...`);

  try {
    const data = await fetchJson("/api/smart-picker/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (requestId !== state.smartPicker.screenRequestId) return;
    state.smartPicker.screen = data;
    state.smartPicker.screenFilters = data.filters || screenFilters;
    const count = (data.candidates || []).length;
    const marketTotal = data.universe?.total ? `全市场 ${data.universe.total} 只股票里` : "全市场里";
    const scopeSummary = pickerScopeSummary(data.board_filters || selectedBoards);
    const prefix = scopeSummary ? `${scopeSummary} 已载入；` : "";
    const filterText = pickerScreenFilterSummary(data.filters || screenFilters);
    setPickerStatus(
      count
        ? `${prefix}已从 ${marketTotal} 生成 ${count} 只结构候选${filterText ? `（${filterText}）` : ""}，先按排序和筛选缩小观察范围。`
        : `${prefix}筛选已完成，但当前条件下没有生成可用候选${filterText ? `（${filterText}）` : ""}。`
    );
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
    if (state.smartPicker.screen?.source_type === "watchlist") {
      await loadPickerWatchlist();
    }
    if (state.smartPicker.detail?.stock) {
      await loadPickerCandidateDetail(state.smartPicker.detail.stock);
    }
  } catch (err) {
    showPickerError(err.message);
  }
}

function visiblePickerCandidates() {
  return filterAndSortPickerCandidates(state.smartPicker.screen?.candidates || []);
}

function buildPickerEastmoneyTargetsText() {
  const names = visiblePickerCandidates()
    .map((item) => String(item.stock?.name || "").trim())
    .filter(Boolean);
  return Array.from(new Set(names)).join("\n");
}

function setPickerEastmoneyFeedback(message, tone = "neutral") {
  if (!els.pickerEastmoneyFeedback) return;
  els.pickerEastmoneyFeedback.className = `pickerEastmoneyFeedback tone-${tone}`;
  els.pickerEastmoneyFeedback.textContent = message || "还没执行操作。";
}

function openPickerEastmoneyModal() {
  if (!els.pickerEastmoneyModal) return;
  const candidates = visiblePickerCandidates();
  const targetsText = buildPickerEastmoneyTargetsText();
  if (els.pickerEastmoneyTargetsInput) {
    els.pickerEastmoneyTargetsInput.value = targetsText;
  }
  if (els.pickerEastmoneyModalMeta) {
    els.pickerEastmoneyModalMeta.textContent = candidates.length
      ? `已按当前候选池筛选结果预填 ${candidates.length} 只股票；可直接批量加入东财自选或删除默认自选。`
      : "当前候选池暂无可批量处理的股票，你也可以手动输入名称或代码。";
  }
  setPickerEastmoneyFeedback(candidates.length ? "已预填当前筛选后的股票列表。" : "当前没有筛选结果，等你手动输入。");
  els.pickerEastmoneyModal.hidden = false;
  document.body.classList.add("modalOpen");
  window.setTimeout(() => {
    if (els.pickerEastmoneyTargetsInput) {
      els.pickerEastmoneyTargetsInput.focus();
      els.pickerEastmoneyTargetsInput.select();
    }
  }, 0);
}

function openPickerEastmoneyModalWithLoading() {
  return startSmartPickerFlow(async () => {
    await new Promise((resolve) => window.setTimeout(resolve, 120));
    openPickerEastmoneyModal();
  });
}

function closePickerEastmoneyModal() {
  if (!els.pickerEastmoneyModal) return;
  els.pickerEastmoneyModal.hidden = true;
  document.body.classList.remove("modalOpen");
}

async function submitPickerEastmoneyBatch(action) {
  const targetsText = els.pickerEastmoneyTargetsInput?.value || "";
  if (!String(targetsText).trim()) {
    setPickerEastmoneyFeedback("先填股票名称或代码，再执行批量操作。", "caution");
    return;
  }

  const buttons = els.pickerEastmoneyForm?.querySelectorAll("button") || [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  setPickerEastmoneyFeedback(
    action === "add_group" ? "正在批量加入东方财富自选..." : "正在批量删除东方财富自选..."
  );
  hidePickerError();
  try {
    const data = await fetchJson("/api/smart-picker/eastmoney-batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        group_name: "",
        targets_text: targetsText,
      }),
    });
    const tone = data.status === "ok" ? "positive" : data.status === "partial" ? "neutral" : "caution";
    const failed = (data.results || [])
      .filter((item) => item.status !== "ok")
      .map((item) => `${item.target}：${item.message}`)
      .slice(0, 6);
    setPickerEastmoneyFeedback(
      failed.length ? `${data.message}\n失败明细：\n${failed.join("\n")}` : data.message || "操作完成。",
      tone
    );
  } catch (err) {
    setPickerEastmoneyFeedback(err.message || "东方财富批量自选操作失败。", "caution");
    showPickerError(err.message);
  } finally {
    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

function openCandidateInAnalysis(stock, options = {}) {
  if (!stock) return;
  state.selectedStock = { ts_code: stock.ts_code };
  els.stockInput.value = `${stock.name} ${stock.symbol}`;
  setAnalysisLevel(els.pickerLevel?.value || "daily");
  const loadingText = options.loadingText || "智能分析中";
  switchMainPage("analysisPage");
  startAnalysisFlow({ loadingText });
}

function openReviewStockInAnalysis(rowOrPayload, options = {}) {
  const row = rowOrPayload || {};
  const tsCode = resolveReviewStockCode(row);
  const name = String(row.name || row.exalter || row.query_name || "").trim();
  const loadingText = options.loadingText || "智能分析中";
  if (tsCode) {
    const symbol = String(tsCode).split(".")[0] || "";
    openCandidateInAnalysis({
      ts_code: tsCode,
      name: name || symbol,
      symbol,
    }, { loadingText });
    return;
  }
  if (!name) return;
  state.selectedStock = null;
  els.stockInput.value = name;
  setAnalysisLevel(els.pickerLevel?.value || "daily");
  switchMainPage("analysisPage");
  startAnalysisFlow({ loadingText });
}

function resolveReviewStockCode(row) {
  if (!row) return "";
  return String(row.ts_code || row.code || row.con_code || row.symbol || "").trim();
}

async function ensureWatchtowerLoaded() {
  if (state.watchtower.loaded && state.watchtower.overview) {
    renderWatchtower();
    return;
  }
  await loadWatchtowerOverview(1);
}

async function loadWatchtowerOverview(page = 1) {
  state.watchtower.requestId += 1;
  const requestId = state.watchtower.requestId;
  state.watchtower.page = Math.max(1, intValue(page) || 1);
  state.watchtower.query = els.watchtowerQueryInput?.value.trim() || state.watchtower.query || "";
  hideWatchtowerError();
  if (els.watchtowerStatusText) {
    els.watchtowerStatusText.textContent = "正在按数据库自选股加载盯盘列表与实时日线。";
  }
  if (els.watchtowerSummaryBox) {
    els.watchtowerSummaryBox.innerHTML = `
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div></article>
    `;
  }
  if (els.watchtowerTableBox) {
    els.watchtowerTableBox.innerHTML = `<div class="empty">正在加载智能盯盘列表...</div>`;
  }
  try {
    const params = new URLSearchParams({
      q: state.watchtower.query,
      page: String(state.watchtower.page),
      page_size: "12",
    });
    const data = await fetchJson(`/api/watchtower/overview?${params.toString()}`);
    if (requestId !== state.watchtower.requestId) return;
    state.watchtower.overview = data;
    state.watchtower.loaded = true;
    renderWatchtower();
  } catch (err) {
    if (requestId !== state.watchtower.requestId) return;
    state.watchtower.overview = null;
    showWatchtowerError(err.message);
    if (els.watchtowerSummaryBox) {
      els.watchtowerSummaryBox.innerHTML = "";
    }
    if (els.watchtowerTableBox) {
      els.watchtowerTableBox.innerHTML = `<div class="empty">智能盯盘加载失败。</div>`;
    }
  }
}

function renderWatchtower() {
  renderWatchtowerSummary();
  renderWatchtowerTable();
  renderWatchtowerGuide();
}

function renderWatchtowerSummary() {
  if (!els.watchtowerSummaryBox) return;
  const overview = state.watchtower.overview;
  if (!overview || overview.status !== "ok") {
    els.watchtowerSummaryBox.innerHTML = `<article class="reviewStatCard"><span>智能盯盘</span><strong>--</strong><p>等待数据库自选股加载。</p></article>`;
    return;
  }
  const summary = overview.summary || {};
  const cards = [
    { label: "数据库自选", value: intValue(summary.total), note: "数据库里当前可盯的自选股数量" },
    { label: "主流先手", value: intValue(summary.strong_count), note: "强于昨收且日内收在高位附近" },
    { label: "分歧承接", value: intValue(summary.absorb_count), note: "盘中有分歧，但承接还在" },
    { label: "兑现回避", value: intValue(summary.risk_count), note: summary.realtime_error || "收弱或日内回落明显，先别硬接" },
  ];
  els.watchtowerSummaryBox.innerHTML = cards
    .map(
      (card) => `
        <article class="reviewStatCard">
          <span>${escapeHtml(card.label)}</span>
          <strong>${escapeHtml(String(card.value))}</strong>
          <p>${escapeHtml(card.note)}</p>
        </article>
      `
    )
    .join("");
  if (els.watchtowerStatusText) {
    els.watchtowerStatusText.textContent = summary.headline || "先盯强承接，再看弱转强。";
  }
}

function renderWatchtowerTable() {
  if (!els.watchtowerTableBox || !els.watchtowerResultMeta || !els.watchtowerTableStatus) return;
  const overview = state.watchtower.overview;
  if (!overview || overview.status !== "ok") {
    els.watchtowerTableStatus.textContent = "等待智能盯盘数据。";
    els.watchtowerResultMeta.textContent = "还没有可展示的数据库自选股。";
    els.watchtowerTableBox.innerHTML = `<div class="empty">等待智能盯盘数据。</div>`;
    return;
  }
  const items = overview.items || [];
  els.watchtowerTableStatus.textContent = state.watchtower.lastEastmoneyMessage || overview.summary?.action || "先看强弱，再看承接。";
  els.watchtowerResultMeta.textContent = `匹配 ${intValue(overview.total)} 只 · 第 ${intValue(overview.page)} / ${intValue(overview.total_pages)} 页`;
  if (!items.length) {
    els.watchtowerTableBox.innerHTML = `<div class="empty">当前没有匹配的数据库自选股。</div>`;
    return;
  }

  els.watchtowerTableBox.innerHTML = `
    <div class="watchtowerTable">
      ${items.map((item) => renderWatchtowerRow(item)).join("")}
    </div>
    ${renderWatchtowerPager(overview)}
  `;
}

function renderWatchtowerRow(item) {
  const stock = item.stock || {};
  const realtime = item.realtime || {};
  const cache = item.cache || {};
  const yangjia = item.yangjia || {};
  const tsCode = String(stock.ts_code || "").trim();
  const syncing = state.watchtower.syncingEastmoneyTsCode === tsCode;
  const synced = state.watchtower.lastEastmoneyTsCode === tsCode;
  const eastmoneyLabel = syncing ? "加入中" : synced ? "已加入东财" : "加入东财";
  const tradeTime = realtime.trade_time ? ` · ${escapeHtml(realtime.trade_time)}` : "";
  return `
    <article class="watchtowerRow">
      <div class="watchtowerStockCol">
        <button type="button" class="watchtowerStockButton" data-watchtower-open="1" data-ts-code="${escapeHtml(stock.ts_code || "")}">
          <strong>${escapeHtml(stock.name || stock.symbol || stock.ts_code || "-")}</strong>
          <span>${escapeHtml(stock.ts_code || "")} · ${escapeHtml(stock.industry || cache.industry || "行业待补充")}</span>
        </button>
        <small>${escapeHtml(stock.area || "区域待补充")} · ${escapeHtml(stock.market || "市场待补充")}</small>
      </div>
      <div class="watchtowerSignalCol">
        <span class="watchtowerBadge tone-${escapeHtml(yangjia.tone || "neutral")}">${escapeHtml(yangjia.label || "轮动观察")}</span>
        <strong>${escapeHtml(yangjia.action || "先看，不追。")}</strong>
        <p>${escapeHtml(yangjia.summary || "")}</p>
      </div>
      <div class="watchtowerRealtimeCol">
        <strong>${formatPrice(realtime.close)}</strong>
        <span class="${Number(realtime.day_pct || 0) >= 0 ? "textSell" : "textBuy"}">${formatSignedPercentValue(realtime.day_pct)}</span>
        <small>开 ${formatSignedPercentValue(realtime.open_pct)} · 振幅 ${formatSignedPercentValue(realtime.amplitude_pct)}${tradeTime}</small>
      </div>
      <div class="watchtowerCacheCol">
        <strong>PE / PB ${formatCompactValue(cache.pe)} / ${formatCompactValue(cache.pb)}</strong>
        <span>股东 ${formatHolderCount(cache.holder_num)} · 总股本 ${formatCompactShare(cache.total_share)}</span>
        <small>营收 / 利润同比 ${formatSignedCompact(cache.rev_yoy)} / ${formatSignedCompact(cache.profit_yoy)}</small>
      </div>
      <div class="watchtowerActionCol">
        <button type="button" class="ghostButton miniButton" data-watchtower-open="1" data-ts-code="${escapeHtml(tsCode)}">实时日线</button>
        <button type="button" class="ghostButton miniButton accentButton" data-watchtower-eastmoney-add="1" data-ts-code="${escapeHtml(tsCode)}" ${syncing ? "disabled" : ""}>${escapeHtml(eastmoneyLabel)}</button>
        <button type="button" class="ghostButton miniButton" data-watchtower-analysis="1" data-ts-code="${escapeHtml(tsCode)}" data-name="${escapeHtml(stock.name || "")}" data-symbol="${escapeHtml(stock.symbol || "")}">股票分析</button>
        <button type="button" class="ghostButton miniButton dangerButton" data-watchtower-delete="1" data-ts-code="${escapeHtml(tsCode)}">删除</button>
      </div>
    </article>
  `;
}

function renderWatchtowerPager(overview) {
  const total = intValue(overview.total);
  const totalPages = intValue(overview.total_pages);
  const page = intValue(overview.page);
  const pageSize = intValue(overview.page_size) || 12;
  if (!total || totalPages <= 1) return "";
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(total, page * pageSize);
  return `
    <div class="reviewPager">
      <small>第 ${page} / ${totalPages} 页 · 显示 ${start}-${end} / ${total}</small>
      <div class="reviewPagerActions">
        <button type="button" class="ghostButton miniButton" data-watchtower-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>上一页</button>
        <button type="button" class="ghostButton miniButton" data-watchtower-page="${page + 1}" ${page >= totalPages ? "disabled" : ""}>下一页</button>
      </div>
    </div>
  `;
}

function renderWatchtowerGuide() {
  if (!els.watchtowerGuideBox) return;
  const summary = state.watchtower.overview?.summary || {};
  els.watchtowerGuideBox.className = "watchtowerGuideStack";
  els.watchtowerGuideBox.innerHTML = `
    <article class="reviewFocusItem reviewFocusHero">
      <div class="reviewFocusHeroHeader">
        <strong>今天先盯什么</strong>
        <span class="reviewBadge">${escapeHtml(summary.strong_count || 0)} 强 / ${escapeHtml(summary.absorb_count || 0)} 承接</span>
      </div>
      <p>${escapeHtml(summary.headline || "先看最强，再看分歧承接。")}</p>
      <div class="reviewBulletListWrap">
        <ul class="reviewBulletList">
          <li>${escapeHtml(summary.action || "先看强票和承接。")}</li>
          <li>养家视角先问有没有主流、有没有承接，再问是不是值得出手。</li>
          <li>后排、缩量、收弱的票先别脑补成龙头。</li>
        </ul>
      </div>
      ${summary.realtime_error ? `<p class="watchtowerWarnText">实时日线提示：${escapeHtml(summary.realtime_error)}</p>` : ""}
    </article>
  `;
}

function showWatchtowerError(message) {
  if (!els.watchtowerErrorBox) return;
  els.watchtowerErrorBox.hidden = false;
  els.watchtowerErrorBox.textContent = message;
}

function hideWatchtowerError() {
  if (!els.watchtowerErrorBox) return;
  els.watchtowerErrorBox.hidden = true;
  els.watchtowerErrorBox.textContent = "";
}

async function openWatchtowerRealtimeModal(tsCode) {
  if (!tsCode || !els.watchtowerModal || !els.watchtowerModalBody) return;
  state.watchtower.modalRequestId += 1;
  const requestId = state.watchtower.modalRequestId;
  state.watchtower.modalDetail = null;
  els.watchtowerModalTitle.textContent = "实时日线";
  els.watchtowerModalMeta.textContent = "正在拉取 rt_k 实时日线...";
  els.watchtowerModalBody.innerHTML = `<div class="empty">正在加载实时日线...</div>`;
  els.watchtowerModal.hidden = false;
  document.body.classList.add("modalOpen");
  try {
    const data = await fetchJson(`/api/watchtower/realtime?ts_code=${encodeURIComponent(tsCode)}`);
    if (requestId !== state.watchtower.modalRequestId) return;
    state.watchtower.modalDetail = data;
    renderWatchtowerModalDetail();
  } catch (err) {
    if (requestId !== state.watchtower.modalRequestId) return;
    els.watchtowerModalTitle.textContent = "实时日线";
    els.watchtowerModalMeta.textContent = "实时日线加载失败";
    els.watchtowerModalBody.innerHTML = `<div class="empty">${escapeHtml(err.message)}</div>`;
  }
}

async function addWatchtowerStockToEastmoney(tsCode) {
  const cleanedCode = String(tsCode || "").trim();
  if (!cleanedCode || state.watchtower.syncingEastmoneyTsCode === cleanedCode) return;
  state.watchtower.syncingEastmoneyTsCode = cleanedCode;
  state.watchtower.lastEastmoneyMessage = "";
  renderWatchtowerTable();
  hideWatchtowerError();
  try {
    const data = await fetchJson("/api/watchtower/eastmoney-add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      timeoutMs: 12000,
      timeoutMessage: "加入东方财富自选超时，请稍后重试。",
      body: JSON.stringify({ ts_code: cleanedCode }),
    });
    state.watchtower.lastEastmoneyTsCode = cleanedCode;
    state.watchtower.lastEastmoneyMessage = data.message || "已加入东方财富重点监控。";
    if (els.watchtowerStatusText) {
      els.watchtowerStatusText.textContent = state.watchtower.lastEastmoneyMessage;
    }
  } catch (err) {
    showWatchtowerError(err.message);
  } finally {
    state.watchtower.syncingEastmoneyTsCode = "";
    renderWatchtowerTable();
  }
}

function renderWatchtowerModalDetail() {
  if (!els.watchtowerModalBody || !els.watchtowerModalTitle || !els.watchtowerModalMeta) return;
  const detail = state.watchtower.modalDetail;
  if (!detail || detail.status !== "ok") {
    els.watchtowerModalBody.innerHTML = `<div class="empty">实时日线暂无数据。</div>`;
    return;
  }
  const stock = detail.stock || {};
  const realtime = detail.realtime || {};
  const yangjia = detail.yangjia || {};
  const cache = detail.cache || {};
  els.watchtowerModalTitle.textContent = `${stock.name || stock.symbol || stock.ts_code || "实时日线"} · ${stock.ts_code || ""}`;
  els.watchtowerModalMeta.textContent = detail.realtime_error
    ? `实时日线降级展示 · ${detail.realtime_error}`
    : `实时日线 · ${realtime.trade_time || "当日最新"} · 养家视角`;
  els.watchtowerModalBody.innerHTML = `
    <section class="watchtowerModalGrid">
      <article class="watchtowerRealtimeHero tone-${escapeHtml(yangjia.tone || "neutral")}">
        <div class="watchtowerRealtimeHeadline">
          <div>
            <span class="watchtowerBadge tone-${escapeHtml(yangjia.tone || "neutral")}">${escapeHtml(yangjia.label || "轮动观察")}</span>
            <h3>${escapeHtml(yangjia.action || "先看，不追。")}</h3>
            <p>${escapeHtml(yangjia.summary || "")}</p>
          </div>
          <div class="watchtowerRealtimePrice">
            <strong>${formatPrice(realtime.close)}</strong>
            <span class="${Number(realtime.day_pct || 0) >= 0 ? "textSell" : "textBuy"}">${formatSignedPercentValue(realtime.day_pct)}</span>
          </div>
        </div>
        <div class="watchtowerRealtimeCanvas">
          ${renderWatchtowerCandleSvg(realtime)}
        </div>
      </article>
      <article class="watchtowerRealtimeStats">
        <h3>实时日线</h3>
        <dl class="miniStats watchtowerMetricList">
          <dt>昨收</dt><dd>${formatPrice(realtime.pre_close)}</dd>
          <dt>今开</dt><dd>${formatPrice(realtime.open)}</dd>
          <dt>最高</dt><dd>${formatPrice(realtime.high)}</dd>
          <dt>最低</dt><dd>${formatPrice(realtime.low)}</dd>
          <dt>成交量</dt><dd>${formatVolumeHand(realtime.vol)}</dd>
          <dt>成交额</dt><dd>${formatAmountYi(realtime.amount)}</dd>
          <dt>成交笔数</dt><dd>${formatPlainNumber(realtime.num)}</dd>
          <dt>时间</dt><dd>${escapeHtml(realtime.trade_time || "--")}</dd>
          <dt>买一</dt><dd>${formatPrice(realtime.bid_price1)} / ${formatPlainNumber(realtime.bid_volume1)}</dd>
          <dt>卖一</dt><dd>${formatPrice(realtime.ask_price1)} / ${formatPlainNumber(realtime.ask_volume1)}</dd>
        </dl>
      </article>
      <article class="watchtowerRealtimeStats">
        <h3>基础资料快照</h3>
        <dl class="miniStats watchtowerMetricList">
          <dt>行业</dt><dd>${escapeHtml(stock.industry || cache.industry || "--")}</dd>
          <dt>地区</dt><dd>${escapeHtml(stock.area || cache.area || "--")}</dd>
          <dt>PE / PB</dt><dd>${formatCompactValue(cache.pe)} / ${formatCompactValue(cache.pb)}</dd>
          <dt>股东人数</dt><dd>${formatHolderCount(cache.holder_num)}</dd>
          <dt>总股本</dt><dd>${formatCompactShare(cache.total_share)}</dd>
          <dt>营收同比</dt><dd>${formatSignedCompact(cache.rev_yoy)}</dd>
          <dt>利润同比</dt><dd>${formatSignedCompact(cache.profit_yoy)}</dd>
          <dt>快照日期</dt><dd>${formatDate(cache.trade_date || "")}</dd>
        </dl>
      </article>
      <article class="watchtowerRealtimeStats wide">
        <h3>养家盯盘依据</h3>
        <ul class="reviewBulletList">
          ${(yangjia.basis || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          <li>${escapeHtml(yangjia.risk || "先看承接，再看有没有必要动手。")}</li>
        </ul>
      </article>
    </section>
  `;
}

function renderWatchtowerCandleSvg(realtime) {
  const open = Number(realtime.open || 0);
  const high = Number(realtime.high || 0);
  const low = Number(realtime.low || 0);
  const close = Number(realtime.close || 0);
  const preClose = Number(realtime.pre_close || 0);
  const valid = high > 0 && low > 0 && close > 0 && open > 0 && preClose > 0;
  if (!valid) {
    return `<div class="empty">暂无可绘制的实时日线。</div>`;
  }
  const top = Math.max(high, preClose, open, close);
  const bottom = Math.min(low, preClose, open, close);
  const span = Math.max(top - bottom, top * 0.01);
  const projectY = (value) => 18 + ((top - value) / span) * 184;
  const yHigh = projectY(high);
  const yLow = projectY(low);
  const yOpen = projectY(open);
  const yClose = projectY(close);
  const bodyTop = Math.min(yOpen, yClose);
  const bodyHeight = Math.max(8, Math.abs(yOpen - yClose));
  const rising = close >= open;
  const color = rising ? "#d91c1c" : "#15803d";
  const preCloseY = projectY(preClose);
  return `
    <svg viewBox="0 0 180 220" class="watchtowerCandleSvg" role="img" aria-label="实时日线">
      <line x1="90" y1="${yHigh.toFixed(2)}" x2="90" y2="${yLow.toFixed(2)}" stroke="${color}" stroke-width="6" stroke-linecap="round"></line>
      <rect x="58" y="${bodyTop.toFixed(2)}" width="64" height="${bodyHeight.toFixed(2)}" rx="12" fill="${color}" opacity="0.92"></rect>
      <line x1="26" y1="${preCloseY.toFixed(2)}" x2="154" y2="${preCloseY.toFixed(2)}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5 5"></line>
      <text x="20" y="20" font-size="12" fill="#64748b">高 ${formatPrice(high)}</text>
      <text x="20" y="212" font-size="12" fill="#64748b">低 ${formatPrice(low)}</text>
      <text x="20" y="${Math.max(34, preCloseY - 8).toFixed(2)}" font-size="12" fill="#64748b">昨收 ${formatPrice(preClose)}</text>
    </svg>
  `;
}

function closeWatchtowerModal() {
  if (!els.watchtowerModal) return;
  els.watchtowerModal.hidden = true;
  document.body.classList.remove("modalOpen");
}

async function deleteWatchtowerStock(tsCode) {
  if (!tsCode) return;
  try {
    await fetchJson("/api/watchtower/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ts_code: tsCode }),
    });
    await loadWatchtowerOverview(state.watchtower.page || 1);
    if (state.analysis?.stock?.ts_code === tsCode) {
      state.analysisWatchlist = { status: "idle", message: "" };
      renderAnalysisWatchlistAction();
    }
  } catch (err) {
    showWatchtowerError(err.message);
  }
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

function setReviewStatus(message) {
  if (els.reviewStatusText) {
    els.reviewStatusText.textContent = message;
  }
}

function showReviewError(message) {
  if (!els.reviewErrorBox) return;
  els.reviewErrorBox.textContent = message;
  els.reviewErrorBox.hidden = false;
}

function hideReviewError() {
  if (!els.reviewErrorBox) return;
  els.reviewErrorBox.hidden = true;
  els.reviewErrorBox.textContent = "";
}

function setThemeResearchStatus(message) {
  if (els.themeResearchStatusText) {
    els.themeResearchStatusText.textContent = message;
  }
}

function showThemeResearchError(message) {
  if (!els.themeResearchErrorBox) return;
  els.themeResearchErrorBox.textContent = message;
  els.themeResearchErrorBox.hidden = false;
}

function hideThemeResearchError() {
  if (!els.themeResearchErrorBox) return;
  els.themeResearchErrorBox.hidden = true;
  els.themeResearchErrorBox.textContent = "";
}

function closeThemeResearchStream() {
  if (state.themeResearch.stream) {
    state.themeResearch.stream.close();
    state.themeResearch.stream = null;
  }
}

async function loadThemeResearchHistory(options = {}) {
  const requestId = ++state.themeResearch.historyRequestId;
  const page = Math.max(1, intValue(options.page ?? state.themeResearch.historyPage) || 1);
  const pageSize = Math.max(1, intValue(options.pageSize ?? state.themeResearch.historyPageSize) || 6);
  if (!options.silent) {
    hideThemeResearchError();
    setThemeResearchStatus("正在读取最近的题材研究报告...");
  }
  try {
    const data = await fetchJson(`/api/theme-research/reports?page=${page}&page_size=${pageSize}&limit=${pageSize}`, {
      timeoutMs: 15000,
      timeoutMessage: "题材研究历史加载超时，请稍后重试。",
    });
    if (requestId !== state.themeResearch.historyRequestId) return;
    state.themeResearch.history = Array.isArray(data.items) ? data.items : [];
    state.themeResearch.historyPage = intValue(data.page) || page;
    state.themeResearch.historyPageSize = intValue(data.page_size) || pageSize;
    state.themeResearch.historyTotal = intValue(data.total);
    state.themeResearch.historyTotalPages = intValue(data.total_pages) || 1;
    state.themeResearch.historyLoaded = true;
    renderThemeResearchHistory();
    if (!options.silent && !state.themeResearch.currentTaskId) {
      setThemeResearchStatus(
        state.themeResearch.history.length
          ? "已加载最近题材研究历史，可直接点开历史报告，也可以重新发起新调研。"
          : "当前还没有历史题材研究报告，输入题材后可直接开始调研。"
      );
    }
  } catch (err) {
    if (requestId !== state.themeResearch.historyRequestId) return;
    state.themeResearch.history = [];
    state.themeResearch.historyPage = page;
    state.themeResearch.historyPageSize = pageSize;
    state.themeResearch.historyTotal = 0;
    state.themeResearch.historyTotalPages = 1;
    state.themeResearch.historyLoaded = true;
    showThemeResearchError(err.message);
    renderThemeResearchHistory();
  }
}

async function loadThemeResearchReport(taskId, options = {}) {
  const cleanTaskId = String(taskId || "").trim();
  if (!cleanTaskId) return;
  const requestId = ++state.themeResearch.reportRequestId;
  if (!options.keepEvents) {
    state.themeResearch.events = [];
  }
  if (!options.silent) {
    hideThemeResearchError();
    setThemeResearchStatus(`正在读取题材研究报告 ${cleanTaskId}...`);
  }
  try {
    const data = await fetchJson(`/api/theme-research/report/${encodeURIComponent(cleanTaskId)}`, {
      timeoutMs: 18000,
      timeoutMessage: "题材研究报告加载超时，请稍后重试。",
    });
    if (requestId !== state.themeResearch.reportRequestId) return;
    state.themeResearch.currentTaskId = cleanTaskId;
    state.themeResearch.currentThemeName = data.theme_name || state.themeResearch.currentThemeName || "";
    state.themeResearch.reportPayload = data;
    state.themeResearch.loading = false;
    renderThemeResearch();
    if (!options.silent) {
      setThemeResearchStatus(`已打开 ${data.theme_name || cleanTaskId} 的题材研究报告。`);
    }
  } catch (err) {
    if (requestId !== state.themeResearch.reportRequestId) return;
    state.themeResearch.loading = false;
    showThemeResearchError(err.message);
    renderThemeResearch();
  }
}

async function startThemeResearchTask() {
  const themeName = String(els.themeResearchInput?.value || "").trim();
  if (!themeName) {
    showThemeResearchError("请输入行业、题材或概念名称。");
    return;
  }
  hideThemeResearchError();
  closeThemeResearchStream();
  state.themeResearch.loading = true;
  state.themeResearch.currentTaskId = "";
  state.themeResearch.currentThemeName = themeName;
  state.themeResearch.events = [];
  state.themeResearch.reportPayload = null;
  renderThemeResearch();
  setThemeResearchStatus(`正在创建“${themeName}”的题材研究任务...`);
  const payload = {
    theme_name: themeName,
    market: els.themeResearchMarket?.value || "A股",
    analysis_depth: els.themeResearchDepth?.value || "standard",
    time_horizon: els.themeResearchHorizon?.value || "短中线",
  };
  try {
    const data = await fetchJson("/api/theme-research/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      timeoutMs: 15000,
      timeoutMessage: "题材研究任务创建超时，请稍后重试。",
    });
    state.themeResearch.currentTaskId = data.task_id || "";
    setThemeResearchStatus(`题材研究任务已创建：${state.themeResearch.currentTaskId}，正在建立实时调研流...`);
    renderThemeResearch();
    openThemeResearchStream(state.themeResearch.currentTaskId);
  } catch (err) {
    state.themeResearch.loading = false;
    showThemeResearchError(err.message);
    renderThemeResearch();
  }
}

function openThemeResearchStream(taskId) {
  const cleanTaskId = String(taskId || "").trim();
  if (!cleanTaskId) return;
  if (typeof EventSource === "undefined") {
    state.themeResearch.loading = false;
    showThemeResearchError("当前浏览器不支持 SSE，无法实时查看题材研究进度。");
    renderThemeResearch();
    return;
  }
  closeThemeResearchStream();
  const stream = new EventSource(`/api/theme-research/stream/${encodeURIComponent(cleanTaskId)}`);
  state.themeResearch.stream = stream;
  const handlePayload = (payload) => {
    if (!payload || (payload.task_id && payload.task_id !== state.themeResearch.currentTaskId)) return;
    upsertThemeResearchEvent(payload);
    if (payload.message) {
      setThemeResearchStatus(payload.message);
    }
    if (payload.event_type === "final_report") {
      state.themeResearch.loading = false;
      state.themeResearch.reportPayload = {
        task_id: cleanTaskId,
        theme_name: state.themeResearch.currentThemeName,
        status: "completed",
        report: payload.report || {},
        created_at: payload.created_at || "",
        updated_at: payload.created_at || "",
      };
      renderThemeResearch();
      void loadThemeResearchReport(cleanTaskId, { silent: true, keepEvents: true });
      void loadThemeResearchHistory({ silent: true, page: state.themeResearch.historyPage || 1 });
      return;
    }
    if (payload.event_type === "task_failed") {
      state.themeResearch.loading = false;
      if (payload.message) {
        showThemeResearchError(payload.message);
      }
    }
    renderThemeResearch();
  };
  [
    "task_started",
    "step_update",
    "tool_call_started",
    "tool_call_finished",
    "tool_call_failed",
    "data_preview",
    "final_report",
    "task_failed",
  ].forEach((eventName) => {
    stream.addEventListener(eventName, (event) => {
      try {
        const payload = JSON.parse(event.data || "{}");
        handlePayload(payload);
      } catch (err) {
        showThemeResearchError(`题材研究流解析失败：${err.message}`);
      }
    });
  });
  stream.onerror = () => {
    const completed = Boolean(state.themeResearch.reportPayload?.report);
    const failed = state.themeResearch.events.some((item) => item.event_type === "task_failed");
    if (completed || failed || stream.readyState === EventSource.CLOSED) {
      closeThemeResearchStream();
      state.themeResearch.loading = false;
      renderThemeResearch();
      return;
    }
    state.themeResearch.loading = false;
    showThemeResearchError("题材研究实时连接已中断，请稍后查看历史报告或重新发起调研。");
    closeThemeResearchStream();
    renderThemeResearch();
  };
}

function upsertThemeResearchEvent(payload) {
  const item = {
    event_type: payload.event_type || "step_update",
    task_id: payload.task_id || state.themeResearch.currentTaskId || "",
    step: Number(payload.step || 0),
    status: payload.status || "",
    title: payload.title || "",
    message: payload.message || "",
    data_preview: Array.isArray(payload.data_preview) ? payload.data_preview : [],
    created_at: payload.created_at || "",
  };
  const key = `${item.event_type}|${item.step}|${item.title}|${item.message}|${item.created_at}`;
  const exists = state.themeResearch.events.some(
    (event) => `${event.event_type}|${event.step}|${event.title}|${event.message}|${event.created_at}` === key
  );
  if (!exists) {
    state.themeResearch.events.push(item);
  }
  if (state.themeResearch.events.length > 120) {
    state.themeResearch.events = state.themeResearch.events.slice(-120);
  }
}

function renderThemeResearch() {
  renderThemeResearchControls();
  renderThemeResearchProgress();
  renderThemeResearchPreview();
  renderThemeResearchReport();
  renderThemeResearchHistory();
}

function renderThemeResearchControls() {
  if (els.themeResearchStartBtn) {
    els.themeResearchStartBtn.disabled = state.themeResearch.loading;
    els.themeResearchStartBtn.textContent = state.themeResearch.loading ? "调研中..." : "开始调研";
  }
}

function renderThemeResearchProgress() {
  if (!els.themeResearchProgressBox) return;
  const event = getLatestThemeResearchProgressEvent();
  if (!event) {
    els.themeResearchProgressBox.innerHTML = `<div class="empty">${state.themeResearch.loading ? "调研任务已创建，正在等待首个步骤返回..." : "点击“开始调研”后，这里会实时显示调研步骤。"}</div>`;
    return;
  }
  els.themeResearchProgressBox.innerHTML = `
    <article class="themeResearchProgressItem themeResearchProgressItemLatest">
      <div class="themeResearchProgressHeader">
        <span class="profileVerdict tone-${themeResearchTone(event.status)}">${escapeHtml(themeResearchStatusLabel(event.status))}</span>
        <strong>Step ${intValue(event.step)} · ${escapeHtml(event.title || themeResearchEventLabel(event.event_type))}</strong>
      </div>
      <p>${escapeHtml(event.message || "等待更多步骤结果。")}</p>
      <div class="themeResearchProgressMeta">
        <span>${escapeHtml(themeResearchEventLabel(event.event_type))}</span>
        <span>${escapeHtml(event.created_at || "实时更新")}</span>
        <span>${Array.isArray(event.data_preview) && event.data_preview.length ? `预览 ${event.data_preview.length} 条` : "暂无预览"}</span>
      </div>
    </article>
  `;
}

function renderThemeResearchPreview() {
  if (!els.themeResearchPreviewBox) return;
  const previewEvent = getLatestThemeResearchPreviewEvent();
  if (!previewEvent) {
    els.themeResearchPreviewBox.innerHTML = `<div class="empty">${state.themeResearch.loading ? "等待妙想、Tushare 或评分步骤返回数据预览..." : "暂时没有步骤预览。"}</div>`;
    return;
  }
  els.themeResearchPreviewBox.innerHTML = `
    ${renderThemeResearchPreviewCard(previewEvent)}
  `;
}

function renderThemeResearchPreviewCard(item) {
  const previewRows = (item.data_preview || []).slice(0, 5);
  return `
    <article class="themeResearchPreviewCard">
      <div class="themeResearchPreviewHeader">
        <strong>${escapeHtml(item.title || themeResearchEventLabel(item.event_type))}</strong>
        <span>${previewRows.length} 条</span>
      </div>
      <div class="themeResearchPreviewRows">
        ${previewRows
          .map(
            (row) => `
              <article class="themeResearchPreviewRow">
                <div class="themeResearchPreviewLead">
                  <strong>${escapeHtml(row.title || row.name || "未命名数据")}</strong>
                  <span class="profileVerdict tone-${themeResearchEvidenceTone(row.evidence_level)}">${escapeHtml(row.evidence_level || "待核实")}</span>
                </div>
                <p>${escapeHtml(row.summary || row.source || "暂无摘要")}</p>
                <div class="themeResearchProgressMeta">
                  <span>${escapeHtml(row.source || "系统")}</span>
                  <span>${escapeHtml(row.publish_time || "实时")}</span>
                </div>
              </article>
            `
          )
          .join("")}
      </div>
    </article>
  `;
}

function renderThemeResearchReport() {
  if (!els.themeResearchReportBox) return;
  const payload = state.themeResearch.reportPayload;
  if (!payload) {
    els.themeResearchReportBox.innerHTML = `<div class="empty">${state.themeResearch.loading ? "正在等待最终研究报告..." : "调研完成后，这里会展示结构化报告。"}</div>`;
    return;
  }
  const report = payload.report || {};
  const atlas = buildThemeResearchAtlas(report, payload);
  els.themeResearchReportBox.innerHTML = `
    <div class="themeResearchAtlasBoard">
      <section class="themeResearchAtlasHeader">
        <div class="themeResearchAtlasTitle">
          <div class="themeResearchHeroMeta">任务 ${escapeHtml(payload.task_id || report.task_id || "-")}</div>
          <h3>${escapeHtml(atlas.themeName)}</h3>
          <p>${escapeHtml(atlas.keywordsText)}</p>
        </div>
        <div class="themeResearchAtlasMeta">
          ${renderThemeResearchAtlasChip("产业阶段", atlas.stage, "neutral")}
          ${renderThemeResearchAtlasChip("拆分维度", atlas.splitDimension, "positive")}
          ${renderThemeResearchAtlasChip("证伪结论", atlas.overallResult, atlas.overallTone)}
          ${renderThemeResearchAtlasChip("参与方式", atlas.suitableFor, "neutral")}
        </div>
      </section>
      ${renderThemeResearchAtlasTable(atlas)}
      <p class="themeResearchAtlasRisk">${escapeHtml(report.risk_disclaimer || "本报告仅供研究，不构成投资建议。")}</p>
    </div>
  `;
}

function renderThemeResearchDefinition(definition) {
  const drivers = Array.isArray(definition.current_drivers) ? definition.current_drivers : [];
  const cards = [
    { label: "终端系统", value: definition.terminal_system || "待核实" },
    { label: "下游需求", value: definition.demand_source || "待核实" },
    { label: "产业阶段", value: definition.stage || "待核实" },
    { label: "当前驱动", value: drivers.length ? drivers.join(" / ") : "待核实" },
  ];
  return `
    <div class="themeResearchMetricGrid">
      ${cards
        .map(
          (item) => `
            <article class="reviewStatCard">
              <span>${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(item.value)}</strong>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchConclusion(conclusion) {
  const cards = [
    { label: "最值得关注的环节", items: conclusion.best_chain_segments || [] },
    { label: "核心公司", items: conclusion.core_companies || [] },
    { label: "情绪映射公司", items: conclusion.sentiment_only_companies || [] },
  ];
  return `
    <div class="themeResearchMetricGrid">
      ${cards
        .map(
          (card) => `
            <article class="themeResearchFactCard">
              <strong>${escapeHtml(card.label)}</strong>
              ${renderThemeResearchSimpleList(card.items, "暂无结论")}
            </article>
          `
        )
        .join("")}
      <article class="themeResearchFactCard">
        <strong>更适合的参与方式</strong>
        <p>${escapeHtml(conclusion.suitable_for || "待核实")}</p>
      </article>
    </div>
  `;
}

function renderThemeResearchFalsification(falsification) {
  return `
    <div class="themeResearchFactStack">
      <article class="themeResearchFactCard">
        <strong>总体结论</strong>
        <p>${escapeHtml(falsification.overall_result || "待核实")}</p>
      </article>
      <article class="themeResearchFactCard">
        <strong>公告核查</strong>
        ${renderThemeResearchComplexList(falsification.announcement_check || [], "暂无公告核查结果")}
      </article>
      <article class="themeResearchFactCard">
        <strong>主业财务核查</strong>
        ${renderThemeResearchComplexList(falsification.financial_check || [], "暂无财务核查结果")}
      </article>
      <article class="themeResearchFactCard">
        <strong>收入贡献测算</strong>
        ${renderThemeResearchComplexList(falsification.revenue_contribution_check || [], "暂无收入贡献测算")}
      </article>
    </div>
  `;
}

function renderThemeResearchChainMap(chainMap) {
  const sections = [
    { label: "Tier-0 终端系统层", value: chainMap.tier_0 || {} },
    { label: "Tier-1 子系统层", value: chainMap.tier_1 || [] },
    { label: "Tier-2 关键器件 / 材料层", value: chainMap.tier_2 || [] },
    { label: "Tier-3 制造工艺与壁垒层", value: chainMap.tier_3 || [] },
    { label: "Tier-4 A股映射层", value: chainMap.tier_4 || [] },
  ];
  return `
    <div class="themeResearchFactStack">
      ${sections
        .map(
          (section) => `
            <article class="themeResearchFactCard">
              <strong>${escapeHtml(section.label)}</strong>
              ${Array.isArray(section.value)
                ? renderThemeResearchComplexList(section.value, "暂无数据")
                : renderThemeResearchKeyValueSection(section.value, "暂无数据")}
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchAnchorClassification(anchorClassification) {
  const sections = [
    { label: "A类 股权锚点", value: anchorClassification.equity_anchor || [] },
    { label: "B类 业务锚点", value: anchorClassification.business_anchor || [] },
    { label: "C类 情绪映射", value: anchorClassification.sentiment_mapping || [] },
  ];
  return `
    <div class="themeResearchMetricGrid">
      ${sections
        .map(
          (section) => `
            <article class="themeResearchFactCard">
              <strong>${escapeHtml(section.label)}</strong>
              ${renderThemeResearchComplexList(section.value, "暂无分层结果")}
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchCompanyLayers(companyLayers) {
  const sections = [
    { label: "核心成长型", value: companyLayers.core_growth || [] },
    { label: "稳健价值型", value: companyLayers.stable_value || [] },
    { label: "概念弹性型", value: companyLayers.concept_elasticity || [] },
    { label: "情绪陷阱型", value: companyLayers.sentiment_trap || [] },
  ];
  return `
    <div class="themeResearchMetricGrid">
      ${sections
        .map(
          (section) => `
            <article class="themeResearchFactCard">
              <strong>${escapeHtml(section.label)}</strong>
              ${renderThemeResearchComplexList(section.value, "暂无公司")}
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchScoringTable(rows) {
  if (!Array.isArray(rows) || !rows.length) {
    return `<div class="empty">暂时没有评分结果。</div>`;
  }
  return `
    <div class="mxTableWrap">
      <table class="mxTable themeResearchScoreTable">
        <thead>
          <tr>
            <th>公司</th>
            <th>代码</th>
            <th>产业相关性</th>
            <th>稀缺性</th>
            <th>国产化空间</th>
            <th>业绩真实性</th>
            <th>景气确定性</th>
            <th>综合评分</th>
            <th>定性</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.company || "-")}</td>
                  <td>${escapeHtml(row.ts_code || "-")}</td>
                  <td>${escapeHtml(String(row.industry_relevance ?? "-"))}</td>
                  <td>${escapeHtml(String(row.scarcity ?? "-"))}</td>
                  <td>${escapeHtml(String(row.localization_space ?? "-"))}</td>
                  <td>${escapeHtml(String(row.earnings_reality ?? "-"))}</td>
                  <td>${escapeHtml(String(row.prosperity_certainty ?? "-"))}</td>
                  <td><strong>${escapeHtml(String(row.total_score ?? "-"))}</strong></td>
                  <td>${escapeHtml(row.qualitative || "-")}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderThemeResearchSources(sources) {
  if (!Array.isArray(sources) || !sources.length) {
    return `<div class="empty">暂无证据来源。</div>`;
  }
  return `
    <div class="themeResearchFactStack">
      ${sources
        .slice(0, 24)
        .map(
          (item) => `
            <article class="themeResearchFactCard">
              <div class="themeResearchPreviewLead">
                <strong>${escapeHtml(item.title || item.source || "来源")}</strong>
                <span class="profileVerdict tone-${themeResearchEvidenceTone(item.evidence_level)}">${escapeHtml(item.evidence_level || "待核实")}</span>
              </div>
              <p>${escapeHtml(item.summary || "暂无摘要")}</p>
              <div class="themeResearchProgressMeta">
                <span>${escapeHtml(item.source || "系统")}</span>
                <span>${escapeHtml(item.publish_time || "待核实")}</span>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchKeyValueSection(payload, emptyText) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload) || !Object.keys(payload).length) {
    return `<div class="empty">${escapeHtml(emptyText)}</div>`;
  }
  return `
    <div class="themeResearchKeyValueList">
      ${Object.entries(payload)
        .map(
          ([key, value]) => `
            <article class="themeResearchKeyValueItem">
              <strong>${escapeHtml(themeResearchFieldLabel(key))}</strong>
              <p>${escapeHtml(themeResearchValueText(value))}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchSimpleList(items, emptyText) {
  if (!Array.isArray(items) || !items.length) {
    return `<p>${escapeHtml(emptyText)}</p>`;
  }
  return `
    <ul class="themeResearchSimpleList">
      ${items.map((item) => `<li>${escapeHtml(themeResearchValueText(item))}</li>`).join("")}
    </ul>
  `;
}

function renderThemeResearchComplexList(items, emptyText) {
  if (!Array.isArray(items) || !items.length) {
    return `<div class="empty">${escapeHtml(emptyText)}</div>`;
  }
  return `
    <div class="themeResearchComplexList">
      ${items
        .map(
          (item) => `
            <article class="themeResearchComplexItem">
              ${renderThemeResearchComplexItem(item)}
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderThemeResearchComplexItem(item) {
  if (item === null || item === undefined) {
    return `<p>待核实</p>`;
  }
  if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") {
    return `<p>${escapeHtml(String(item))}</p>`;
  }
  if (Array.isArray(item)) {
    return renderThemeResearchSimpleList(item, "暂无条目");
  }
  const lead = item.company_name || item.company || item.title || item.name || item.stock_code || "条目";
  const bodyParts = [];
  [
    item.reason,
    item.summary,
    item.conclusion,
    item.industry_position,
    item.chain_role,
    item.earnings_realization,
  ].forEach((value) => {
    const text = String(value || "").trim();
    if (text) bodyParts.push(text);
  });
  if (Array.isArray(item.risk_points) && item.risk_points.length) {
    bodyParts.push(`风险：${item.risk_points.join(" / ")}`);
  }
  if (item.evidence_level) {
    bodyParts.push(`证据等级 ${item.evidence_level}`);
  }
  return `
    <strong>${escapeHtml(lead)}</strong>
    <p>${escapeHtml(bodyParts.join("；") || themeResearchValueText(item))}</p>
  `;
}

function renderThemeResearchHistory() {
  if (els.themeResearchHistoryMeta) {
    els.themeResearchHistoryMeta.textContent = state.themeResearch.historyTotal
      ? `共 ${state.themeResearch.historyTotal} 份报告 · 第 ${state.themeResearch.historyPage} / ${state.themeResearch.historyTotalPages} 页`
      : "支持回看最近的题材研究任务。";
  }
  if (!els.themeResearchHistoryBox) return;
  if (!state.themeResearch.historyLoaded && !state.themeResearch.history.length) {
    els.themeResearchHistoryBox.innerHTML = `<div class="empty">正在加载历史报告...</div>`;
    return;
  }
  if (!state.themeResearch.history.length) {
    els.themeResearchHistoryBox.innerHTML = `<div class="empty">当前还没有历史报告。</div>`;
    return;
  }
  els.themeResearchHistoryBox.innerHTML = `
    <div class="themeResearchHistoryScroll">
      <div class="themeResearchHistoryList">
        ${state.themeResearch.history
          .map(
            (item) => `
              <button
                type="button"
                class="themeResearchHistoryItem${item.task_id === state.themeResearch.currentTaskId ? " active" : ""}"
                data-theme-research-task="${escapeHtml(item.task_id || "")}"
                data-theme-research-name="${escapeHtml(item.theme_name || "")}"
              >
                <div class="themeResearchHistoryLead">
                  <strong>${escapeHtml(item.theme_name || item.task_id || "未命名题材")}</strong>
                  <span class="profileVerdict tone-${themeResearchTone(item.status)}">${escapeHtml(themeResearchStatusLabel(item.status))}</span>
                </div>
                <small>${escapeHtml(item.updated_at || item.created_at || "")}</small>
                <span class="themeResearchHistoryTaskId">${escapeHtml(item.task_id || "")}</span>
              </button>
            `
          )
          .join("")}
      </div>
    </div>
    ${renderReviewPager({
      page: state.themeResearch.historyPage,
      totalPages: state.themeResearch.historyTotalPages,
      totalItems: state.themeResearch.historyTotal,
      pageSize: state.themeResearch.historyPageSize,
      action: "theme-research-history",
    })}
  `;
}

function getLatestThemeResearchProgressEvent() {
  const events = (state.themeResearch.events || []).filter((item) => item.event_type !== "data_preview");
  return events.length ? events[events.length - 1] : null;
}

function getLatestThemeResearchPreviewEvent() {
  const events = (state.themeResearch.events || []).filter((item) => Array.isArray(item.data_preview) && item.data_preview.length);
  return events.length ? events[events.length - 1] : null;
}

function renderThemeResearchAtlasChip(label, value, tone = "neutral") {
  return `
    <article class="themeResearchAtlasChip">
      <span>${escapeHtml(label)}</span>
      <strong class="tone-${escapeHtml(tone)}">${escapeHtml(value || "待核实")}</strong>
    </article>
  `;
}

function renderThemeResearchAtlasTable(atlas) {
  if (!atlas.totalRows) {
    return `<div class="empty">当前报告还没有可展示的树形图谱数据。</div>`;
  }
  return `
    <div class="themeResearchAtlasTableWrap">
      <table class="themeResearchTreeTable">
        <thead>
          <tr>
            <th>题材</th>
            <th>一级拆分</th>
            <th>细分</th>
            <th>股票</th>
            <th>评分</th>
          </tr>
        </thead>
        <tbody>
          ${atlas.groups
            .map((group, groupIndex) =>
              group.items
                .map(
                  (item, itemIndex) => `
                    <tr>
                      ${groupIndex === 0 && itemIndex === 0 ? renderThemeResearchThemeCell(atlas) : ""}
                      ${itemIndex === 0 ? renderThemeResearchGroupCell(group) : ""}
                      ${renderThemeResearchSegmentCell(item)}
                      <td class="themeResearchTreeStockCell">
                        ${renderThemeResearchTreeCompanies(item.companies || [])}
                      </td>
                      <td class="themeResearchTreeScoreCell">
                        <div class="themeResearchTreeScore">
                          <strong>${escapeHtml(item.scoreText)}</strong>
                          <span class="profileVerdict tone-${escapeHtml(item.scoreTone || "neutral")}">${escapeHtml(item.scoreVerdict || "等待评分")}</span>
                          <small>${escapeHtml(item.scoreMeta || "待核实")}</small>
                        </div>
                      </td>
                    </tr>
                  `
                )
                .join("")
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderThemeResearchThemeCell(atlas) {
  return `
    <td class="themeResearchTreeThemeCell" rowspan="${atlas.totalRows}">
      <div class="themeResearchTreeTheme">
        <div class="themeResearchTreeThemeGlyphs">${themeResearchThemeGlyphs(atlas.themeName)}</div>
        <span>${escapeHtml(atlas.stage)}</span>
        <small>${escapeHtml(atlas.suitableFor)}</small>
      </div>
    </td>
  `;
}

function renderThemeResearchGroupCell(group) {
  return `
    <td class="themeResearchTreeGroupCell" rowspan="${group.items.length}">
      <div class="themeResearchTreeGroup">
        <strong>${escapeHtml(group.label)}</strong>
        <span>${escapeHtml(group.summary)}</span>
        <small>${escapeHtml(group.countLabel)}</small>
      </div>
    </td>
  `;
}

function renderThemeResearchSegmentCell(item) {
  return `
    <td class="themeResearchTreeSegmentCell">
      <div class="themeResearchTreeSegment">
        <strong>${escapeHtml(item.segmentLabel || "待核实")}</strong>
        <span>${escapeHtml(item.segmentSummary || "待核实")}</span>
      </div>
    </td>
  `;
}

function renderThemeResearchTreeCompanies(companies) {
  if (!Array.isArray(companies) || !companies.length) {
    return `<div class="themeResearchTreeCompanyList"><p class="themeResearchTreeEmptyNote">暂无可确认的 A 股映射公司。</p></div>`;
  }
  return `
    <div class="themeResearchTreeCompanyList">
      ${companies
        .map(
          (company) => `
            <article class="themeResearchTreeCompanyChip">
              <div class="themeResearchTreeCompanyMain">
                <strong>${escapeHtml(company.companyName || "待核实")}</strong>
                <span class="themeResearchTreeCompanyCode">${escapeHtml(company.tsCode || "待核实")}</span>
                ${company.scoreText && company.scoreText !== "待核实" ? `<span class="profileVerdict tone-${escapeHtml(company.scoreTone || "neutral")}">${escapeHtml(company.scoreText)} 分</span>` : ""}
                ${company.isCore ? '<span class="profileVerdict tone-positive">核心</span>' : ""}
              </div>
              <div class="themeResearchTreeCompanyMeta">
                <small>${escapeHtml(company.noteText || "待核实")}</small>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function buildThemeResearchAtlas(report, payload) {
  if (report.industry_tree && Array.isArray(report.industry_tree.children) && report.industry_tree.children.length) {
    return buildThemeResearchAtlasFromTree(report, payload);
  }
  return buildThemeResearchAtlasFromLegacy(report, payload);
}

function buildThemeResearchAtlasFromTree(report, payload) {
  const themeName = report.normalized_name || payload.theme_name || report.theme_name || "题材研究";
  const definition = report.industry_definition || {};
  const finalConclusion = report.final_conclusion || {};
  const falsification = report.falsification || {};
  const keywords = Array.isArray(report.keywords) ? report.keywords.filter(Boolean) : [];
  const tree = report.industry_tree || {};
  const leafRows = flattenThemeResearchIndustryTree(tree.children || []);
  const groups = [];
  const grouped = new Map();
  leafRows.forEach((row) => {
    const groupLabel = row.path[0] || "待核实";
    const group = grouped.get(groupLabel) || {
      label: groupLabel,
      items: [],
      companyCount: 0,
    };
    const companies = normalizeThemeResearchTreeCompanies(row.companies || [], finalConclusion.core_companies || []);
    const scoreValues = companies.map((item) => item.scoreValue).filter((value) => Number.isFinite(value));
    const averageScore = scoreValues.length
      ? scoreValues.reduce((sum, value) => sum + value, 0) / scoreValues.length
      : null;
    const scoreView = themeResearchScoreView(averageScore);
    group.items.push({
      segmentLabel: row.path.slice(1).join(" / ") || row.path[0] || "待核实",
      segmentSummary: themeResearchCompactText(row.summary || "待核实", 36),
      companies,
      scoreValue: averageScore,
      scoreText: scoreView.text,
      scoreTone: scoreView.tone,
      scoreVerdict: scoreView.verdict,
      scoreMeta: companies.length ? `${companies.length} 家公司均值` : "暂无公司映射",
    });
    group.companyCount += companies.length;
    grouped.set(groupLabel, group);
  });
  grouped.forEach((group) => {
    group.summary = `${group.items.length} 个细分 / ${group.companyCount || 0} 家公司`;
    groups.push(group);
  });

  return {
    themeName,
    stage: definition.stage || "待核实",
    suitableFor: finalConclusion.suitable_for || "待核实",
    splitDimension: tree.dimension || "待核实",
    overallResult: falsification.overall_result || "待核实",
    overallTone: themeResearchAtlasResultTone(falsification.overall_result || ""),
    keywordsText: keywords.length ? keywords.join(" / ") : "等待关键词归纳",
    groups,
    totalRows: groups.reduce((sum, group) => sum + group.items.length, 0),
  };
}

function buildThemeResearchAtlasFromLegacy(report, payload) {
  const themeName = report.normalized_name || payload.theme_name || report.theme_name || "题材研究";
  const definition = report.industry_definition || {};
  const finalConclusion = report.final_conclusion || {};
  const falsification = report.falsification || {};
  const keywords = Array.isArray(report.keywords) ? report.keywords.filter(Boolean) : [];
  const layerDefinitions = [
    { key: "core_growth", label: "核心成长" },
    { key: "stable_value", label: "稳健价值" },
    { key: "concept_elasticity", label: "概念弹性" },
    { key: "sentiment_trap", label: "情绪陷阱" },
  ];
  const companyLayers = report.company_layers || {};
  const scoringRows = Array.isArray(report.scoring_table) ? report.scoring_table : [];
  const tier4Rows = Array.isArray(report.industry_chain_map?.tier_4) ? report.industry_chain_map.tier_4 : [];
  const anchorRows = buildThemeResearchAnchorRows(report.anchor_classification || {});
  const coreSet = new Set((finalConclusion.core_companies || []).map((item) => String(item || "").trim()));
  const groups = layerDefinitions
    .map((definitionItem) => {
      const rawItems = Array.isArray(companyLayers[definitionItem.key]) ? companyLayers[definitionItem.key] : [];
      const items = rawItems
        .map((item) => buildThemeResearchAtlasItem(item, definitionItem.label, scoringRows, tier4Rows, anchorRows, coreSet))
        .filter((item) => item && item.companyName)
        .map((item) => {
          const scoreView = themeResearchScoreView(item.scoreValue);
          return {
            segmentLabel: item.companyName,
            segmentSummary: themeResearchCompactText(item.stockMeta || "待核实", 36),
            companies: [
              {
                companyName: item.companyName,
                tsCode: item.tsCode,
                scoreValue: item.scoreValue,
                scoreText: item.scoreText,
                scoreTone: item.scoreTone,
                noteText: themeResearchCompactText(item.qualitative || item.conclusion || "待核实", 42),
                isCore: item.isCore,
              },
            ],
            scoreValue: item.scoreValue,
            scoreText: item.scoreText,
            scoreTone: scoreView.tone,
            scoreVerdict: scoreView.verdict,
            scoreMeta: "单股映射",
          };
        });
      return items.length
        ? {
            label: definitionItem.label,
            summary: `${items.length} 家公司`,
            items,
          }
        : null;
    })
    .filter(Boolean);
  return {
    themeName,
    stage: definition.stage || "待核实",
    suitableFor: finalConclusion.suitable_for || "待核实",
    splitDimension: "按公司分层兜底",
    overallResult: falsification.overall_result || "待核实",
    overallTone: themeResearchAtlasResultTone(falsification.overall_result || ""),
    keywordsText: keywords.length ? keywords.join(" / ") : "等待关键词归纳",
    groups,
    totalRows: groups.reduce((sum, group) => sum + group.items.length, 0),
  };
}

function flattenThemeResearchIndustryTree(nodes, path = []) {
  const rows = [];
  (nodes || []).forEach((node) => {
    const cleanName = String(node?.name || "").trim();
    if (!cleanName) return;
    const nextPath = [...path, cleanName];
    const childNodes = Array.isArray(node?.children) ? node.children : [];
    const companies = Array.isArray(node?.companies) ? node.companies : [];
    if (childNodes.length) {
      rows.push(...flattenThemeResearchIndustryTree(childNodes, nextPath));
      return;
    }
    rows.push({
      path: nextPath,
      summary: String(node?.summary || "").trim(),
      companies,
    });
  });
  return rows;
}

function normalizeThemeResearchTreeCompanies(companies, coreCompanies) {
  const coreSet = new Set((coreCompanies || []).map((item) => String(item || "").trim()));
  return (companies || []).map((item) => {
    const scoreValue = Number(item?.score);
    const qualitative = String(item?.qualitative || "").trim();
    const conclusion = String(item?.conclusion || "").trim();
    const chainRole = String(item?.chain_role || "").trim();
    const anchorType = themeResearchAnchorText(item?.anchor_type || "");
    const noteParts = [anchorType, chainRole, qualitative || conclusion].filter(Boolean);
    const companyName = String(item?.company_name || item?.company || item?.name || "").trim() || "待核实";
    const scoreView = themeResearchScoreView(scoreValue);
    return {
      companyName,
      tsCode: String(item?.stock_code || item?.ts_code || "").trim().toUpperCase(),
      scoreValue: Number.isFinite(scoreValue) ? scoreValue : null,
      scoreText: scoreView.text,
      scoreTone: scoreView.tone,
      noteText: themeResearchCompactText(noteParts.join(" / ") || "待核实", 42),
      isCore: coreSet.has(companyName),
    };
  });
}

function finalizeThemeResearchAtlasGroup(label, items) {
  const cleanItems = (items || []).filter(Boolean);
  if (!cleanItems.length) return null;
  cleanItems.sort((left, right) => {
    if (right.isCore !== left.isCore) return right.isCore ? 1 : -1;
    return (right.scoreValue || -1) - (left.scoreValue || -1);
  });
  const scoreValues = cleanItems.map((item) => item.scoreValue).filter((value) => Number.isFinite(value));
  const averageScore = scoreValues.length
    ? `${formatCompactValue(scoreValues.reduce((sum, value) => sum + value, 0) / scoreValues.length)} 分`
    : "暂无评分";
  return {
    label,
    items: cleanItems,
    countLabel: `${cleanItems.length} 只股票`,
    summary: averageScore,
  };
}

function buildThemeResearchAtlasItem(sourceItem, layerLabel, scoringRows, tier4Rows, anchorRows, coreSet) {
  const companyName = String(sourceItem.company_name || sourceItem.company || sourceItem.name || "").trim();
  const tsCode = String(sourceItem.stock_code || sourceItem.ts_code || "").trim().toUpperCase();
  if (!companyName && !tsCode) return null;
  const scoreRow = themeResearchFindCompanyRow(scoringRows, companyName, tsCode);
  const tier4Row = themeResearchFindCompanyRow(tier4Rows, companyName, tsCode);
  const anchorRow = themeResearchFindCompanyRow(anchorRows, companyName, tsCode);
  const scoreValue = Number(scoreRow?.total_score);
  const qualitative = scoreRow?.qualitative || sourceItem.qualitative || "";
  const conclusion = sourceItem.conclusion || sourceItem.reason || qualitative || "待核实";
  const noteParts = [
    tsCode,
    themeResearchCompactChainRole(tier4Row?.chain_role || tier4Row?.industry_position || sourceItem.chain_role || sourceItem.industry_position || ""),
    themeResearchAnchorText(tier4Row?.anchor_type || sourceItem.anchor_type || anchorRow?.anchor_type || anchorRow?.anchor_label || ""),
    tier4Row?.evidence_level || anchorRow?.evidence_level ? `证据 ${(tier4Row?.evidence_level || anchorRow?.evidence_level)}` : "",
  ].filter(Boolean);
  const scoreView = themeResearchScoreView(scoreValue);
  return {
    identityKey: themeResearchIdentityKey(companyName, tsCode),
    companyName: companyName || tsCode,
    tsCode,
    layerLabel,
    scoreValue: Number.isFinite(scoreValue) ? scoreValue : null,
    scoreText: scoreView.text,
    scoreTone: scoreView.tone,
    qualitative,
    conclusion,
    stockMeta: themeResearchCompactText(noteParts.join(" / ") || "暂无更多映射说明。", 42),
    isCore: coreSet.has(companyName),
  };
}

function buildThemeResearchAnchorRows(anchorClassification) {
  return [
    ...((anchorClassification.equity_anchor || []).map((item) => ({ ...item, anchor_label: "股权锚点" }))),
    ...((anchorClassification.business_anchor || []).map((item) => ({ ...item, anchor_label: "业务锚点" }))),
    ...((anchorClassification.sentiment_mapping || []).map((item) => ({ ...item, anchor_label: "情绪映射" }))),
  ];
}

function themeResearchFindCompanyRow(rows, companyName, tsCode) {
  const cleanName = String(companyName || "").trim();
  const cleanCode = String(tsCode || "").trim().toUpperCase();
  return (rows || []).find((row) => {
    const rowName = String(row?.company_name || row?.company || row?.name || row?.title || "").trim();
    const rowCode = String(row?.stock_code || row?.ts_code || "").trim().toUpperCase();
    return (cleanCode && rowCode && cleanCode === rowCode) || (cleanName && rowName && cleanName === rowName);
  }) || null;
}

function themeResearchIdentityKey(companyName, tsCode) {
  return `${String(tsCode || "").trim().toUpperCase()}|${String(companyName || "").trim()}`;
}

function themeResearchCompactChainRole(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  if (text.includes("业务映射")) return "业务映射";
  if (text.includes("股权映射")) return "股权映射";
  if (text.includes("情绪映射")) return "情绪映射";
  if (text.length <= 20) return text;
  return `${text.slice(0, 20)}…`;
}

function themeResearchAnchorText(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  if (text === "A") return "股权锚点";
  if (text === "B") return "业务锚点";
  if (text === "C") return "情绪映射";
  return text;
}

function themeResearchThemeGlyphs(value) {
  const text = String(value || "").trim();
  if (/^[\u4e00-\u9fa5]{2,6}$/.test(text)) {
    return text
      .split("")
      .map((char) => `<span>${escapeHtml(char)}</span>`)
      .join("");
  }
  return `<strong>${escapeHtml(text || "题材")}</strong>`;
}

function themeResearchAtlasResultTone(result) {
  const text = String(result || "");
  if (text.includes("部分")) return "neutral";
  if (text.includes("失败")) return "caution";
  if (text.includes("通过")) return "positive";
  return "neutral";
}

function themeResearchScoreView(scoreValue) {
  if (!Number.isFinite(scoreValue)) {
    return { text: "待核实", verdict: "等待评分", tone: "neutral" };
  }
  if (scoreValue >= 8) {
    return { text: formatCompactValue(scoreValue), verdict: "重点研究", tone: "positive" };
  }
  if (scoreValue >= 6) {
    return { text: formatCompactValue(scoreValue), verdict: "观察验证", tone: "neutral" };
  }
  if (scoreValue >= 4) {
    return { text: formatCompactValue(scoreValue), verdict: "偏概念", tone: "neutral" };
  }
  return { text: formatCompactValue(scoreValue), verdict: "谨慎回避", tone: "caution" };
}

function themeResearchCompactText(value, limit = 36) {
  const text = String(value || "").trim();
  if (!text) return "待核实";
  if (text.length <= limit) return text;
  return `${text.slice(0, Math.max(0, limit - 1))}…`;
}

function themeResearchTone(status) {
  if (status === "success" || status === "completed") return "positive";
  if (status === "error" || status === "failed") return "caution";
  return "neutral";
}

function themeResearchEvidenceTone(level) {
  if (level === "S" || level === "A") return "positive";
  if (level === "C") return "caution";
  return "neutral";
}

function themeResearchStatusLabel(status) {
  if (status === "success" || status === "completed") return "已完成";
  if (status === "error" || status === "failed") return "失败";
  if (status === "partial") return "部分完成";
  if (status === "running") return "进行中";
  return status || "更新";
}

function themeResearchEventLabel(eventType) {
  return {
    task_started: "任务已启动",
    step_update: "步骤更新",
    tool_call_started: "工具开始调用",
    tool_call_finished: "工具调用完成",
    tool_call_failed: "工具调用失败",
    data_preview: "数据预览",
    final_report: "最终报告",
    task_failed: "任务失败",
  }[eventType] || "步骤更新";
}

function themeResearchFieldLabel(key) {
  return {
    terminal_system: "终端系统",
    demand_source: "下游需求",
    stage: "产业阶段",
    current_drivers: "当前驱动",
    value_location: "价值量所在",
    barrier: "壁垒",
    supply_constraint: "供给约束",
    demand_driver: "需求驱动力",
    a_share_uniqueness: "A股唯一性",
    earnings_timeline: "业绩兑现时间表",
    volume: "量",
    price: "价",
    competition: "竞争",
    policy_capital: "政策/资本",
  }[key] || key;
}

function themeResearchValueText(value) {
  if (value === null || value === undefined) return "待核实";
  if (typeof value === "string") return value || "待核实";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.length ? value.map((item) => themeResearchValueText(item)).join(" / ") : "待核实";
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${themeResearchFieldLabel(key)}：${themeResearchValueText(item)}`)
      .join("；");
  }
  return String(value);
}

function setThemeBoardStatus(message) {
  if (els.themeBoardStatusText) {
    els.themeBoardStatusText.textContent = message;
  }
}

function showThemeBoardError(message) {
  if (!els.themeBoardErrorBox) return;
  els.themeBoardErrorBox.textContent = message;
  els.themeBoardErrorBox.hidden = false;
}

function hideThemeBoardError() {
  if (!els.themeBoardErrorBox) return;
  els.themeBoardErrorBox.hidden = true;
  els.themeBoardErrorBox.textContent = "";
}

function closeThemeBoardModal() {
  if (!els.themeBoardModal) return;
  state.themeBoard.modalTsCode = "";
  state.themeBoard.modalName = "";
  state.themeBoard.detail = null;
  els.themeBoardModal.hidden = true;
  document.body.classList.remove("modalOpen");
}

async function loadThemeBoardOverview() {
  const requestId = ++state.themeBoard.requestId;
  state.themeBoard.overview = { status: "loading" };
  closeThemeBoardModal();
  renderThemeBoard();
  hideThemeBoardError();
  setThemeBoardStatus("正在聚合开盘啦题材榜单与股票明细...");
  try {
    const dateValue = normalizeDateInput(els.themeBoardDate?.value || "");
    const suffix = dateValue ? `?trade_date=${encodeURIComponent(dateValue)}` : "";
    const data = await fetchJson(`/api/theme-board/overview${suffix}`);
    if (requestId !== state.themeBoard.requestId) return;
    state.themeBoard.overview = data;
    state.themeBoard.loaded = true;
    setThemeBoardStatus(`题材榜单已更新到 ${formatDate(data.trade_date || dateValue)}，先看题材热度，再点开题材股票找核心票。`);
  } catch (err) {
    if (requestId !== state.themeBoard.requestId) return;
    state.themeBoard.overview = { status: "error", message: err.message };
    showThemeBoardError(err.message);
  }
  renderThemeBoard();
}

function renderThemeBoard() {
  renderThemeBoardSummary();
  renderThemeBoardList();
  renderThemeBoardInsight();
}

function renderThemeBoardSummary() {
  const overview = state.themeBoard.overview;
  if (!els.themeBoardSummaryBox) return;
  if (!overview || overview.status === "loading") {
    els.themeBoardSummaryBox.innerHTML = `
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
    `;
    return;
  }
  if (overview.status === "error") {
    els.themeBoardSummaryBox.innerHTML = `<div class="mxError">${escapeHtml(overview.message || "题材榜单加载失败。")}</div>`;
    return;
  }
  const summary = overview.summary || {};
  const cards = [
    { label: "题材数", value: intValue(summary.theme_count), note: "当日可聚合题材" },
    { label: "上榜股数", value: intValue(summary.stock_count), note: "去重后的题材股票" },
    { label: "龙一题材", value: summary.leader_name || "-", note: `上榜股 ${intValue(summary.leader_stock_count)} 只` },
    { label: "题材热度", value: intValue(summary.leader_hot_total), note: `榜单个股 ${intValue(summary.kpl_stock_count)} 只` },
  ];
  els.themeBoardSummaryBox.innerHTML = cards
    .map(
      (card) => `
        <article class="reviewStatCard">
          <span>${escapeHtml(card.label)}</span>
          <strong>${escapeHtml(String(card.value ?? "-"))}</strong>
          <p>${escapeHtml(card.note)}</p>
        </article>
      `
    )
    .join("");
}

function renderThemeBoardList() {
  const overview = state.themeBoard.overview;
  if (!els.themeBoardListBox) return;
  if (!overview || overview.status === "loading") {
    els.themeBoardListBox.innerHTML = `<div class="empty">正在加载题材榜单...</div>`;
    return;
  }
  if (overview.status === "error") {
    els.themeBoardListBox.innerHTML = `<div class="mxError">${escapeHtml(overview.message || "题材榜单加载失败。")}</div>`;
    return;
  }
  const items = overview.items || [];
  if (!items.length) {
    els.themeBoardListBox.innerHTML = `<div class="empty">当前日期没有可用的题材榜单数据。</div>`;
    return;
  }
  els.themeBoardListBox.innerHTML = `
    <div class="themeBoardList">
      ${items.map((item) => renderThemeBoardCard(item)).join("")}
    </div>
  `;
}

function renderThemeBoardCard(item) {
  const topStock = item.top_stock || {};
  const sampleStocks = Array.isArray(item.stock_names) ? item.stock_names.slice(0, 6) : [];
  return `
    <article class="themeBoardCard reviewClickable" data-theme-board-open="1" data-ts-code="${escapeHtml(item.ts_code || "")}" data-name="${escapeHtml(item.name || "")}">
      <div class="themeBoardCardHeader">
        <div>
          <div class="themeBoardRank">第 ${intValue(item.rank)} 名</div>
          <strong>${escapeHtml(item.name || "-")}</strong>
        </div>
        <span class="profileVerdict tone-neutral">热度 ${intValue(item.hot_total)}</span>
      </div>
      <div class="themeBoardMetrics">
        <span>上榜股 ${intValue(item.stock_count)} 只</span>
        <span>均值 ${escapeHtml(String(item.hot_avg ?? 0))}</span>
        <span>龙一 ${escapeHtml(topStock.name || "-")}</span>
        <span>人气 ${intValue(topStock.hot_num)}</span>
      </div>
      ${sampleStocks.length ? `<p>${escapeHtml(sampleStocks.join(" / "))}</p>` : `<p>暂无题材股票摘要。</p>`}
      ${item.sample_desc ? `<small>${escapeHtml(item.sample_desc)}</small>` : ""}
    </article>
  `;
}

function renderThemeBoardInsight() {
  const overview = state.themeBoard.overview;
  if (!els.themeBoardInsightBox) return;
  if (!overview || overview.status === "loading") {
    els.themeBoardInsightBox.innerHTML = `<div class="empty">正在生成题材观察要点...</div>`;
    return;
  }
  if (overview.status === "error") {
    els.themeBoardInsightBox.innerHTML = `<div class="mxError">${escapeHtml(overview.message || "题材观察要点加载失败。")}</div>`;
    return;
  }
  const items = overview.items || [];
  const leader = items[0] || {};
  const runnerUp = items[1] || {};
  els.themeBoardInsightBox.innerHTML = `
    <div class="reviewFocusStack">
      <article class="reviewFocusItem">
        <strong>当前龙一</strong>
        <p>${escapeHtml(leader.name || "暂无数据")}</p>
        <div class="reviewFocusMeta">上榜股 ${intValue(leader.stock_count)} 只 · 热度 ${intValue(leader.hot_total)}</div>
      </article>
      <article class="reviewFocusItem">
        <strong>第二梯队</strong>
        <p>${escapeHtml(runnerUp.name || "暂无数据")}</p>
        <div class="reviewFocusMeta">上榜股 ${intValue(runnerUp.stock_count)} 只 · 热度 ${intValue(runnerUp.hot_total)}</div>
      </article>
      <article class="reviewFocusItem">
        <strong>使用方式</strong>
        <p>先看题材热度密度，再点开题材股票，优先核对龙一和前排辨识度个股。</p>
      </article>
    </div>
  `;
}

async function openThemeBoardModal(tsCode, name) {
  const cleanTsCode = String(tsCode || "").trim().toUpperCase();
  const cleanName = String(name || "").trim();
  if (!cleanTsCode && !cleanName) return;
  const requestId = ++state.themeBoard.detailRequestId;
  state.themeBoard.modalTsCode = cleanTsCode;
  state.themeBoard.modalName = cleanName;
  state.themeBoard.detail = { status: "loading" };
  if (els.themeBoardModalTitle) {
    els.themeBoardModalTitle.textContent = cleanName || "题材股票明细";
  }
  if (els.themeBoardModalMeta) {
    els.themeBoardModalMeta.textContent = `正在加载 ${cleanName || cleanTsCode} 的题材股票数据...`;
  }
  if (els.themeBoardModalBody) {
    els.themeBoardModalBody.innerHTML = `<div class="empty">正在加载题材股票数据...</div>`;
  }
  if (els.themeBoardModal) {
    els.themeBoardModal.hidden = false;
  }
  document.body.classList.add("modalOpen");
  try {
    const params = new URLSearchParams();
    const dateValue = normalizeDateInput(els.themeBoardDate?.value || "");
    if (dateValue) params.set("trade_date", dateValue);
    if (cleanTsCode) params.set("ts_code", cleanTsCode);
    if (cleanName) params.set("name", cleanName);
    const data = await fetchJson(`/api/theme-board/detail?${params.toString()}`);
    if (requestId !== state.themeBoard.detailRequestId) return;
    state.themeBoard.detail = data;
    renderThemeBoardModal();
  } catch (err) {
    if (requestId !== state.themeBoard.detailRequestId) return;
    state.themeBoard.detail = { status: "error", message: err.message };
    renderThemeBoardModal();
  }
}

function renderThemeBoardModal() {
  const detail = state.themeBoard.detail;
  if (!els.themeBoardModalBody || !els.themeBoardModalTitle || !els.themeBoardModalMeta) return;
  if (!detail || detail.status === "loading") {
    els.themeBoardModalTitle.textContent = state.themeBoard.modalName || "题材股票明细";
    els.themeBoardModalMeta.textContent = "正在加载题材股票数据...";
    els.themeBoardModalBody.innerHTML = `<div class="empty">正在加载题材股票数据...</div>`;
    return;
  }
  if (detail.status === "error") {
    els.themeBoardModalTitle.textContent = state.themeBoard.modalName || "题材股票明细";
    els.themeBoardModalMeta.textContent = "题材股票加载失败";
    els.themeBoardModalBody.innerHTML = `<div class="mxError">${escapeHtml(detail.message || "题材股票加载失败。")}</div>`;
    return;
  }
  const theme = detail.theme || {};
  const items = detail.items || [];
  els.themeBoardModalTitle.textContent = theme.name || state.themeBoard.modalName || "题材股票明细";
  els.themeBoardModalMeta.textContent = `题材日期 ${formatDate(detail.trade_date || "")} · 股票 ${intValue(theme.stock_count)} 只 · 总热度 ${intValue(theme.hot_total)}`;
  els.themeBoardModalBody.innerHTML = items.length
    ? `
      <div class="reviewPanelStack">
        <div class="reviewPanelMeta">
          <small>点击股票可直接跳转到股票分析；优先展示题材成分接口明细，缺失时回退到榜单题材原文。</small>
        </div>
        <table class="reviewTable">
          <thead>
            <tr>
              <th>股票</th>
              <th>代码</th>
              <th>人气值</th>
              <th>题材描述</th>
            </tr>
          </thead>
          <tbody>
            ${items.map((item) => `
              <tr class="reviewClickable" data-review-open-analysis="1" data-ts-code="${escapeHtml(item.ts_code || "")}" data-name="${escapeHtml(item.name || "")}">
                <td>${renderReviewStockButton(item.name || "-", item)}</td>
                <td>${escapeHtml(item.ts_code || "-")}</td>
                <td>${intValue(item.hot_num)}</td>
                <td>${escapeHtml(item.desc || "-")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `
    : `<div class="empty">当前题材没有可展示的股票数据。</div>`;
}

async function loadReviewOverview() {
  const requestId = ++state.review.requestId;
  const aiRequestId = ++state.review.aiRequestId;
  state.review.overview = { status: "loading" };
  state.review.hotMoneyPage = 1;
  state.review.modalPage = 1;
  state.review.modalSearch = "";
  state.review.modalKey = "";
  closeReviewModal();
  renderReview();
  setReviewStatus("正在汇总龙虎榜、游资、涨跌停与连板天梯...");
  hideReviewError();

  try {
    const dateValue = normalizeDateInput(els.reviewDate?.value || "");
    const suffix = dateValue ? `?trade_date=${encodeURIComponent(dateValue)}` : "";
    const data = await fetchJson(`/api/review/overview${suffix}`);
    if (requestId !== state.review.requestId) return;
    data.ai_review = { status: "loading", message: "" };
    state.review.overview = data;
    setReviewStatus(`复盘已更新到 ${formatDate(data.trade_date || dateValue)}，先看主线板块，再等 AI 补充养家视角结论。`);
    renderReview();
    void loadReviewAiBrief(data, requestId, aiRequestId, dateValue);
  } catch (err) {
    if (requestId !== state.review.requestId) return;
    state.review.overview = { status: "error", message: err.message };
    showReviewError(err.message);
  }

  renderReview();
}

async function loadReviewAiBrief(reviewPayload, requestId, aiRequestId, dateValue = "") {
  try {
    const data = await fetchJson("/api/review/ai-brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review: reviewPayload }),
    });
    if (requestId !== state.review.requestId || aiRequestId !== state.review.aiRequestId) return;
    state.review.overview = data;
    setReviewStatus(`复盘已更新到 ${formatDate(data.trade_date || dateValue)}，先看养家视角阶段判断，再看主线板块与核心个股。`);
  } catch (err) {
    if (requestId !== state.review.requestId || aiRequestId !== state.review.aiRequestId) return;
    if (state.review.overview && state.review.overview.status === "ok") {
      state.review.overview = {
        ...state.review.overview,
        ai_review: { status: "error", message: err.message },
      };
      setReviewStatus(`复盘已更新到 ${formatDate(state.review.overview.trade_date || dateValue)}，先看主线板块，再看龙虎榜与游资共振。`);
    }
  }
  renderReview();
}

function renderReview() {
  renderReviewSummary();
  renderReviewDragonTiger();
  renderReviewInstitution();
  renderReviewLimitLists();
  renderReviewLadder();
  renderReviewFocus();
  renderReviewEmotionCyclePanel();
  renderReviewBoards();
  renderReviewStocks();
}

function renderReviewSummary() {
  const review = state.review.overview;
  if (!els.reviewSummaryBox) return;

  if (!review || review.status === "loading") {
    els.reviewSummaryBox.innerHTML = `
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
      <article class="reviewStatCard loading"><div class="mxSkeleton"></div><div class="mxSkeleton short"></div></article>
    `;
    return;
  }

  if (review.status === "error") {
    els.reviewSummaryBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "复盘数据加载失败。")}</div>`;
    return;
  }

  const summary = review.summary || {};
  const hotMoneyStats = review.hot_money_stats || {};
  const cards = [
    { label: "龙虎榜", value: summary.dragon_count, note: "上榜个股数", modalKey: "dragon_tiger" },
    { label: "游资数据", value: summary.hot_money_count, note: `原始 ${intValue(hotMoneyStats.record_count)} 条 · 合并后 ${intValue(hotMoneyStats.merged_count)} 只`, modalKey: "hot_money_trades" },
    { label: "涨停 / 跌停", value: `${summary.up_limit_count || 0} / ${summary.down_limit_count || 0}`, note: `炸板 ${summary.burst_count || 0} 家`, modalKey: "limit_lists" },
    { label: "最高连板", value: `${summary.highest_board || 0} 板`, note: `关注板块 ${summary.focus_board_count || 0} 个 · 股票 ${summary.focus_stock_count || 0} 只`, modalKey: "ladder" },
  ];
  els.reviewSummaryBox.innerHTML = cards
    .map(
      (card) => `
        <article class="reviewStatCard${card.modalKey ? " actionable" : ""}" ${card.modalKey ? `data-review-summary-open="${escapeHtml(card.modalKey)}"` : ""}>
          <span>${escapeHtml(card.label)}</span>
          <strong>${escapeHtml(String(card.value ?? "-"))}</strong>
          <p>${escapeHtml(card.note)}</p>
        </article>
      `
    )
    .join("");
}

function renderReviewDragonTiger() {
  const review = state.review.overview;
  if (!els.reviewDragonBox) return;
  if (!review || review.status === "loading") {
    els.reviewDragonBox.innerHTML = `<div class="empty">正在加载龙虎榜数据...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewDragonBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "龙虎榜加载失败。")}</div>`;
    return;
  }
  const items = (review.dragon_tiger || []).slice(0, 12);
  if (!items.length) {
    els.reviewDragonBox.innerHTML = `<div class="empty">当天没有可用龙虎榜数据。</div>`;
    return;
  }
  els.reviewDragonBox.innerHTML = renderReviewTable(
    [
      { key: "name", label: "股票", stockLink: true },
      { key: "pct_change", label: "涨跌幅", format: formatSignedPercentValue },
      { key: "net_amount", label: "净额", format: formatAmountYi },
      { key: "reason", label: "上榜原因" },
    ],
    items
  );
}

function renderReviewInstitution() {
  const review = state.review.overview;
  if (!els.reviewInstBox) return;
  if (!review || review.status === "loading") {
    els.reviewInstBox.innerHTML = `<div class="empty">正在加载游资数据...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewInstBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "游资数据加载失败。")}</div>`;
    return;
  }
  const items = review.hot_money_trades || [];
  if (!items.length) {
    els.reviewInstBox.innerHTML = `<div class="empty">当天没有游资明细。</div>`;
    return;
  }
  const { rows, page, totalPages, total } = paginateRows(items, state.review.hotMoneyPage, 8);
  state.review.hotMoneyPage = page;
  const table = renderReviewTable(
    [
      { key: "name", label: "股票", stockLink: true },
      { key: "hot_money_label", label: "游资" },
      { key: "net_amount", label: "净买入", format: formatAmountYi },
      { key: "org_count", label: "席位数", format: intValue },
      { key: "record_count", label: "记录数", format: intValue },
    ],
    rows
  );
  els.reviewInstBox.innerHTML = `
    <div class="reviewPanelStack">
      <div class="reviewPanelMeta">
        <small>按股票合并相关游资交易记录，共 ${intValue(total)} 只股票。</small>
      </div>
      ${table}
      ${renderReviewPager({
        page,
        totalPages,
        totalItems: total,
        pageSize: 8,
        action: "hot-money-panel",
      })}
    </div>
  `;
}

function renderReviewLimitLists() {
  const review = state.review.overview;
  if (!els.reviewLimitBox) return;
  if (!review || review.status === "loading") {
    els.reviewLimitBox.innerHTML = `<div class="empty">正在加载涨跌停列表...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewLimitBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "涨跌停列表加载失败。")}</div>`;
    return;
  }
  const groups = review.limit_lists || {};
  const sections = [
    { title: "涨停前排", tone: "positive", items: (groups.up || []).slice(0, 6), summary: (item) => `${item.name || ""} · ${intValue(item.limit_times)} 次封板 · 强度 ${intValue(item.strth)}` },
    { title: "炸板观察", tone: "warn", items: (groups.burst || []).slice(0, 6), summary: (item) => `${item.name || ""} · 开板 ${intValue(item.open_times)} 次` },
    { title: "跌停风险", tone: "danger", items: (groups.down || []).slice(0, 6), summary: (item) => `${item.name || ""} · ${formatSignedPercentValue(item.pct_chg)}` },
  ];
  els.reviewLimitBox.innerHTML = `
    <div class="reviewList">
      ${sections
        .map(
          (section) => `
            <article class="reviewFocusItem">
              <strong><span class="reviewBadge ${section.tone === "warn" ? "warn" : section.tone === "danger" ? "danger" : ""}">${escapeHtml(section.title)}</span></strong>
              ${
                section.items.length
                  ? `<div class="newsList">
                      ${section.items
                        .map(
                          (item) => `
                            <article class="newsItem${reviewRowCanOpen(item) ? " reviewClickable" : ""}" ${reviewRowCanOpen(item) ? `data-review-open-analysis="1" data-ts-code="${escapeHtml(resolveReviewStockCode(item))}" data-name="${escapeHtml(item.name || "")}"` : ""}>
                              <strong>${renderReviewStockButton(item.name || "", item)}</strong>
                              <p>${escapeHtml(section.summary(item))}</p>
                            </article>
                          `
                        )
                        .join("")}
                    </div>`
                  : `<p class="mxCardMessage">暂无样本。</p>`
              }
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderReviewLadder() {
  const review = state.review.overview;
  if (!els.reviewLadderBox) return;
  if (!review || review.status === "loading") {
    els.reviewLadderBox.innerHTML = `<div class="empty">正在加载连板天梯...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewLadderBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "连板天梯加载失败。")}</div>`;
    return;
  }
  const items = (review.ladder || []).slice(0, 12);
  if (!items.length) {
    els.reviewLadderBox.innerHTML = `<div class="empty">当天没有连板天梯数据。</div>`;
    return;
  }
  els.reviewLadderBox.innerHTML = renderReviewTable(
    [
      { key: "name", label: "股票", stockLink: true },
      { key: "continue_num", label: "连板", format: (value) => `${intValue(value)} 板` },
      { key: "limit_times", label: "涨停次数", format: intValue },
      { key: "concept", label: "概念" },
    ],
    items
  );
}

function renderReviewFocus() {
  const review = state.review.overview;
  if (!els.reviewFocusBox) return;
  if (!review || review.status === "loading") {
    els.reviewFocusBox.innerHTML = `<div class="empty">正在提炼复盘要点...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewFocusBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "复盘要点加载失败。")}</div>`;
    return;
  }
  const notes = review.notes || {};
  const aiReview = review.ai_review?.status === "ok" ? review.ai_review.analysis || {} : null;
  const aiLoading = review.ai_review?.status === "loading";
  const indices = (review.market_indices?.items || []).slice(0, 3);
  const aiError = review.ai_review?.status === "error" ? review.ai_review.message || "" : "";
  els.reviewFocusBox.className = "reviewFocusStack";
  els.reviewFocusBox.innerHTML = `
    <article class="reviewFocusItem reviewFocusHero">
      <div class="reviewFocusHeroHeader">
        <strong>一句话复盘</strong>
        ${aiReview?.market_stage ? `<span class="reviewBadge">${escapeHtml(aiReview.market_stage)}</span>` : ""}
      </div>
      <p>${escapeHtml(aiReview?.summary || notes.summary || "暂无复盘结论。")}</p>
      ${
        aiReview
          ? `<small class="reviewFocusMeta">养家视角 AI 已接入当前复盘事实层。</small>`
          : aiLoading
            ? `<small class="reviewFocusMeta">AI 正在补充养家视角，不影响下方事实层先看。</small>`
            : aiError
              ? `<small class="reviewFocusMeta">AI 复盘暂时降级：${escapeHtml(aiError)}</small>`
              : ""
      }
    </article>
    ${
      indices.length
        ? `<section class="reviewIndexStrip">
            ${indices
              .map(
                (item) => `
                  <article class="reviewIndexCard">
                    <span>${escapeHtml(item.name || item.ts_code || "")}</span>
                    <strong>${formatBakMetric(item.pct_chg, "%", 2) || "-"}</strong>
                    <small>收 ${formatPrice(item.close)} · PB ${formatBakMetric(item.pb, "", 2) || "-"}</small>
                  </article>
                `
              )
              .join("")}
          </section>`
        : ""
    }
    <section class="reviewInsightGrid">
      ${renderReviewInsightCard("指数复盘", aiReview?.index_review?.summary || "先看三大指数强弱与估值位置。", aiReview?.index_review?.signals || [])}
      ${renderReviewInsightCard("情绪周期", aiReview?.emotion_cycle?.summary || "先看赚钱效应、亏钱效应和接力反馈。", aiReview?.emotion_cycle?.signals || notes.watch_points || [])}
      ${renderReviewInsightCard("盘面复盘", aiReview?.tape_review?.summary || "先看热点板块、资金流向和涨跌停前排。", []
        .concat(aiReview?.tape_review?.hot_themes || [])
        .concat(aiReview?.tape_review?.fund_flow || [])
        .concat(aiReview?.tape_review?.limit_watch || []))}
      ${renderReviewInsightCard("消息复盘", aiReview?.news_review?.summary || "先看催化强度和连板梯队是否继续扩散。", []
        .concat(aiReview?.news_review?.catalysts || [])
        .concat(aiReview?.news_review?.ladder_focus || []))}
    </section>
    <article class="reviewFocusItem">
      <strong>今天先看什么</strong>
      <ul class="reviewBulletList">
        ${(aiReview?.watch_points || notes.watch_points || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>暂无重点观察项。</li>"}
      </ul>
    </article>
    <article class="reviewFocusItem">
      <strong>风险提醒</strong>
      <ul class="reviewBulletList">
        ${(aiReview?.risk_points || notes.risk_points || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>暂无额外风险提醒。</li>"}
      </ul>
    </article>
  `;
}

function renderReviewEmotionCyclePanel() {
  const review = state.review.overview;
  if (!els.reviewEmotionCycleBox) return;
  if (!review || review.status === "loading") {
    els.reviewEmotionCycleBox.className = "reviewFocusStack";
    els.reviewEmotionCycleBox.innerHTML = `<div class="empty">正在生成情绪周期图...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewEmotionCycleBox.className = "reviewFocusStack";
    els.reviewEmotionCycleBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "情绪周期图加载失败。")}</div>`;
    return;
  }
  const aiReview = review.ai_review?.status === "ok" ? review.ai_review.analysis || {} : null;
  els.reviewEmotionCycleBox.className = "reviewFocusStack";
  els.reviewEmotionCycleBox.innerHTML = renderReviewEmotionCycle(review, aiReview);
}

function renderReviewEmotionCycle(review, aiReview) {
  const cycle = review?.emotion_cycle || {};
  const aiCycle = aiReview?.emotion_cycle || {};
  const activeKey = cycle.phase_key || inferEmotionCycleKey(aiCycle.phase || aiCycle.summary || aiReview?.market_stage || "");
  const activeLabel = cycle.phase || aiCycle.phase || "低位分歧";
  const stage = cycle.stage || aiReview?.market_stage || "阶段观察";
  const summary = aiCycle.summary || cycle.summary || "先看赚钱效应和亏钱效应的相对强弱。";
  const basis = Array.isArray(cycle.basis) && cycle.basis.length ? cycle.basis : Array.isArray(aiCycle.signals) ? aiCycle.signals : [];
  const metrics = cycle.metrics || {};
  const phases = [
    ["low_divergence", "低位分歧", "试错前夜", "turn"],
    ["turn_strong", "分歧转强", "弱转强", "rise"],
    ["acceleration", "加速", "大阳线", "rise"],
    ["climax", "一致", "高潮", "rise"],
    ["ice_point", "冰点", "一致恐慌", "turn"],
    ["down_acceleration", "分歧加速", "杀跌释放", "fall"],
    ["turn_weak", "分歧转弱", "强转弱", "fall"],
    ["high_divergence", "高位分歧", "高位博弈", "fall"],
  ];
  const phaseMap = new Map(phases.map(([key, label, sub, tone]) => [key, { key, label, sub, tone }]));
  const activeIndex = Math.max(
    0,
    phases.findIndex(([key, label]) => key === activeKey || label === activeLabel)
  );
  const activeTone = cycle.tone || phaseMap.get(activeKey)?.tone || "turn";
  const previousKey = cycle.previous_phase_key || phases[(activeIndex - 1 + phases.length) % phases.length][0];
  const nextKey = cycle.next_phase_key || phases[(activeIndex + 1) % phases.length][0];
  const previousPhase = phaseMap.get(previousKey) || phaseMap.get(phases[(activeIndex - 1 + phases.length) % phases.length][0]);
  const nextPhase = phaseMap.get(nextKey) || phaseMap.get(phases[(activeIndex + 1) % phases.length][0]);
  const badgeClass = activeTone === "fall" ? "danger" : activeTone === "turn" ? "warn" : "";
  const metricCards = [
    ["进攻温度", metrics.attack_score, "涨停扩散 + 指数配合"],
    ["分歧压力", metrics.pressure_score, "炸板 / 跌停 / 高标兑现"],
    ["高标承接", metrics.carry_score, `最高 ${intValue(metrics.highest_board)} 板`],
  ];
  const biasLabel = cycle.bias_label || "阶段观察";
  const confidence = intValue(cycle.confidence);
  return `
    <article class="reviewFocusItem reviewEmotionCycleCard">
      <div class="reviewFocusHeroHeader">
        <strong>情绪周期图</strong>
        <span class="reviewBadge ${badgeClass}">${escapeHtml(activeLabel)}</span>
      </div>
      <section class="reviewEmotionCycleSummary tone-${escapeHtml(activeTone)}">
        <div class="reviewEmotionCycleSummaryMain">
          <small>当前阶段</small>
          <strong>${escapeHtml(activeLabel)}</strong>
          <p>${escapeHtml(stage)}</p>
        </div>
        <div class="reviewEmotionCycleSummaryAside">
          <span>${escapeHtml(biasLabel)}</span>
          <strong>${confidence}</strong>
          <small>阶段置信</small>
        </div>
      </section>
      <div class="reviewEmotionMetricStrip">
        ${metricCards
          .map(
            ([label, value, hint]) => `
              <article class="reviewEmotionMetricCard">
                <span>${escapeHtml(label)}</span>
                <strong>${intValue(value)}</strong>
                <small>${escapeHtml(hint)}</small>
              </article>
            `
          )
          .join("")}
      </div>
      <div class="reviewEmotionCycleLoop" aria-label="养家情绪周期">
        ${phases
          .map(([key, label, sub, tone], index) => {
            const isActive = key === activeKey || label === activeLabel;
            const isPrevious = key === previousKey;
            const isNext = key === nextKey;
            return `
              <div class="reviewEmotionNode tone-${tone}${isActive ? " active" : ""}${isPrevious ? " previous" : ""}${isNext ? " next" : ""}">
                <b>${index + 1}</b>
                <span>${escapeHtml(label)}</span>
                ${sub ? `<small>${escapeHtml(sub)}</small>` : ""}
                ${isActive ? `<em>当前阶段</em>` : isPrevious ? `<em>上一段</em>` : isNext ? `<em>下一段</em>` : ""}
              </div>
            `;
          })
          .join("")}
      </div>
      <div class="reviewEmotionCycleFlow">
        <span>上一段：${escapeHtml(cycle.previous_phase || previousPhase?.label || "—")}</span>
        <strong>${escapeHtml(activeLabel)}</strong>
        <span>下一段：${escapeHtml(cycle.next_phase || nextPhase?.label || "—")}</span>
      </div>
      <p>${escapeHtml(summary)}</p>
      <ul class="reviewBulletList">
        ${basis.slice(0, 3).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>暂无情绪样本。</li>"}
      </ul>
      ${cycle.action ? `<p class="reviewActionText">${escapeHtml(cycle.action)}</p>` : ""}
      ${cycle.focus ? `<p class="reviewFocusMeta">盯盘重点：${escapeHtml(cycle.focus)}</p>` : ""}
      ${cycle.risk ? `<p class="reviewFocusMeta">${escapeHtml(cycle.risk)}</p>` : ""}
    </article>
  `;
}

function inferEmotionCycleKey(text) {
  const value = String(text || "");
  if (value.includes("冰点")) return "ice_point";
  if (value.includes("分歧加速")) return "down_acceleration";
  if (value.includes("分歧转弱") || value.includes("强转弱") || value.includes("退潮")) return "turn_weak";
  if (value.includes("高位分歧")) return "high_divergence";
  if (value.includes("一致") || value.includes("高潮")) return "climax";
  if (value.includes("加速")) return "acceleration";
  if (value.includes("分歧转强") || value.includes("弱转强") || value.includes("修复")) return "turn_strong";
  return "low_divergence";
}

function renderReviewBoards() {
  const review = state.review.overview;
  if (!els.reviewBoardsBox) return;
  if (!review || review.status === "loading") {
    els.reviewBoardsBox.innerHTML = `<div class="empty">正在生成关注板块...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewBoardsBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "关注板块加载失败。")}</div>`;
    return;
  }
  const items = review.focus_boards || [];
  if (!items.length) {
    els.reviewBoardsBox.innerHTML = `<div class="empty">当前没有可提炼的主线板块。</div>`;
    return;
  }
  els.reviewBoardsBox.className = "reviewList";
  els.reviewBoardsBox.innerHTML = items
    .map(
      (item) => {
        const metaParts = [
          `涨停 ${intValue(item.limit_count)} 家`,
          intValue(item.count) > 0
            ? `板块样本 ${intValue(item.count)} 家`
            : intValue(item.chain_count) > 0
            ? `连板 ${intValue(item.chain_count)} 家`
            : (item.up_stat ? `高标 ${escapeHtml(item.up_stat)}` : ""),
          `涨幅 ${formatSignedPercentValue(item.pct_chg)}`,
        ].filter(Boolean);
        return `
        <article class="reviewFocusItem">
          <strong>${escapeHtml(item.name || "")} <span class="reviewBadge">第 ${intValue(item.rank)} 名</span></strong>
          <div class="reviewFocusMeta">${metaParts.join(" · ")}</div>
          <p>${escapeHtml(item.watch_reason || "")}</p>
          ${item.ai_action ? `<p class="reviewActionText">${escapeHtml(item.ai_action)}</p>` : ""}
          ${item.ai_reason ? `<p>${escapeHtml(item.ai_reason)}</p>` : ""}
        </article>
      `;
      }
    )
    .join("");
}

function renderReviewStocks() {
  const review = state.review.overview;
  if (!els.reviewStocksBox) return;
  if (!review || review.status === "loading") {
    els.reviewStocksBox.innerHTML = `<div class="empty">正在生成关注股票...</div>`;
    return;
  }
  if (review.status === "error") {
    els.reviewStocksBox.innerHTML = `<div class="mxError">${escapeHtml(review.message || "关注股票加载失败。")}</div>`;
    return;
  }
  const items = review.focus_stocks || [];
  if (!items.length) {
    els.reviewStocksBox.innerHTML = `<div class="empty">当前没有可提炼的核心股票。</div>`;
    return;
  }
  els.reviewStocksBox.className = "reviewList";
  els.reviewStocksBox.innerHTML = items
    .map(
      (item) => `
        <article class="reviewFocusItem${reviewRowCanOpen(item) ? " reviewClickable" : ""}" ${reviewRowCanOpen(item) ? `data-review-open-analysis="1" data-ts-code="${escapeHtml(resolveReviewStockCode(item))}" data-name="${escapeHtml(item.name || "")}"` : ""}>
          ${renderReviewStockHeadline(item)}
          <div class="reviewFocusMeta">${escapeHtml(item.ts_code || "")} · 分数 ${escapeHtml(String(item.score ?? "-"))}</div>
          <p>${escapeHtml((item.tags || []).join(" / "))}</p>
          ${item.ai_action ? `<p class="reviewActionText">${escapeHtml(item.ai_action)}</p>` : ""}
          ${item.ai_reason ? `<p>${escapeHtml(item.ai_reason)}</p>` : ""}
          <p>${escapeHtml(item.reason || "")}</p>
        </article>
      `
    )
    .join("");
}

function renderReviewInsightCard(title, summary, bullets) {
  const items = Array.isArray(bullets) ? bullets.filter(Boolean).slice(0, 4) : [];
  return `
    <article class="reviewFocusItem reviewInsightCard">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(summary || "暂无补充结论。")}</p>
      <ul class="reviewBulletList">
        ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>暂无补充样本。</li>"}
      </ul>
    </article>
  `;
}

function renderReviewTable(columns, rows) {
  return `
    <table class="reviewTable">
      <thead>
        <tr>${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr${reviewRowCanOpen(row) ? ` class="reviewClickable" data-review-open-analysis="1" data-ts-code="${escapeHtml(resolveReviewStockCode(row))}" data-name="${escapeHtml(row.name || row.exalter || "")}"` : ""}>
                ${columns
                  .map((column) => {
                    const raw = row[column.key];
                    const value = column.format ? column.format(raw, row) : raw;
                    if (column.stockLink) {
                      return `<td>${renderReviewStockButton(value ?? "-", row)}</td>`;
                    }
                    return `<td>${escapeHtml(value ?? "-")}</td>`;
                  })
                  .join("")}
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderReviewStockButton(label, row, className = "reviewStockLink") {
  const text = String(label ?? "-");
  const tsCode = resolveReviewStockCode(row);
  const name = row?.name || row?.exalter || text;
  if (!tsCode && !String(name || "").trim()) {
    return escapeHtml(text);
  }
  return `<button type="button" class="${escapeHtml(className)}" data-review-open-analysis="1" data-ts-code="${escapeHtml(tsCode)}" data-name="${escapeHtml(name)}">${escapeHtml(text)}</button>`;
}

function matchesReviewKeyword(parts, keyword) {
  if (!keyword) return false;
  const values = Array.isArray(parts) ? parts : [parts];
  return values.some((part) => String(part || "").toLowerCase().includes(keyword));
}

function renderReviewInstitutionModal(items, searchTerm = "", page = 1) {
  const keyword = String(searchTerm || "").trim().toLowerCase();
  const groups = groupReviewHotMoneyRecords(items);
  const filtered = keyword
    ? groups.filter((row) => `${row.name || ""} ${row.org_summary || ""} ${row.stock_names.join(" ")}`.toLowerCase().includes(keyword))
    : groups;
  state.review.modalPage = 1;
  const sections = buildReviewHotMoneyCategorySections(filtered);
  const board = filtered.length
    ? `
      <div class="reviewHotMoneyBoard">
        ${sections.map((section) => renderReviewHotMoneyCategorySection(section, keyword)).join("")}
      </div>
    `
    : `<div class="empty">没有匹配当前游资、股票名称或代码的游资明细。</div>`;
  return `
    <form class="reviewModalSearchBar" data-review-modal-search-form="hot-money">
      <label class="reviewModalSearchField">
        <span>按游资或股票搜索</span>
        <input type="search" data-review-modal-search="hot-money" placeholder="例如：量化基金、北京帮、达实智能、002421" value="${escapeHtml(searchTerm)}" />
      </label>
      <div class="reviewModalSearchActions">
        <button type="submit" class="miniButton">确定</button>
        <button type="button" class="ghostButton miniButton" data-review-modal-reset-search="hot-money">重置</button>
      </div>
      <small>匹配 ${intValue(filtered.length)} / 共 ${intValue(groups.length)} 组游资</small>
    </form>
    <div class="reviewPanelStack">
      <div class="reviewPanelMeta">
        <small>支持按“机构 / 量化 / 游资名称”或股票名称、代码搜索；点击股票可直接跳转到股票分析。</small>
      </div>
      ${filtered.length ? `
        <div class="reviewPanelMeta">
          <small>${keyword ? "命中的股票会用红色高亮，方便你快速扫出来。" : "输入游资名或股票名后，会把命中的股票用红色高亮。"}</small>
        </div>
      ` : ""}
      ${board}
    </div>
  `;
}

function groupReviewHotMoneyRecords(items) {
  const groups = new Map();
  (items || []).forEach((row) => {
    const names = Array.isArray(row.hot_money_names) && row.hot_money_names.length
      ? row.hot_money_names
      : [row.hm_name || row.hot_money_label || "未识别游资"];
    names
      .map((item) => String(item || "").trim())
      .filter(Boolean)
      .forEach((name) => {
        const group = groups.get(name) || {
          name,
          buy_amount: 0,
          sell_amount: 0,
          net_amount: 0,
          record_count: 0,
          orgs: new Set(),
          stocks: new Map(),
          stock_names: [],
        };
        group.buy_amount += Number(row.buy_amount || 0);
        group.sell_amount += Number(row.sell_amount || 0);
        group.net_amount += Number(row.net_amount || 0);
        group.record_count += 1;
        String(row.exalter || row.hm_orgs || "")
          .split(/[；;\n]+/)
          .map((item) => item.trim())
          .filter(Boolean)
          .forEach((org) => group.orgs.add(org));
        const stockKey = String(resolveReviewStockCode(row) || row.name || row.ts_name || "").trim();
        if (!stockKey) {
          groups.set(name, group);
          return;
        }
        const stock = group.stocks.get(stockKey) || {
          ts_code: resolveReviewStockCode(row),
          name: row.name || row.ts_name || stockKey,
          buy_amount: 0,
          sell_amount: 0,
          net_amount: 0,
          record_count: 0,
          orgs: new Set(),
          tags: new Set(),
        };
        stock.buy_amount += Number(row.buy_amount || 0);
        stock.sell_amount += Number(row.sell_amount || 0);
        stock.net_amount += Number(row.net_amount || 0);
        stock.record_count += 1;
        String(row.exalter || row.hm_orgs || "")
          .split(/[；;\n]+/)
          .map((item) => item.trim())
          .filter(Boolean)
          .forEach((org) => stock.orgs.add(org));
        if (row.tag) stock.tags.add(String(row.tag));
        group.stocks.set(stockKey, stock);
        groups.set(name, group);
      });
  });

  return Array.from(groups.values())
    .map((group) => {
      const stocks = Array.from(group.stocks.values())
        .map((item) => ({
          ...item,
          org_summary: Array.from(item.orgs || []).slice(0, 3).join("；"),
          org_count: (item.orgs && item.orgs.size) || 0,
          tags: Array.from(item.tags),
        }))
        .sort((a, b) => Math.abs(Number(b.net_amount || 0)) - Math.abs(Number(a.net_amount || 0)));
      return {
        name: group.name,
        buy_amount: group.buy_amount,
        sell_amount: group.sell_amount,
        net_amount: group.net_amount,
        record_count: group.record_count,
        org_count: group.orgs.size,
        org_summary: Array.from(group.orgs).slice(0, 3).join("；"),
        stock_count: stocks.length,
        stock_names: stocks.map((item) => item.name).filter(Boolean),
        stocks,
      };
    })
    .sort((a, b) => Math.abs(Number(b.net_amount || 0)) - Math.abs(Number(a.net_amount || 0)));
}

function flattenReviewHotMoneyTableRows(groups) {
  const rows = [];
  (groups || []).forEach((group) => {
    const stocks = Array.isArray(group.stocks) && group.stocks.length ? group.stocks : [null];
    stocks.forEach((stock) => {
      rows.push({
        group_name: group.name || "未识别游资",
        group_buy_amount: Number(group.buy_amount || 0),
        group_sell_amount: Number(group.sell_amount || 0),
        group_net_amount: Number(group.net_amount || 0),
        group_record_count: Number(group.record_count || 0),
        group_org_count: Number(group.org_count || 0),
        group_org_summary: group.org_summary || "",
        ts_code: stock?.ts_code || "",
        name: stock?.name || "",
        buy_amount: Number(stock?.buy_amount ?? group.buy_amount ?? 0),
        sell_amount: Number(stock?.sell_amount ?? group.sell_amount ?? 0),
        net_amount: Number(stock?.net_amount ?? group.net_amount ?? 0),
        record_count: Number(stock?.record_count ?? group.record_count ?? 0),
        org_count: Number(stock?.org_count ?? group.org_count ?? 0),
        org_summary: stock?.org_summary || group.org_summary || "",
        tags: Array.isArray(stock?.tags) ? stock.tags : [],
      });
    });
  });
  return rows.sort((a, b) => Math.abs(Number(b.net_amount || 0)) - Math.abs(Number(a.net_amount || 0)));
}

function buildReviewHotMoneyCategorySections(groups) {
  const ordered = ["机构", "量化", "游资"];
  const buckets = new Map(ordered.map((label) => [label, { label, groups: [], net_amount: 0, stock_count: 0 }]));
  (groups || []).forEach((group) => {
    const category = classifyReviewHotMoneyGroup(group);
    const bucket = buckets.get(category) || { label: category, groups: [], net_amount: 0, stock_count: 0 };
    bucket.groups.push(group);
    bucket.net_amount += Number(group.net_amount || 0);
    bucket.stock_count += Number(group.stock_count || 0);
    buckets.set(category, bucket);
  });
  return ordered
    .map((label) => buckets.get(label))
    .filter((section) => section && section.groups.length)
    .map((section) => ({
      ...section,
      groups: section.groups.sort((a, b) => Math.abs(Number(b.net_amount || 0)) - Math.abs(Number(a.net_amount || 0))),
    }));
}

function classifyReviewHotMoneyGroup(group) {
  const text = `${group?.name || ""} ${group?.org_summary || ""}`.toLowerCase();
  if (/(量化|程序化|量化基金|量化打板|对冲|高频|机器|算法)/.test(text)) return "量化";
  if (/(机构|机构专用|深股通|沪股通|港股通|北向|陆股通|基金专用|社保|养老金|券商自营|保险|qfii|公募|私募)/.test(text)) return "机构";
  return "游资";
}

function renderReviewHotMoneyCategorySection(section, keyword = "") {
  return `
    <section class="reviewHotMoneyCategorySection">
      <div class="reviewHotMoneyCategoryCell">
        <strong>${escapeHtml(section.label || "游资")}</strong>
        <small>${intValue(section.groups.length)} 组 · ${intValue(section.stock_count)} 只股票</small>
        <span class="reviewHotMoneyCategoryNet ${Number(section.net_amount || 0) >= 0 ? "positive" : "negative"}">${formatSignedAmountShort(section.net_amount)}</span>
      </div>
      <div class="reviewHotMoneyCategoryRows">
        ${section.groups.map((group) => renderReviewHotMoneyBoardRow(group, keyword)).join("")}
      </div>
    </section>
  `;
}

function splitReviewHotMoneyStocks(stocks) {
  const list = Array.isArray(stocks) ? stocks : [];
  const buys = list.filter((stock) => Number(stock?.net_amount || 0) >= 0);
  const sells = list.filter((stock) => Number(stock?.net_amount || 0) < 0);
  return [
    {
      key: "buy",
      label: "净买入",
      tone: "positive",
      stocks: buys,
      total: buys.reduce((sum, stock) => sum + Number(stock?.net_amount || 0), 0),
    },
    {
      key: "sell",
      label: "净卖出",
      tone: "negative",
      stocks: sells,
      total: sells.reduce((sum, stock) => sum + Number(stock?.net_amount || 0), 0),
    },
  ].filter((section) => section.stocks.length);
}

function renderReviewHotMoneyBoardRow(group, keyword = "") {
  const positive = Number(group.net_amount || 0) >= 0;
  const stocks = Array.isArray(group.stocks) ? group.stocks : [];
  const stockSections = splitReviewHotMoneyStocks(stocks);
  return `
    <article class="reviewHotMoneyBoardRow ${positive ? "positive" : "negative"}">
      <div class="reviewHotMoneyBoardLead">
        <div class="reviewHotMoneyBoardName">
          <strong>${escapeHtml(group.name || "未识别游资")}</strong>
          <small>${intValue(group.stock_count)} 只股票 · ${intValue(group.org_count)} 席位 · ${intValue(group.record_count)} 条记录</small>
        </div>
        <div class="reviewHotMoneyBoardAmounts">
          <span>买 ${formatAmountYi(group.buy_amount)}</span>
          <span>卖 ${formatAmountYi(group.sell_amount)}</span>
          <strong class="${positive ? "positive" : "negative"}">${formatSignedAmountShort(group.net_amount)}</strong>
        </div>
      </div>
      <div class="reviewHotMoneyBoardStocks">
        ${stockSections.map((section) => `
          <section class="reviewHotMoneyStockBucket tone-${section.tone}">
            <div class="reviewHotMoneyStockBucketHeader">
              <strong>${section.label}</strong>
              <small>${intValue(section.stocks.length)} 只 · ${formatSignedAmountShort(section.total)}</small>
            </div>
            <div class="reviewHotMoneyStockBucketGrid">
              ${section.stocks.map((stock) => renderReviewHotMoneyStockPill(stock, keyword)).join("")}
            </div>
          </section>
        `).join("")}
      </div>
    </article>
  `;
}

function renderReviewHotMoneyStockPill(stock, keyword = "") {
  const tags = Array.isArray(stock?.tags) ? stock.tags.filter(Boolean) : [];
  const positive = Number(stock?.net_amount || 0) >= 0;
  const matched = matchesReviewKeyword([stock?.name, stock?.ts_code], keyword);
  return `
    <div class="reviewHotMoneyStockPill ${positive ? "positive" : "negative"}${matched ? " matched" : ""}">
      <div class="reviewHotMoneyStockPillMain">
        ${renderReviewStockButton(stock?.name || stock?.ts_code || "-", stock, `reviewStockLink board-pill${matched ? " matched" : ""}`)}
        <span class="reviewHotMoneyStockPillAmount ${positive ? "positive" : "negative"}${matched ? " matched" : ""}">${formatSignedAmountShort(stock?.net_amount || 0)}</span>
      </div>
      <small class="${matched ? "matched" : ""}">${escapeHtml(stock?.ts_code || "-")}${tags.length ? ` · ${escapeHtml(tags.join(" / "))}` : ""}</small>
    </div>
  `;
}

function renderReviewHotMoneyGroup(group, keyword = "") {
  const positive = Number(group.net_amount || 0) >= 0;
  return `
    <article class="reviewHotMoneyGroup reviewHotMoneyFlowCard">
      <div class="reviewHotMoneyFlowHeader">
        <div class="reviewHotMoneyHeadline">
          <strong>${escapeHtml(group.name || "未识别游资")}</strong>
          <p>关联 ${intValue(group.stock_count)} 只股票 · ${intValue(group.org_count)} 个席位 · ${intValue(group.record_count)} 条记录</p>
        </div>
        <div class="reviewHotMoneyFlowTotals">
          <span>买入 ${formatAmountYi(group.buy_amount)}</span>
          <span>卖出 ${formatAmountYi(group.sell_amount)}</span>
          <span class="reviewHotMoneyNet ${positive ? "" : "negative"}">净额 ${formatSignedAmountShort(group.net_amount)}</span>
        </div>
      </div>
      <div class="reviewHotMoneyFlow">
        <div class="reviewHotMoneyOrgNode ${positive ? "positive" : "negative"}">
          <strong>${escapeHtml(group.name || "未识别游资")}</strong>
          <small>${escapeHtml(group.org_summary || "席位数据待补充")}</small>
        </div>
        <div class="reviewHotMoneyBranchList">
          ${group.stocks.map((stock) => renderReviewHotMoneyStockRow(stock, keyword)).join("")}
        </div>
      </div>
    </article>
  `;
}

function renderReviewHotMoneyStockRow(stock, keyword = "") {
  const tags = Array.isArray(stock.tags) ? stock.tags.filter(Boolean) : [];
  const positive = Number(stock.net_amount || 0) >= 0;
  const matched = matchesReviewKeyword([stock?.name, stock?.ts_code], keyword);
  return `
    <article class="reviewHotMoneyBranch">
      <div class="reviewHotMoneyStockNode ${positive ? "positive" : "negative"}${matched ? " matched" : ""}${reviewRowCanOpen(stock) ? " reviewClickable" : ""}" ${reviewRowCanOpen(stock) ? `data-review-open-analysis="1" data-ts-code="${escapeHtml(resolveReviewStockCode(stock))}" data-name="${escapeHtml(stock.name || "")}"` : ""}>
        <div class="reviewHotMoneyStockLabel">
          <strong>${renderReviewStockButton(stock.name || stock.ts_code || "-", stock, `reviewStockLink inline light${matched ? " matched" : ""}`)}</strong>
          <small class="${matched ? "matched" : ""}">${escapeHtml(stock.ts_code || "-")}</small>
        </div>
        <span class="reviewHotMoneyStockAmount${matched ? " matched" : ""}">${formatSignedAmountShort(stock.net_amount)}</span>
      </div>
      <div class="reviewHotMoneyAmountNode">
        <strong>${escapeHtml(stock.org_summary || "关联席位")}</strong>
        <div class="reviewHotMoneyAmountMeta">
          <span>买入 ${formatAmountYi(stock.buy_amount)}</span>
          <span>卖出 ${formatAmountYi(stock.sell_amount)}</span>
          <span class="reviewHotMoneyNet ${positive ? "" : "negative"}">净额 ${formatSignedAmountShort(stock.net_amount)}</span>
          <span>记录 ${intValue(stock.record_count)} 条</span>
        </div>
        ${tags.length ? `<p>${escapeHtml(tags.join(" / "))}</p>` : ""}
      </div>
    </article>
  `;
}

function renderReviewModalSection(title, content) {
  return `
    <section class="reviewModalSection">
      <h3>${escapeHtml(title)}</h3>
      ${content}
    </section>
  `;
}

function reviewRowCanOpen(row) {
  return Boolean(resolveReviewStockCode(row) || String(row?.name || row?.exalter || "").trim());
}

function paginateRows(items, page, pageSize) {
  const safePageSize = Math.max(1, intValue(pageSize) || 1);
  const total = Array.isArray(items) ? items.length : 0;
  const totalPages = Math.max(1, Math.ceil(total / safePageSize));
  const currentPage = Math.min(Math.max(intValue(page) || 1, 1), totalPages);
  const start = (currentPage - 1) * safePageSize;
  return {
    rows: (items || []).slice(start, start + safePageSize),
    page: currentPage,
    totalPages,
    total,
  };
}

function renderReviewPager({ page, totalPages, totalItems, pageSize, action }) {
  if (!totalItems || totalPages <= 1) return "";
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(totalItems, page * pageSize);
  return `
    <div class="reviewPager">
      <small>第 ${page} / ${totalPages} 页 · 显示 ${start}-${end} / ${intValue(totalItems)}</small>
      <div class="reviewPagerActions">
        <button type="button" class="ghostButton miniButton" data-review-page-action="${escapeHtml(action)}" data-review-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>上一页</button>
        <button type="button" class="ghostButton miniButton" data-review-page-action="${escapeHtml(action)}" data-review-page="${page + 1}" ${page >= totalPages ? "disabled" : ""}>下一页</button>
      </div>
    </div>
  `;
}

function openReviewSummaryModal(key) {
  const review = state.review.overview;
  if (!review || review.status !== "ok" || !els.reviewModal) return;
  let title = "复盘明细";
  let meta = `复盘日期 ${formatDate(review.trade_date || "")}`;
  let body = `<div class="empty">暂无可展示数据。</div>`;

  if (key === "dragon_tiger") {
    title = "龙虎榜明细";
    meta = `复盘日期 ${formatDate(review.trade_date || "")} · 共 ${intValue((review.dragon_tiger || []).length)} 只上榜股票`;
    body = (review.dragon_tiger || []).length
      ? renderReviewTable(
          [
            { key: "name", label: "股票", stockLink: true },
            { key: "pct_change", label: "涨跌幅", format: formatSignedPercentValue },
            { key: "turnover_rate", label: "换手率", format: (value) => formatSignedPercentValue(value) },
            { key: "net_amount", label: "龙虎榜净额", format: formatAmountYi },
            { key: "reason", label: "上榜原因" },
          ],
          review.dragon_tiger || []
        )
      : `<div class="empty">当天没有可用龙虎榜数据。</div>`;
  } else if (key === "hot_money_trades") {
    title = "游资龙虎榜合并视图";
    meta = `复盘日期 ${formatDate(review.trade_date || "")} · 原始 ${intValue(review.hot_money_stats?.record_count)} 条 · 归并 ${intValue((review.hot_money_trades || []).length)} 只股票`;
    body = (review.hot_money_records || []).length
      ? renderReviewInstitutionModal(review.hot_money_records || [], "", 1)
      : `<div class="empty">当天没有游资明细。</div>`;
  } else if (key === "limit_lists") {
    const groups = review.limit_lists || {};
    const upRows = groups.up || [];
    const burstRows = groups.burst || [];
    const downRows = groups.down || [];
    title = "涨跌停列表明细";
    meta = `复盘日期 ${formatDate(review.trade_date || "")} · 涨停 ${upRows.length} 家 · 炸板 ${burstRows.length} 家 · 跌停 ${downRows.length} 家`;
    body = [
      renderReviewModalSection(
        "涨停前排",
        upRows.length
          ? renderReviewTable(
              [
                { key: "name", label: "股票", stockLink: true },
                { key: "pct_chg", label: "涨跌幅", format: formatSignedPercentValue },
                { key: "limit_times", label: "封板次数", format: intValue },
                { key: "strth", label: "强度", format: intValue },
                { key: "open_times", label: "开板次数", format: intValue },
              ],
              upRows
            )
          : `<div class="empty">暂无涨停前排样本。</div>`
      ),
      renderReviewModalSection(
        "炸板观察",
        burstRows.length
          ? renderReviewTable(
              [
                { key: "name", label: "股票", stockLink: true },
                { key: "pct_chg", label: "涨跌幅", format: formatSignedPercentValue },
                { key: "open_times", label: "开板次数", format: intValue },
                { key: "fd_amount", label: "封单额", format: formatAmountYi },
                { key: "strth", label: "强度", format: intValue },
              ],
              burstRows
            )
          : `<div class="empty">暂无炸板观察样本。</div>`
      ),
      renderReviewModalSection(
        "跌停风险",
        downRows.length
          ? renderReviewTable(
              [
                { key: "name", label: "股票", stockLink: true },
                { key: "pct_chg", label: "涨跌幅", format: formatSignedPercentValue },
                { key: "limit_times", label: "封板次数", format: intValue },
                { key: "open_times", label: "开板次数", format: intValue },
              ],
              downRows
            )
          : `<div class="empty">暂无跌停风险样本。</div>`
      ),
    ].join("");
  } else if (key === "ladder") {
    title = "连板天梯明细";
    meta = `复盘日期 ${formatDate(review.trade_date || "")} · 最高连板 ${intValue(review.summary?.highest_board)} 板`;
    body = (review.ladder || []).length
      ? renderReviewTable(
          [
            { key: "name", label: "股票", stockLink: true },
            { key: "continue_num", label: "连板", format: (value) => `${intValue(value)} 板` },
            { key: "limit_times", label: "涨停次数", format: intValue },
            { key: "pct_chg", label: "涨跌幅", format: formatSignedPercentValue },
            { key: "turnover_rate", label: "换手率", format: formatSignedPercentValue },
            { key: "amount", label: "成交额", format: formatAmountYi },
            { key: "concept", label: "概念" },
          ],
          review.ladder || []
        )
      : `<div class="empty">当天没有连板天梯数据。</div>`;
  }

  state.review.modalKey = key;
  state.review.modalSearch = "";
  els.reviewModalTitle.textContent = title;
  els.reviewModalMeta.textContent = meta;
  els.reviewModalBody.innerHTML = body;
  els.reviewModal.hidden = false;
  document.body.classList.add("modalOpen");
}

function closeReviewModal() {
  if (!els.reviewModal) return;
  state.review.modalKey = "";
  state.review.modalSearch = "";
  els.reviewModal.hidden = true;
  document.body.classList.remove("modalOpen");
}

function updateReviewInstitutionModalSearch(term) {
  const review = state.review.overview;
  if (!review || review.status !== "ok" || state.review.modalKey !== "hot_money_trades" || !els.reviewModalBody) return;
  state.review.modalSearch = String(term || "").trim();
  state.review.modalPage = 1;
  els.reviewModalBody.innerHTML = renderReviewInstitutionModal(review.hot_money_records || [], state.review.modalSearch, 1);
}

function applyReviewInstitutionModalSearch() {
  if (!els.reviewModalBody) return;
  const field = els.reviewModalBody.querySelector("[data-review-modal-search='hot-money']");
  updateReviewInstitutionModalSearch(field?.value || "");
}

function resetReviewInstitutionModalSearch() {
  updateReviewInstitutionModalSearch("");
}

function updateReviewHotMoneyPage(page) {
  state.review.hotMoneyPage = Math.max(1, intValue(page) || 1);
  renderReviewInstitution();
}

function updateReviewModalPage(page) {
  const review = state.review.overview;
  if (!review || review.status !== "ok" || state.review.modalKey !== "hot_money_trades" || !els.reviewModalBody) return;
  state.review.modalPage = Math.max(1, intValue(page) || 1);
  els.reviewModalBody.innerHTML = renderReviewInstitutionModal(
    review.hot_money_records || [],
    state.review.modalSearch || "",
    state.review.modalPage
  );
}

function renderReviewStockHeadline(item) {
  const canOpen = reviewRowCanOpen(item);
  const name = item?.name || "";
  const verdict = item?.verdict || "观察";
  if (!canOpen) {
    return `<strong>${escapeHtml(name)} <span class="reviewBadge">${escapeHtml(verdict)}</span></strong>`;
  }
  return `
    <strong
      class="reviewFocusHeading"
      data-review-open-analysis="1"
      data-ts-code="${escapeHtml(resolveReviewStockCode(item))}"
      data-name="${escapeHtml(name)}"
    >
      <span class="reviewFocusHeadingText">${escapeHtml(name)}</span>
      <span class="reviewBadge">${escapeHtml(verdict)}</span>
    </strong>
  `;
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
  const themes = overview.theme_ladders || [];
  const leaders = overview.leader_board || [];
  els.pickerMarketBox.className = "pickerSummaryGrid";
  els.pickerMarketBox.innerHTML = `
    <article class="pickerStageCard tone-${escapeHtml(stage.tone || "neutral")}">
      <div class="profileBlockHeader">
        <strong>养家市场温度</strong>
        <span class="profileVerdict tone-${escapeHtml(stage.tone || "neutral")}">${escapeHtml(stage.label || "未判断")}</span>
      </div>
      <div class="pickerGaugeRow">
        <span class="pickerGaugeLabel">${escapeHtml(stage.cycle || "阶段未明")}</span>
        <div class="pickerGaugeTrack"><span class="pickerGaugeFill tone-${escapeHtml(stage.tone || "neutral")}" style="width:${escapeHtml(String(stage.temperature || 0))}%"></span></div>
        <span class="pickerGaugeValue">${escapeHtml(String(stage.temperature || 0))}</span>
      </div>
      <p class="profileSummary">${escapeHtml(stage.summary || "")}</p>
      <p class="profileAction">${escapeHtml(stage.action || "")}</p>
      ${
        Array.isArray(stage.basis) && stage.basis.length
          ? `<div class="profileList"><span>判断依据</span><ul>${stage.basis.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`
          : ""
      }
      ${
        Array.isArray(stage.playbook) && stage.playbook.length
          ? `<div class="profileList"><span>当前玩法</span><ul>${stage.playbook.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`
          : ""
      }
      ${stage.warning ? `<p class="pickerWarningText">${escapeHtml(stage.warning)}</p>` : ""}
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
    <article class="pickerThemeBoard">
      <div class="profileBlockHeader">
        <strong>主流热点与梯队</strong>
        <span class="profileVerdict tone-neutral">${escapeHtml(themes.length ? `前 ${themes.length} 组` : "待生成")}</span>
      </div>
      ${
        themes.length
          ? `<div class="themeLadderList">
              ${themes.map(renderThemeLadderCard).join("")}
            </div>`
          : `<p class="mxCardMessage">当前样本里还没有足够清晰的热点梯队。</p>`
      }
    </article>
    <article class="pickerLeaderBoard">
      <div class="profileBlockHeader">
        <strong>龙头识别标签</strong>
        <span class="profileVerdict tone-neutral">${escapeHtml(leaders.length ? `${leaders.length} 个样本` : "待生成")}</span>
      </div>
      ${
        leaders.length
          ? `<div class="leaderBoardList">
              ${leaders.map(renderLeaderBoardRow).join("")}
            </div>`
          : `<p class="mxCardMessage">等待热点样本生成后，再标记龙头、前排和容量中军。</p>`
      }
    </article>
  `;
}

function renderThemeLadderCard(item) {
  const fronts = item.front_runners || [];
  return `
    <article class="themeLadderCard tone-${escapeHtml(item.tone || "neutral")}">
      <div class="profileBlockHeader">
        <strong>${escapeHtml(item.industry || "行业待定")}</strong>
        <span class="profileVerdict tone-${escapeHtml(item.tone || "neutral")}">${escapeHtml(item.tier_label || "轮动观察")}</span>
      </div>
      <p class="pickerCellText">${escapeHtml(item.summary || "")}</p>
      <dl class="miniStats">
        <dt>样本</dt><dd>${escapeHtml(String(item.sample_count || 0))} 只</dd>
        <dt>均涨幅</dt><dd>${escapeHtml(Number(item.avg_change_pct || 0).toFixed(2))}%</dd>
        <dt>强势数</dt><dd>${escapeHtml(String(item.strong_count || 0))}</dd>
        <dt>活跃数</dt><dd>${escapeHtml(String(item.active_count || 0))}</dd>
      </dl>
      <div class="themeRoleList">
        ${item.dragon ? `<span><b>龙头</b>${escapeHtml(`${item.dragon.name || ""} ${item.dragon.symbol || ""}`.trim())}</span>` : ""}
        ${item.capacity_core && item.capacity_core.symbol !== item.dragon?.symbol ? `<span><b>中军</b>${escapeHtml(`${item.capacity_core.name || ""} ${item.capacity_core.symbol || ""}`.trim())}</span>` : ""}
        ${
          fronts.length
            ? `<span><b>前排</b>${escapeHtml(
                fronts
                  .slice(0, 2)
                  .map((front) => `${front.name || ""} ${front.symbol || ""}`.trim())
                  .filter(Boolean)
                  .join("、")
              )}</span>`
            : ""
        }
      </div>
    </article>
  `;
}

function renderLeaderBoardRow(item) {
  const stock = item.stock || {};
  return `
    <article class="leaderBoardRow tone-${escapeHtml(item.tone || "neutral")}">
      <div class="profileBlockHeader">
        <strong>${escapeHtml(`${stock.name || ""} ${stock.symbol || ""}`.trim())}</strong>
        <span class="profileVerdict tone-${escapeHtml(item.tone || "neutral")}">${escapeHtml(item.role || "观察")}</span>
      </div>
      <p class="pickerCellText">${escapeHtml(item.industry || "")} · ${escapeHtml(item.tier_label || "")}</p>
      <small>${escapeHtml(item.summary || "")}</small>
    </article>
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

function renderPickerTable() {
  const screen = state.smartPicker.screen;
  if (!els.pickerTableBox) return;

  if (!screen) {
    els.pickerTableStatus.textContent = "候选池以手动同步东财自选或条件筛选结果为准。";
    if (els.pickerResultMeta) {
      els.pickerResultMeta.textContent = "默认不自动同步东财自选，点击“查询东财自选”后再生成候选池。";
    }
    els.pickerTableBox.innerHTML = `<div class="empty">默认不自动查询东财自选；点击“查询东财自选”或执行条件筛选后，这里再展示候选池。</div>`;
    return;
  }

  if (screen.status === "loading") {
    const isWatchlist = screen?.source_type === "watchlist";
    els.pickerTableStatus.textContent = isWatchlist ? "正在同步自选股并生成候选池..." : "正在生成候选池...";
    if (els.pickerResultMeta) {
      els.pickerResultMeta.textContent = isWatchlist ? "正在手动同步东财自选并生成候选池。" : "默认从全 A 股范围执行条件筛选。";
    }
    els.pickerTableBox.innerHTML = `
      <div class="pickerLoadingTable">
        <div class="mxSkeleton short"></div>
        <div class="mxSkeleton"></div>
        <div class="mxSkeleton"></div>
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
  const boardFilters = screen.board_filters || [];
  const isWatchlist = screen.source_type === "watchlist";
  const filterSummary = buildPickerFilterSummary(rawCandidates.length, candidates.length);
  els.pickerTableStatus.textContent = screen.description || screen.parser_text || `候选总数 ${screen.total || 0}`;
  if (els.pickerResultMeta) {
    const boardScope = boardFilters.length
      ? `已限定 ${boardFilters
          .map((item) => `${item.source_label || "板块"}${item.idx_type || "板块"}“${item.name || ""}”`)
          .join(" + ")}；`
      : "";
    const totalText = isWatchlist
      ? `我的自选共 ${screen.total || rawCandidates.length} 只`
      : boardFilters.length && !screen.query_text
      ? `板块成分股共 ${screen.total || rawCandidates.length} 只`
      : boardFilters.length
      ? `条件命中 ${screen.total || rawCandidates.length} 只`
      : universe.total
      ? `全 A 股 ${universe.total} 只股票中，条件命中 ${screen.total || rawCandidates.length} 只`
      : `条件命中 ${screen.total || rawCandidates.length} 只`;
    els.pickerResultMeta.textContent = `${boardScope}${totalText}；当前展示 ${candidates.length} 只。${filterSummary}`;
  }
  if (!candidates.length) {
    els.pickerTableBox.innerHTML = `<div class="empty">${
      isWatchlist ? "当前自选股没有生成可用候选，可以先检查自选同步或稍后重试。" : "当前条件下没有筛出可用候选，可以放宽条件再试一次。"
    }</div>`;
    return;
  }

  els.pickerTableBox.innerHTML = `
    <table class="pickerTable">
      <thead>
        <tr>
          <th>股票</th>
          <th>缠论结构</th>
          <th>主流梯队</th>
          <th>龙头标签</th>
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
                  <span class="profileVerdict tone-${escapeHtml(item.leader?.tone || "neutral")}">${escapeHtml(item.leader?.label || "")}</span>
                  <p class="pickerCellText">${escapeHtml(item.leader?.summary || "")}</p>
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
        ? `<div class="pickerHint">${
            isWatchlist && Number(screen.fallback_count || 0) > 0
              ? `有 ${screen.fallback_count} 只自选股暂缺结构数据，已先按自选行情展示；其余 ${screen.errors.length - screen.fallback_count} 条因股票匹配或数据缺失未展示。`
              : `有 ${screen.errors.length} 条结果因股票匹配或数据缺失被跳过，当前优先展示可用候选。`
          }</div>`
        : ""
    }
  `;
}

function buildPickerFilterSummary(rawCount, visibleCount) {
  const parts = [];
  const boardParts = [
    state.smartPicker.selectedBoard
      ? `东财=${state.smartPicker.selectedBoard.name}`
      : "",
    state.smartPicker.selectedTdxBoard
      ? `通达信=${state.smartPicker.selectedTdxBoard.name}`
      : "",
    state.smartPicker.selectedThsBoard
      ? `同花顺=${state.smartPicker.selectedThsBoard.name}`
      : "",
  ].filter(Boolean);
  if (boardParts.length) {
    parts.push(boardParts.join(" / "));
  }
  if (state.smartPicker.focusReadyOnly) {
    parts.push("已启用“主流强票”快捷筛选");
  }
  const screenFilterText = pickerScreenFilterSummary(state.smartPicker.screen?.filters || state.smartPicker.screenFilters);
  if (screenFilterText) {
    parts.push(screenFilterText);
  }
  if (state.smartPicker.marketScopeFilter !== "all") {
    parts.push(`市场=${pickerMarketScopeLabel(state.smartPicker.marketScopeFilter)}`);
  }
  if (state.smartPicker.structureFilter !== "all") {
    parts.push(`结构=${state.smartPicker.structureFilter}`);
  }
  if (state.smartPicker.emotionFilter !== "all") {
    parts.push(`热点=${state.smartPicker.emotionFilter}`);
  }
  if (state.smartPicker.leaderFilter !== "all") {
    parts.push(`龙头=${state.smartPicker.leaderFilter}`);
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

function boardTypeApiValue(source, value) {
  const mapping = {
    dc: { all: "", industry: "industry", concept: "concept", region: "region" },
    tdx: { all: "", industry: "industry", concept: "concept", style: "style", region: "region" },
    ths: { all: "", concept: "concept", industry: "industry", region: "region", feature: "feature", style: "style", theme: "theme", broad: "broad" },
  };
  return mapping[source]?.[value] ?? "";
}

function pickerMarketScopeLabel(value) {
  const mapping = {
    all: "全部市场",
    sz: "深证",
    sh: "上证",
    chinext: "创业板",
    star: "科创板",
    bse: "北交所",
  };
  return mapping[value] || "全部市场";
}

function pickerBoardDom(source) {
  const mapping = {
    dc: {
      source: "dc",
      typeInput: els.pickerBoardType,
      input: els.pickerBoardInput,
      options: els.pickerBoardOptions,
      selection: els.pickerBoardSelection,
      label: "东方财富",
      typeStateKey: "boardType",
      stateKey: "selectedBoard",
      matchesKey: "boardMatches",
      requestKey: "boardSearchRequestId",
    },
    tdx: {
      source: "tdx",
      typeInput: els.pickerTdxType,
      input: els.pickerTdxInput,
      options: els.pickerTdxOptions,
      selection: els.pickerTdxSelection,
      label: "通达信",
      typeStateKey: "tdxType",
      stateKey: "selectedTdxBoard",
      matchesKey: "tdxMatches",
      requestKey: "tdxSearchRequestId",
    },
    ths: {
      source: "ths",
      typeInput: els.pickerThsType,
      input: els.pickerThsInput,
      options: els.pickerThsOptions,
      selection: els.pickerThsSelection,
      label: "同花顺",
      typeStateKey: "thsType",
      stateKey: "selectedThsBoard",
      matchesKey: "thsMatches",
      requestKey: "thsSearchRequestId",
    },
  };
  return mapping[source];
}

function renderPickerBoardOptions(source, items = []) {
  const dom = pickerBoardDom(source);
  if (!dom?.options) return;
  dom.options.innerHTML = items
    .map(
      (item) =>
        `<option value="${escapeHtml(item.name || "")}" label="${escapeHtml(
          [item.idx_type || "", item.ts_code || ""].filter(Boolean).join(" · ")
        )}"></option>`
    )
    .join("");
}

function renderPickerBoardSelection(source) {
  const dom = pickerBoardDom(source);
  if (!dom?.selection) return;
  const board = state.smartPicker[dom.stateKey];
  if (!board) {
    dom.selection.textContent = `未限定${dom.label}板块。`;
    return;
  }
  dom.selection.textContent = `已限定${dom.label}${board.idx_type || "板块"}：${board.name || ""}（${board.ts_code || ""}），会只在该板块成分股里执行筛选。`;
}

function renderAllBoardSelections() {
  ["dc", "tdx", "ths"].forEach((source) => renderPickerBoardSelection(source));
}

async function searchPickerBoards(source, queryOverride = "", silent = false) {
  const dom = pickerBoardDom(source);
  if (!dom) return;
  const query = queryOverride || dom.input?.value.trim() || "";
  const boardType = dom.typeInput?.value || "all";
  if (!query) {
    state.smartPicker[dom.matchesKey] = [];
    renderPickerBoardOptions(source, []);
    if (!state.smartPicker[dom.stateKey]) {
      renderPickerBoardSelection(source);
    }
    return;
  }

  const requestId = ++state.smartPicker[dom.requestKey];
  try {
    const data = await fetchJson(
      `/api/boards/search?source=${encodeURIComponent(source)}&q=${encodeURIComponent(query)}&type=${encodeURIComponent(
        boardTypeApiValue(source, boardType)
      )}&limit=12`
    );
    if (requestId !== state.smartPicker[dom.requestKey]) return;
    state.smartPicker[dom.matchesKey] = data.items || [];
    renderPickerBoardOptions(source, state.smartPicker[dom.matchesKey]);
  } catch (err) {
    if (requestId !== state.smartPicker[dom.requestKey]) return;
    state.smartPicker[dom.matchesKey] = [];
    renderPickerBoardOptions(source, []);
    if (!silent) {
      showPickerError(err.message);
    }
  }
}

function debouncePickerBoardSearch(source) {
  window.clearTimeout(pickerBoardTimer);
  pickerBoardTimer = window.setTimeout(() => {
    searchPickerBoards(source);
  }, 200);
}

function ensurePickerBoardSelection(source, queryText) {
  const dom = pickerBoardDom(source);
  if (!dom) return null;
  const query = String(queryText || "").trim();
  if (!query) {
    state.smartPicker[dom.stateKey] = null;
    renderPickerBoardSelection(source);
    return null;
  }
  const existing = state.smartPicker[dom.stateKey];
  if (existing && [existing.name, existing.ts_code].includes(query)) {
    return existing;
  }
  const normalized = query.toUpperCase();
  const picked =
    (state.smartPicker[dom.matchesKey] || []).find(
      (item) => normalized === String(item.ts_code || "").toUpperCase() || query === String(item.name || "")
    ) ||
    (state.smartPicker[dom.matchesKey] || [])[0];
  if (!picked) return null;
  state.smartPicker[dom.stateKey] = picked;
  if (dom.input) {
    dom.input.value = picked.name || "";
  }
  renderPickerBoardSelection(source);
  return picked;
}

function pickerSortLabel(sortBy) {
  const mapping = {
    overall_score: "综合分",
    structure_score: "结构分",
    theme_score: "热点分",
    leader_score: "龙头分",
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
    items = items.filter((item) => item.structure?.label === "结构可看" && item.emotion?.label === "主流热点");
  }
  if (state.smartPicker.marketScopeFilter !== "all") {
    items = items.filter((item) => matchesPickerMarketScope(item.stock || {}, state.smartPicker.marketScopeFilter));
  }
  if (state.smartPicker.structureFilter !== "all") {
    items = items.filter((item) => item.structure?.label === state.smartPicker.structureFilter);
  }
  if (state.smartPicker.emotionFilter !== "all") {
    items = items.filter((item) => item.emotion?.label === state.smartPicker.emotionFilter);
  }
  if (state.smartPicker.leaderFilter !== "all") {
    items = items.filter((item) => item.leader?.label === state.smartPicker.leaderFilter);
  }
  if (state.smartPicker.overallFilter !== "all") {
    items = items.filter((item) => item.overall?.label === state.smartPicker.overallFilter);
  }

  const direction = state.smartPicker.sortDirection === "asc" ? 1 : -1;
  const sortBy = state.smartPicker.sortBy;
  items.sort((left, right) => comparePickerCandidate(left, right, sortBy) * direction);
  return items;
}

function matchesPickerMarketScope(stock, scope) {
  const exchange = String(stock?.exchange || "").toUpperCase();
  const market = String(stock?.market || "");
  const tsCode = String(stock?.ts_code || "").toUpperCase();
  const symbol = String(stock?.symbol || "");

  switch (scope) {
    case "sz":
      return exchange === "SZSE" || tsCode.endsWith(".SZ");
    case "sh":
      return exchange === "SSE" || tsCode.endsWith(".SH");
    case "chinext":
      return market.includes("创业板") || symbol.startsWith("300") || tsCode.startsWith("300");
    case "star":
      return market.includes("科创板") || symbol.startsWith("688") || tsCode.startsWith("688");
    case "bse":
      return exchange === "BSE" || exchange === "BJSE" || market.includes("北交所") || tsCode.endsWith(".BJ") || symbol.startsWith("4") || symbol.startsWith("8");
    default:
      return true;
  }
}

function comparePickerCandidate(left, right, sortBy) {
  if (sortBy === "name") {
    return String(left.stock?.name || "").localeCompare(String(right.stock?.name || ""), "zh-Hans-CN");
  }

  const valueOf = (item) => {
    switch (sortBy) {
      case "structure_score":
        return Number(item.structure?.score || 0);
      case "theme_score":
        return Number(item.emotion?.score || 0);
      case "leader_score":
        return Number(item.leader?.score || 0);
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
    els.pickerDetailBox.textContent = "点击候选池中的自选股，这里会展开三视角交易画像和自选操作。";
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
  const candidate = currentPickerCandidate();
  const execution = detail.execution || {};

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
    ${renderPickerTacticalCard(candidate, state.smartPicker.screen?.stage)}
    ${renderExecutionPlanCard(execution.plan)}
    ${renderDisciplineCard(execution.discipline)}
    ${renderReviewCard(execution.review)}
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
      <p class="mxCardMessage">${escapeHtml(analysis.message || analysis.trend?.reason || "暂无补充结构说明。")}</p>
    </article>
    ${renderMarketScan(profilePayload.market_scan)}
    ${renderNewsDigest(profilePayload.news)}
    ${mxCards}
  `;
}

function currentPickerCandidate() {
  const tsCode = state.smartPicker.selectedTsCode;
  return (state.smartPicker.screen?.candidates || []).find((item) => item.stock?.ts_code === tsCode) || null;
}

function renderPickerTacticalCard(candidate, stage) {
  if (!candidate) return "";
  return `
    <article class="mxCard status-ok pickerTacticalCard">
      <div class="mxCardHeader">
        <strong>养家战术卡</strong>
        <small>${escapeHtml(stage?.cycle || "阶段未明")}</small>
      </div>
      <div class="pickerTacticalGrid">
        <div class="pickerTacticalItem">
          <span>市场阶段</span>
          <strong class="tone-${escapeHtml(stage?.tone || "neutral")}">${escapeHtml(stage?.label || "未判断")}</strong>
          <small>${escapeHtml(stage?.action || "")}</small>
        </div>
        <div class="pickerTacticalItem">
          <span>主流梯队</span>
          <strong class="tone-${escapeHtml(candidate.emotion?.tone || "neutral")}">${escapeHtml(candidate.emotion?.label || "未归类")}</strong>
          <small>${escapeHtml(candidate.emotion?.summary || "")}</small>
        </div>
        <div class="pickerTacticalItem">
          <span>龙头角色</span>
          <strong class="tone-${escapeHtml(candidate.leader?.tone || "neutral")}">${escapeHtml(candidate.leader?.label || "待判断")}</strong>
          <small>${escapeHtml(candidate.leader?.summary || "")}</small>
        </div>
        <div class="pickerTacticalItem">
          <span>当前结论</span>
          <strong class="tone-${escapeHtml(candidate.overall?.tone || "neutral")}">${escapeHtml(candidate.overall?.label || "先观察")}</strong>
          <small>${escapeHtml(candidate.overall?.decision || "")}</small>
        </div>
      </div>
    </article>
  `;
}

function renderExecutionPlanCard(plan) {
  if (!plan) return "";
  return `
    <article class="mxCard status-ok executionCard">
      <div class="mxCardHeader">
        <strong>${escapeHtml(plan.title || "交易计划")}</strong>
        <small>${escapeHtml(plan.setup || "等待确认型")}</small>
      </div>
      <div class="profileBlockHeader">
        <strong class="tone-${escapeHtml(plan.tone || "neutral")}">${escapeHtml(plan.verdict || "先观察")}</strong>
        ${
          plan.invalidation_price !== undefined && plan.invalidation_price !== null
            ? `<span class="aiMetaText">失效价 ${escapeHtml(formatPrice(plan.invalidation_price))}</span>`
            : ""
        }
      </div>
      <p class="mxCardTitle">${escapeHtml(plan.summary || "")}</p>
      <p class="profileAction">${escapeHtml(plan.action || "")}</p>
      <div class="executionMetaRow">
        <span class="profileVerdict tone-${escapeHtml(plan.tone || "neutral")}">${escapeHtml(plan.position_hint || "先看计划再谈仓位")}</span>
      </div>
      ${renderAiListBlock("计划依据", plan.basis)}
      ${renderAiListBlock("观察重点", plan.watch_points)}
      ${renderAiListBlock("取消条件", plan.avoid_if)}
    </article>
  `;
}

function renderDisciplineCard(discipline) {
  if (!discipline) return "";
  const checks = Array.isArray(discipline.checks) ? discipline.checks : [];
  return `
    <article class="mxCard status-ok disciplineCard">
      <div class="mxCardHeader">
        <strong>${escapeHtml(discipline.title || "纪律引擎")}</strong>
        <small>${escapeHtml(String(discipline.score ?? "--"))} 分</small>
      </div>
      <div class="profileBlockHeader">
        <strong class="tone-${escapeHtml(discipline.tone || "neutral")}">${escapeHtml(discipline.label || "先观察")}</strong>
        <span class="profileVerdict tone-${escapeHtml(discipline.tone || "neutral")}">${escapeHtml(discipline.position_hint || "")}</span>
      </div>
      <p class="mxCardTitle">${escapeHtml(discipline.summary || "")}</p>
      <p class="mxCardMessage">${escapeHtml(discipline.next_step || "")}</p>
      ${
        checks.length
          ? `<div class="disciplineChecklist">
              ${checks
                .map(
                  (item) => `
                    <article class="disciplineCheck ${item.passed ? "pass" : "hold"}">
                      <div class="disciplineCheckHeader">
                        <strong>${escapeHtml(item.label || "")}</strong>
                        <span class="profileVerdict tone-${item.passed ? "positive" : "caution"}">${item.passed ? "通过" : "待确认"}</span>
                      </div>
                      <p>${escapeHtml(item.detail || "")}</p>
                    </article>
                  `
                )
                .join("")}
            </div>`
          : ""
      }
    </article>
  `;
}

function renderReviewCard(review) {
  if (!review) return "";
  const cases = Array.isArray(review.recent_cases) ? review.recent_cases : [];
  return `
    <article class="mxCard status-ok reviewCard">
      <div class="mxCardHeader">
        <strong>${escapeHtml(review.title || "复盘系统")}</strong>
        <small>${escapeHtml(review.label || "样本不足")}</small>
      </div>
      <p class="mxCardTitle tone-${escapeHtml(review.tone || "neutral")}">${escapeHtml(review.summary || "")}</p>
      ${renderAiListBlock("复盘结论", review.lessons)}
      ${
        cases.length
          ? `<div class="reviewCaseList">
              ${cases
                .map(
                  (item) => `
                    <article class="reviewCaseItem">
                      <div class="disciplineCheckHeader">
                        <strong>${escapeHtml(item.label || "")} ${escapeHtml(formatDate(item.date || ""))}</strong>
                        <span class="profileVerdict tone-neutral">${escapeHtml(item.outcome || "待观察")}</span>
                      </div>
                      <p>顺向 ${escapeHtml(`${Number(item.forward_pct || 0).toFixed(2)}%`)} / 逆向 ${escapeHtml(`${Number(item.adverse_pct || 0).toFixed(2)}%`)} / 收盘 ${escapeHtml(`${Number(item.close_return_pct || 0).toFixed(2)}%`)}</p>
                    </article>
                  `
                )
                .join("")}
            </div>`
          : ""
      }
      <p class="mxCardMessage">${escapeHtml(review.note || "")}</p>
    </article>
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
  const maPlot = plots.ma;
  const macdPlot = plots.macd;
  const visibleCenters = replayItemsByEnd(analysis.centers || [], "end_index").filter((item) => overlapsWindow(item.start_index, item.end_index, view));
  const visibleMacd = (analysis.indicators?.macd || []).slice(view.start, view.end);
  const visibleBbi = (analysis.indicators?.bbi || []).slice(view.start, view.end);
  const visibleMa5 = (analysis.indicators?.ma5 || []).slice(view.start, view.end);
  const visibleMa10 = (analysis.indicators?.ma10 || []).slice(view.start, view.end);
  const visibleMa20 = (analysis.indicators?.ma20 || []).slice(view.start, view.end);
  const visibleMaCenters = visibleItems(replayItemsByEnd(analysis.ma_centers || [], "end_index"), "start_index", "end_index", view);
  const visibleKlinePatterns = visibleIndexSignals(replayFilteredIndexSignals(analysis.kline_patterns || []), view);
  const weakToStrongSet = buildWeakToStrongSet(analysis);
  const range = priceRange(visibleKlines, visibleCenters, visibleBbi);
  const maRange = movingAverageRange(visibleKlines, visibleMa5, visibleMa10, visibleMa20, visibleMaCenters);
  const x = (idx) => plot.left + ((idx - view.start + 0.5) / view.count) * plot.width;
  const y = (price) => plot.top + ((range.high - price) / (range.high - range.low)) * plot.height;
  const maY = (price) => maPlot.top + ((maRange.high - price) / (maRange.high - maRange.low)) * maPlot.height;
  const candleW = Math.max(4, Math.min(13, (plot.width / view.count) * 0.62));

  drawGrid(ctx, rect, plot, range, visibleKlines, x, false);
  drawCenters(ctx, visibleCenters, x, y, plot);
  drawCandles(ctx, visibleKlines, x, y, candleW, weakToStrongSet);
  drawBbi(ctx, visibleBbi, x, y);
  if (state.showStrokes) {
    drawStrokes(ctx, visibleItems(replayItemsByEnd(analysis.strokes || [], "end_index"), "start_index", "end_index", view), x, y, view);
    drawActiveStroke(ctx, analysis.active_stroke, x, y, view);
  }
  if (state.showSegments) {
    drawSegments(ctx, visibleItems(replayItemsByEnd(analysis.segments || [], "end_index"), "start_index", "end_index", view), x, y, view);
  }
  drawFractals(ctx, visibleItems(replayItemsByEnd(analysis.fractals || [], "raw_index"), "raw_index", "raw_index", view), x, y);
  drawSignals(ctx, visibleSignals(replayFilteredSignals(analysis.signals || []), view), x, y, plot);
  drawGrid(ctx, rect, maPlot, maRange, visibleKlines, x, false);
  drawMaCenters(ctx, visibleMaCenters, x, maY, maPlot);
  drawCandles(ctx, visibleKlines, x, maY, Math.max(3, candleW * 0.72), weakToStrongSet, 0.18);
  drawMovingAverageLines(ctx, x, maY, [
    { key: "MA5", rows: visibleMa5, color: "#f59e0b" },
    { key: "MA10", rows: visibleMa10, color: "#2563eb" },
    { key: "MA20", rows: visibleMa20, color: "#7c3aed" },
  ]);
  drawKlinePatterns(ctx, visibleKlinePatterns, x, maY, maPlot);
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
  const gap = 24;
  const usableHeight = Math.max(620, rect.height - top - bottom - gap * 2);
  const mainHeight = Math.max(320, Math.min(usableHeight * 0.54, usableHeight - 260));
  const maHeight = Math.max(160, Math.min(220, usableHeight * 0.24));
  const macdHeight = Math.max(140, usableHeight - mainHeight - maHeight);
  const width = rect.width - left - right;
  return {
    main: { left, right, top, bottom: rect.height - top - mainHeight, width, height: mainHeight },
    ma: {
      left,
      right,
      top: top + mainHeight + gap,
      bottom: rect.height - (top + mainHeight + gap + maHeight),
      width,
      height: maHeight,
    },
    macd: {
      left,
      right,
      top: top + mainHeight + gap + maHeight + gap,
      bottom,
      width,
      height: Math.max(72, rect.height - (top + mainHeight + gap + maHeight + gap) - bottom),
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

function drawCandles(ctx, klines, x, y, candleW, weakToStrongSet = new Set(), fillAlpha = 0.22) {
  klines.forEach((bar) => {
    const up = bar.close >= bar.open;
    const weakToStrong = weakToStrongSet.has(bar.index);
    const color = weakToStrong ? "#c7a100" : up ? "#c24136" : "#14845f";
    const fill = weakToStrong
      ? `rgba(199, 161, 0, ${Math.max(fillAlpha, 0.18)})`
      : up
        ? `rgba(194, 65, 54, ${fillAlpha})`
        : `rgba(20, 132, 95, ${fillAlpha})`;
    const px = x(bar.index);
    const openY = y(bar.open);
    const closeY = y(bar.close);
    const highY = y(bar.high);
    const lowY = y(bar.low);
    ctx.strokeStyle = color;
    ctx.fillStyle = fill;
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

function drawMovingAverageLines(ctx, x, y, lines) {
  lines.forEach(({ key, rows, color }) => {
    const validRows = (rows || []).filter((item) => item.value !== null && item.value !== undefined && Number.isFinite(Number(item.value)));
    if (validRows.length < 2) return;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    validRows.forEach((item, idx) => {
      const px = x(item.index);
      const py = y(item.value);
      if (idx === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    const last = validRows[validRows.length - 1];
    ctx.fillStyle = color;
    ctx.font = "11px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(key, x(last.index) + 5, y(last.value));
  });
  ctx.lineWidth = 1;
}

function drawMaCenters(ctx, centers, x, y, plot) {
  centers.forEach((item) => {
    const left = Math.max(plot.left, x(Math.min(item.start_index, item.end_index)));
    const right = Math.min(plot.left + plot.width, x(Math.max(item.start_index, item.end_index)));
    const top = y(item.high);
    const bottom = y(item.low);
    if (right < plot.left || left > plot.left + plot.width) return;
    ctx.fillStyle = "rgba(37, 99, 235, 0.08)";
    ctx.strokeStyle = "rgba(37, 99, 235, 0.42)";
    ctx.fillRect(left, top, Math.max(right - left, 4), Math.max(bottom - top, 2));
    ctx.strokeRect(left, top, Math.max(right - left, 4), Math.max(bottom - top, 2));
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

function drawKlinePatterns(ctx, patterns, x, y, plot) {
  patterns.forEach((item) => {
    drawPatternTag(ctx, {
      x: x(item.index),
      y: y(item.price),
      label: item.label || "形态",
      direction: item.direction || "neutral",
      tone: item.tone || "neutral",
      focus: Boolean(item.focus),
      plot,
    });
  });
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

function drawActiveStroke(ctx, item, x, y, view) {
  if (!item || !overlapsWindow(item.start_index, item.end_index, view)) return;
  ctx.lineWidth = 2.2;
  ctx.strokeStyle = item.direction === "up" ? "rgba(169, 53, 45, 0.7)" : "rgba(15, 111, 82, 0.7)";
  ctx.setLineDash([7, 4]);
  ctx.beginPath();
  ctx.moveTo(x(item.start_index), y(item.start_price));
  ctx.lineTo(x(item.end_index), y(item.end_price));
  ctx.stroke();
  ctx.setLineDash([]);
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
    drawSegmentFeatureSequence(ctx, item, x, y, view);
  });
  ctx.setLineDash([]);
  ctx.lineWidth = 1;
}

function drawSegmentFeatureSequence(ctx, segment, x, y, view) {
  const features = Array.isArray(segment.feature_sequence) ? segment.feature_sequence : [];
  const featureColor = segment.direction === "up" ? "rgba(31, 118, 255, 0.82)" : "rgba(139, 92, 246, 0.82)";
  const gapColor = segment.direction === "up" ? "rgba(245, 158, 11, 0.86)" : "rgba(16, 185, 129, 0.86)";

  features.forEach((item) => {
    if (!overlapsWindow(item.start_index, item.end_index, view)) return;
    const left = x(item.start_index);
    const right = x(item.end_index);
    const top = Math.min(y(item.high), y(item.low)) - 4;
    const bottom = Math.max(y(item.high), y(item.low)) + 4;
    ctx.save();
    ctx.strokeStyle = featureColor;
    ctx.lineWidth = 1.4;
    ctx.setLineDash([4, 3]);
    ctx.strokeRect(left - 3, top, Math.max(right - left + 6, 8), Math.max(bottom - top, 10));
    ctx.restore();
  });

  const gap = segment.feature_gap || {};
  if (!gap.direction || !overlapsWindow(gap.start_index, gap.end_index, view)) return;
  const left = x(gap.start_index);
  const right = x(gap.end_index);
  const top = y(gap.high);
  const bottom = y(gap.low);
  const centerY = (top + bottom) / 2;

  ctx.save();
  ctx.strokeStyle = gapColor;
  ctx.lineWidth = 1.6;
  ctx.setLineDash([2, 2]);
  ctx.beginPath();
  ctx.moveTo(left, centerY);
  ctx.lineTo(right, centerY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.moveTo(left, top);
  ctx.lineTo(left, bottom);
  ctx.moveTo(right, top);
  ctx.lineTo(right, bottom);
  ctx.stroke();
  ctx.restore();
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

function drawSignalTag(ctx, { x, y, label, buy, plot, compact = false }) {
  const { tagX, tagY, width, height } = signalTagBounds(x, y, buy, plot, compact);
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
  ctx.font = compact ? "600 11px sans-serif" : "600 12px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, tagX + width / 2, tagY + height / 2 + 0.5);

  ctx.fillStyle = color;
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(x, y, compact ? 3 : 3.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth = 1;
}

function drawPatternTag(ctx, { x, y, label, direction, tone, focus, plot }) {
  const above = direction !== "down";
  const { tagX, tagY, width, height } = patternTagBounds(x, y, label, above, plot);
  const color = patternToneColor(tone);

  ctx.fillStyle = color;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
  ctx.lineWidth = focus ? 2 : 1;
  roundedRect(ctx, tagX, tagY, width, height, 4);
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth = 1;

  ctx.beginPath();
  if (above) {
    const baseY = tagY + height;
    ctx.moveTo(x, Math.max(y - 1, plot.top));
    ctx.lineTo(Math.max(tagX + 8, x - 5), baseY);
    ctx.lineTo(Math.min(tagX + width - 8, x + 5), baseY);
  } else {
    const baseY = tagY;
    ctx.moveTo(x, Math.min(y + 1, plot.top + plot.height));
    ctx.lineTo(Math.max(tagX + 8, x - 5), baseY);
    ctx.lineTo(Math.min(tagX + width - 8, x + 5), baseY);
  }
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#fff";
  ctx.font = "600 11px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, tagX + width / 2, tagY + height / 2 + 0.5);

  ctx.fillStyle = color;
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.arc(x, y, 3.3, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth = 1;
}

function signalTagBounds(x, y, buy, plot, compact = false) {
  const width = compact ? 28 : 34;
  const height = compact ? 18 : 20;
  const pointer = compact ? 5 : 6;
  const gap = compact ? 5 : 7;
  const tagX = Math.max(plot.left + 2, Math.min(x - width / 2, plot.left + plot.width - width - 2));
  const idealY = buy ? y + gap + pointer : y - gap - pointer - height;
  const tagY = Math.max(plot.top + 2, Math.min(idealY, plot.top + plot.height - height - 2));
  return { tagX, tagY, width, height };
}

function patternTagBounds(x, y, label, above, plot) {
  const metrics = patternTagMetrics(label);
  const pointer = 6;
  const gap = 7;
  const tagX = Math.max(plot.left + 2, Math.min(x - metrics.width / 2, plot.left + plot.width - metrics.width - 2));
  const idealY = above ? y - gap - pointer - metrics.height : y + gap + pointer;
  const tagY = Math.max(plot.top + 2, Math.min(idealY, plot.top + plot.height - metrics.height - 2));
  return { tagX, tagY, width: metrics.width, height: metrics.height };
}

function patternTagMetrics(label) {
  return {
    width: Math.max(48, Math.min(86, String(label || "").length * 13 + 18)),
    height: 20,
  };
}

function patternToneColor(tone) {
  if (tone === "positive") return "#c24136";
  if (tone === "caution") return "#14845f";
  return "#256f92";
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

function movingAverageRange(klines, ma5Rows = [], ma10Rows = [], ma20Rows = [], centers = []) {
  const maValues = [ma5Rows, ma10Rows, ma20Rows]
    .flat()
    .map((item) => item?.value)
    .filter((value) => value !== null && value !== undefined && Number.isFinite(Number(value)));
  const highs = klines.map((item) => item.high).concat(centers.map((item) => item.high), maValues);
  const lows = klines.map((item) => item.low).concat(centers.map((item) => item.low), maValues);
  const high = Math.max(...highs);
  const low = Math.min(...lows);
  const padding = Math.max((high - low) * 0.09, high * 0.006, 0.01);
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

function replayFilteredIndexSignals(signals) {
  const cutoff = replayCutoffIndex();
  if (cutoff < 0) return [];
  return signals.filter((item) => Number(item.index) <= cutoff);
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

function visibleIndexSignals(signals, view) {
  return signals.filter((item) => item.index >= view.start && item.index < view.end);
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
  if (y >= plots.ma.top && y <= plots.ma.top + plots.ma.height) return "ma";
  if (y >= plots.macd.top && y <= plots.macd.top + plots.macd.height) return "macd";
  return "gap";
}

function positionTooltip(event, width = 220, height = 140) {
  const rect = els.canvas.getBoundingClientRect();
  els.tooltip.style.left = `${clamp(event.clientX - rect.left + 12, 8, rect.width - width)}px`;
  els.tooltip.style.top = `${clamp(event.clientY - rect.top - 20, 12, rect.height - height)}px`;
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

function klinePatternFromPointer(event, analysis) {
  const rect = els.canvas.getBoundingClientRect();
  const plots = chartPlots(rect);
  const plot = plots.ma;
  const pointerX = event.clientX - rect.left;
  const pointerY = event.clientY - rect.top;
  if (pointerY < plot.top || pointerY > plot.top + plot.height) return null;

  const view = visibleWindow();
  const visibleKlines = analysis.klines.slice(view.start, view.end);
  const visibleMa5 = (analysis.indicators?.ma5 || []).slice(view.start, view.end);
  const visibleMa10 = (analysis.indicators?.ma10 || []).slice(view.start, view.end);
  const visibleMa20 = (analysis.indicators?.ma20 || []).slice(view.start, view.end);
  const visibleMaCenters = visibleItems(replayItemsByEnd(analysis.ma_centers || [], "end_index"), "start_index", "end_index", view);
  const range = movingAverageRange(visibleKlines, visibleMa5, visibleMa10, visibleMa20, visibleMaCenters);
  const x = (idx) => plot.left + ((idx - view.start + 0.5) / view.count) * plot.width;
  const y = (price) => plot.top + ((range.high - price) / (range.high - range.low)) * plot.height;
  const candidates = visibleIndexSignals(replayFilteredIndexSignals(analysis.kline_patterns || []), view);
  const barHit = Math.max(10, plot.width / view.count);

  let best = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const item of candidates) {
    const px = x(item.index);
    const py = y(item.price);
    const bounds = patternTagBounds(px, py, item.label || "形态", item.direction !== "down", plot);
    const insideTag =
      pointerX >= bounds.tagX - 4 &&
      pointerX <= bounds.tagX + bounds.width + 4 &&
      pointerY >= bounds.tagY - 4 &&
      pointerY <= bounds.tagY + bounds.height + 4;
    const nearAnchor = Math.abs(pointerX - px) <= barHit && Math.abs(pointerY - py) <= 16;
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
  positionTooltip(event, 280, 180);
  els.tooltip.innerHTML = `
    <strong>${signalLabel(signal)} · ${formatDate(signal.date)}</strong><br>
    状态 ${signal.status_label || "候选"} · 价格 ${formatPrice(signal.price)}<br>
    失效 ${formatPrice(signal.invalidation_price)}<br>
    ${signal.reason || ""}<br>
    <span class="tooltipNote">${signal.confirmation || ""}</span>
    ${signal.observation ? `<br><span class="tooltipNote">${signal.observation}</span>` : ""}
  `;
}

function showKlinePatternTooltip(event, pattern) {
  els.tooltip.hidden = false;
  positionTooltip(event, 260, 140);
  const strength = Number(pattern.strength);
  const direction = pattern.direction === "down" ? "偏空/风险" : pattern.direction === "up" ? "偏多/转强" : "中性";
  const strengthLabel = Number.isFinite(strength) ? `${(Math.abs(strength) * 100).toFixed(2)}%` : "-";
  els.tooltip.innerHTML = `
    <strong>${pattern.label || "K线形态"} · ${formatDate(pattern.date)}</strong><br>
    范围 ${pattern.scope_label || "近期形态"} · 方向 ${direction}<br>
    参考价 ${formatPrice(pattern.price)}<br>
    强度 ${strengthLabel}<br>
    ${pattern.reason || ""}
  `;
}

function showMainTooltip(event, analysis, idx) {
  const bar = analysis.klines[idx];
  const macd = analysis.indicators?.macd?.[idx];
  const bbi = analysis.indicators?.bbi?.[idx];
  const ma5 = analysis.indicators?.ma5?.[idx];
  const ma10 = analysis.indicators?.ma10?.[idx];
  const ma20 = analysis.indicators?.ma20?.[idx];
  const changePct = barChangePct(analysis.klines, idx);
  const weakToStrong = isWeakToStrongBar(analysis, idx);
  const weakToStrongReasons = weakToStrong ? weakToStrongReasonList(analysis, idx) : [];

  els.tooltip.hidden = false;
  positionTooltip(event, weakToStrongReasons.length ? 320 : 240, weakToStrongReasons.length ? 210 : 150);
  els.tooltip.innerHTML = `
    <strong>${formatDate(bar.date)}</strong><br>
    开 ${formatPrice(bar.open)} 高 ${formatPrice(bar.high)}<br>
    低 ${formatPrice(bar.low)} 收 ${formatPrice(bar.close)}<br>
    涨跌幅 ${changePct === null ? "-" : formatSignedPercent(changePct)}${weakToStrong ? " · 弱转强黄K" : ""}<br>
    BBI ${bbi?.value !== null && bbi?.value !== undefined ? formatPrice(bbi.value) : "-"}<br>
    MA5 ${ma5?.value !== null && ma5?.value !== undefined ? formatPrice(ma5.value) : "-"} · MA10 ${ma10?.value !== null && ma10?.value !== undefined ? formatPrice(ma10.value) : "-"} · MA20 ${ma20?.value !== null && ma20?.value !== undefined ? formatPrice(ma20.value) : "-"}<br>
    量 ${Math.round(bar.vol).toLocaleString()}<br>
    MACD ${macd ? formatMacd(macd.hist) : "-"} · DIF ${macd ? formatMacd(macd.dif) : "-"} · DEA ${macd ? formatMacd(macd.dea) : "-"}
    ${
      weakToStrongReasons.length
        ? `<dl class="evidenceGrid"><dt>弱转强依据</dt><dd>${escapeHtml(weakToStrongReasons.join("、"))}</dd></dl>`
        : ""
    }
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
  positionTooltip(event, 360, 320);
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

function todayInputValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function normalizeDateInput(value) {
  return String(value || "").replaceAll("-", "");
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

function formatSignedPercent(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
}

function formatSignedPercentValue(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return String(value || "-");
  return `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
}

function formatAmountYi(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return `${(num / 100000000).toFixed(2)} 亿`;
}

function formatPlainNumber(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 }).format(num);
}

function formatVolumeHand(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return `${trimZeroes((num / 100).toFixed(0))} 手`;
}

function formatCompactValue(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return trimZeroes(num.toFixed(2));
}

function formatCompactShare(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return `${trimZeroes(num.toFixed(2))} 亿股`;
}

function formatSignedCompact(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return `${num > 0 ? "+" : ""}${trimZeroes(num.toFixed(1))}%`;
}

function formatHolderCount(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  if (num >= 10000) return `${trimZeroes((num / 10000).toFixed(2))}万户`;
  return `${Math.round(num)}户`;
}

function formatSignedAmountShort(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  const sign = num > 0 ? "+" : num < 0 ? "-" : "";
  const abs = Math.abs(num);
  if (abs >= 100000000) return `${sign}${trimZeroes((abs / 100000000).toFixed(2))}亿`;
  if (abs >= 10000) return `${sign}${trimZeroes((abs / 10000).toFixed(0))}万`;
  return `${sign}${trimZeroes(abs.toFixed(0))}`;
}

function intValue(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "0";
  return String(Math.round(num));
}

function barChangePct(klines, idx) {
  if (!Array.isArray(klines) || idx <= 0 || idx >= klines.length) return null;
  const prevClose = Number(klines[idx - 1]?.close);
  const close = Number(klines[idx]?.close);
  if (!Number.isFinite(prevClose) || !Number.isFinite(close) || prevClose === 0) return null;
  return ((close - prevClose) / prevClose) * 100;
}

function buildWeakToStrongSet(analysis) {
  const bars = analysis?.klines || [];
  const bbiMap = buildBbiValueMap(analysis?.indicators?.bbi || []);
  const flagged = new Set();
  bars.forEach((bar, idx) => {
    if (evaluateWeakToStrong(bars, bbiMap, idx).matched) {
      flagged.add(bar.index);
    }
  });
  return flagged;
}

function isWeakToStrongBar(analysis, idx) {
  const bars = analysis?.klines || [];
  const bbiMap = buildBbiValueMap(analysis?.indicators?.bbi || []);
  return evaluateWeakToStrong(bars, bbiMap, idx).matched;
}

function buildBbiValueMap(rows) {
  return new Map(
    (rows || []).map((item) => [item.index, item.value === null || item.value === undefined ? Number.NaN : Number(item.value)])
  );
}

// 游资视角的“弱转强”先用轻量规则近似：先有回踩走弱，再出现放量、近高收盘和强势反包。
function evaluateWeakToStrong(bars, bbiMap, idx) {
  if (!Array.isArray(bars) || idx < 3 || idx >= bars.length) return { matched: false, reasons: [] };
  const bar = bars[idx];
  const prev = bars[idx - 1];
  const prev2 = bars[idx - 2];
  const prev3 = bars[idx - 3];
  if (!bar || !prev || !prev2 || !prev3) return { matched: false, reasons: [] };
  if (!(Number(bar.close) > Number(bar.open) && Number(bar.close) > Number(prev.close))) {
    return { matched: false, reasons: [] };
  }

  let weakCount = 0;
  for (let cursor = idx - 3; cursor < idx; cursor += 1) {
    if (cursor <= 0) continue;
    if (Number(bars[cursor].close) <= Number(bars[cursor - 1].close)) weakCount += 1;
  }

  const range = Math.max(Number(bar.high) - Number(bar.low), 0.001);
  const closeNearHigh = (Number(bar.high) - Number(bar.close)) / range <= 0.28;
  const changePct = barChangePct(bars, idx) ?? 0;
  const breakPrevHigh = Number(bar.close) > Number(prev.high) || Number(bar.high) > Math.max(Number(prev.high), Number(prev2.high));
  const volumeExpand = Number(prev.vol) > 0 ? Number(bar.vol) >= Number(prev.vol) * 1.15 : false;
  const currentBbi = bbiMap.get(bar.index);
  const prevBbi = bbiMap.get(prev.index);
  const recoverBbi =
    Number.isFinite(currentBbi) &&
    Number.isFinite(prevBbi) &&
    Number(bar.close) >= Number(currentBbi) &&
    Number(prev.close) < Number(prevBbi);
  const reclaimAverage = Number(bar.close) > average([prev.close, prev2.close, prev3.close].map(Number).filter(Number.isFinite));
  const recentPullback = weakCount >= 2 || Number(prev.close) < Number(prev.open);
  const strongBreakout = breakPrevHigh || changePct >= 3.5;
  const supportCount = [volumeExpand, recoverBbi, reclaimAverage].filter(Boolean).length;
  const matched = recentPullback && closeNearHigh && strongBreakout && supportCount >= 1;
  if (!matched) return { matched: false, reasons: [] };

  const reasons = ["前序回踩后转强"];
  if (changePct >= 3.5) reasons.push(`当日涨幅 ${changePct.toFixed(2)}%`);
  if (breakPrevHigh) reasons.push("收盘突破前高");
  if (volumeExpand) reasons.push("量能放大");
  if (recoverBbi) reasons.push("重新站上 BBI");
  if (reclaimAverage) reasons.push("收回近三日均价");
  if (closeNearHigh) reasons.push("收盘接近当日高点");
  return { matched: true, reasons };
}

function weakToStrongReasonList(analysis, idx) {
  const bars = analysis?.klines || [];
  const bbiMap = buildBbiValueMap(analysis?.indicators?.bbi || []);
  return evaluateWeakToStrong(bars, bbiMap, idx).reasons;
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
      startAnalysisFlow();
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
    startAnalysisFlow();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".searchBox")) hideSuggestions();
  });

  els.mainMenu?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-page]");
    if (!button) return;
    switchMainPage(button.dataset.page);
  });

  els.pickerOverviewBtn?.addEventListener("click", () => startSmartPickerFlow(() => loadPickerOverview()));
  els.pickerWatchlistBtn?.addEventListener("click", () => startSmartPickerFlow(() => loadPickerWatchlist()));
  els.watchtowerRefreshBtn?.addEventListener("click", () => loadWatchtowerOverview(1));
  els.watchtowerSearchBtn?.addEventListener("click", () => loadWatchtowerOverview(1));
  els.watchtowerQueryInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      loadWatchtowerOverview(1);
    }
  });
  els.reviewRefreshBtn?.addEventListener("click", () => startReviewFlow(() => loadReviewOverview()));
  els.themeResearchStartBtn?.addEventListener("click", () => startThemeResearchFlow(() => startThemeResearchTask()));
  els.themeResearchInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      startThemeResearchFlow(() => startThemeResearchTask());
    }
  });
  els.themeBoardRefreshBtn?.addEventListener("click", () => startThemeBoardFlow(() => loadThemeBoardOverview()));
  els.systemConfigRefreshBtn?.addEventListener("click", () => startSystemConfigFlow(() => loadSystemConfigs({ keepEditing: true })));
  els.systemConfigCreateBtn?.addEventListener("click", () => {
    resetSystemConfigForm();
    openSystemConfigModal();
  });
  els.systemConfigForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    startSystemConfigFlow(() => submitSystemConfigForm());
  });
  els.systemConfigDeleteBtn?.addEventListener("click", () => startSystemConfigFlow(() => deleteCurrentSystemConfig()));
  els.systemConfigResetBtn?.addEventListener("click", resetSystemConfigForm);
  els.systemConfigTableBox?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-system-config-edit]");
    if (!button) return;
    startSystemConfigFlow(() => loadSystemConfigDetail(button.dataset.systemConfigEdit || ""));
  });
  els.pickerRunBtn?.addEventListener("click", () => startSmartPickerFlow(() => runSmartPicker("combined")));
  els.pickerEastmoneyBatchBtn?.addEventListener("click", openPickerEastmoneyModalWithLoading);
  els.pickerRunConditionBtn?.addEventListener("click", () => startSmartPickerFlow(() => runSmartPicker("condition")));
  els.pickerRunDcBtn?.addEventListener("click", () => startSmartPickerFlow(() => runSmartPicker("dc")));
  els.pickerRunTdxBtn?.addEventListener("click", () => startSmartPickerFlow(() => runSmartPicker("tdx")));
  els.pickerRunThsBtn?.addEventListener("click", () => startSmartPickerFlow(() => runSmartPicker("ths")));

  ["dc", "tdx", "ths"].forEach((source) => {
    const dom = pickerBoardDom(source);
    dom?.typeInput?.addEventListener("change", () => {
      state.smartPicker[dom.typeStateKey] = dom.typeInput?.value || "all";
      state.smartPicker[dom.stateKey] = null;
      state.smartPicker[dom.matchesKey] = [];
      renderPickerBoardOptions(source, []);
      renderPickerBoardSelection(source);
      if (dom.input?.value.trim()) {
        debouncePickerBoardSearch(source);
      }
    });
    dom?.input?.addEventListener("input", () => {
      const text = dom.input?.value.trim() || "";
      if (!text) {
        state.smartPicker[dom.stateKey] = null;
        state.smartPicker[dom.matchesKey] = [];
        renderPickerBoardOptions(source, []);
        renderPickerBoardSelection(source);
        return;
      }
      debouncePickerBoardSearch(source);
    });
    dom?.input?.addEventListener("change", () => {
      ensurePickerBoardSelection(source, dom.input?.value || "");
    });
    dom?.input?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        ensurePickerBoardSelection(source, dom.input?.value || "");
        runSmartPicker(source);
      }
    });
  });
  [els.pickerMarketScopeFilter, els.pickerStructureFilter, els.pickerEmotionFilter, els.pickerLeaderFilter, els.pickerOverallFilter, els.pickerSortBy, els.pickerSortDirection].forEach((input) => {
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
    if (els.pickerMarketScopeFilter) els.pickerMarketScopeFilter.value = "all";
    if (els.pickerStructureFilter) els.pickerStructureFilter.value = "all";
    if (els.pickerEmotionFilter) els.pickerEmotionFilter.value = "all";
    if (els.pickerLeaderFilter) els.pickerLeaderFilter.value = "all";
    if (els.pickerOverallFilter) els.pickerOverallFilter.value = "all";
    if (els.pickerSortBy) els.pickerSortBy.value = "overall_score";
    if (els.pickerSortDirection) els.pickerSortDirection.value = "desc";
    if (els.pickerTechnicalShape) els.pickerTechnicalShape.value = "all";
    if (els.pickerScreenMarket) els.pickerScreenMarket.value = "all";
    if (els.pickerTurnoverMin) els.pickerTurnoverMin.value = "";
    if (els.pickerTurnoverMax) els.pickerTurnoverMax.value = "";
    if (els.pickerMarketCapMin) els.pickerMarketCapMin.value = "";
    if (els.pickerMarketCapMax) els.pickerMarketCapMax.value = "";
    state.smartPicker.screenFilters = {};
    if (els.pickerQueryInput) els.pickerQueryInput.value = "";
    [
      { source: "dc", typeInput: els.pickerBoardType, input: els.pickerBoardInput },
      { source: "tdx", typeInput: els.pickerTdxType, input: els.pickerTdxInput },
      { source: "ths", typeInput: els.pickerThsType, input: els.pickerThsInput },
    ].forEach(({ source, typeInput, input }) => {
      const dom = pickerBoardDom(source);
      if (typeInput) typeInput.value = "all";
      if (input) input.value = "";
      state.smartPicker[dom.typeStateKey] = "all";
      state.smartPicker[dom.stateKey] = null;
      state.smartPicker[dom.matchesKey] = [];
      renderPickerBoardOptions(source, []);
    });
    renderAllBoardSelections();
    syncPickerFiltersFromControls();
    renderPickerTable();
  });
  els.pickerQueryInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      startSmartPickerFlow(() => runSmartPicker("condition"));
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

  document.querySelector("#reviewPage")?.addEventListener("click", (event) => {
    const pagerTrigger = event.target.closest("[data-review-page-action]");
    if (pagerTrigger) {
      const action = pagerTrigger.dataset.reviewPageAction || "";
      const page = pagerTrigger.dataset.reviewPage || "1";
      if (action === "hot-money-panel") {
        updateReviewHotMoneyPage(page);
      }
      return;
    }
    const summaryTrigger = event.target.closest("[data-review-summary-open]");
    if (summaryTrigger) {
      openReviewSummaryModal(summaryTrigger.dataset.reviewSummaryOpen || "");
      return;
    }
    const trigger = event.target.closest("[data-review-open-analysis]");
    if (!trigger) return;
    openReviewStockInAnalysis({
      ts_code: trigger.dataset.tsCode || "",
      query_name: trigger.dataset.name || "",
    });
  });

  document.querySelector("#watchtowerPage")?.addEventListener("click", (event) => {
    const pagerTrigger = event.target.closest("[data-watchtower-page]");
    if (pagerTrigger) {
      const page = pagerTrigger.dataset.watchtowerPage || "1";
      loadWatchtowerOverview(page);
      return;
    }
    const openTrigger = event.target.closest("[data-watchtower-open]");
    if (openTrigger) {
      openWatchtowerRealtimeModal(openTrigger.dataset.tsCode || "");
      return;
    }
    const analysisTrigger = event.target.closest("[data-watchtower-analysis]");
    if (analysisTrigger) {
      openCandidateInAnalysis({
        ts_code: analysisTrigger.dataset.tsCode || "",
        name: analysisTrigger.dataset.name || "",
        symbol: analysisTrigger.dataset.symbol || "",
      });
      return;
    }
    const eastmoneyTrigger = event.target.closest("[data-watchtower-eastmoney-add]");
    if (eastmoneyTrigger) {
      addWatchtowerStockToEastmoney(eastmoneyTrigger.dataset.tsCode || "");
      return;
    }
    const deleteTrigger = event.target.closest("[data-watchtower-delete]");
    if (deleteTrigger) {
      deleteWatchtowerStock(deleteTrigger.dataset.tsCode || "");
    }
  });

  document.querySelector("#themeBoardPage")?.addEventListener("click", (event) => {
    const themeTrigger = event.target.closest("[data-theme-board-open]");
    if (themeTrigger) {
      openThemeBoardModal(themeTrigger.dataset.tsCode || "", themeTrigger.dataset.name || "");
      return;
    }
    const stockTrigger = event.target.closest("[data-review-open-analysis]");
    if (stockTrigger) {
      openReviewStockInAnalysis({
        ts_code: stockTrigger.dataset.tsCode || "",
        query_name: stockTrigger.dataset.name || "",
      });
    }
  });

  document.querySelector("#themeResearchPage")?.addEventListener("click", (event) => {
    const pagerTrigger = event.target.closest("[data-review-page-action]");
    if (pagerTrigger && pagerTrigger.dataset.reviewPageAction === "theme-research-history") {
      const page = pagerTrigger.dataset.reviewPage || "1";
      void startThemeResearchFlow(() => loadThemeResearchHistory({ page, silent: true }));
      return;
    }
    const historyTrigger = event.target.closest("[data-theme-research-task]");
    if (!historyTrigger) return;
    const taskId = historyTrigger.dataset.themeResearchTask || "";
    const themeName = historyTrigger.dataset.themeResearchName || "";
    closeThemeResearchStream();
    state.themeResearch.loading = false;
    state.themeResearch.currentThemeName = themeName;
    if (els.themeResearchInput && themeName) {
      els.themeResearchInput.value = themeName;
    }
    void startThemeResearchFlow(() => loadThemeResearchReport(taskId, { keepEvents: false }));
  });

  els.reviewModal?.addEventListener("click", (event) => {
    if (event.target.closest("[data-review-modal-close]")) {
      closeReviewModal();
      return;
    }
    if (event.target.closest("[data-review-modal-reset-search='hot-money']")) {
      resetReviewInstitutionModalSearch();
      return;
    }
    const pagerTrigger = event.target.closest("[data-review-page-action]");
    if (pagerTrigger) {
      const action = pagerTrigger.dataset.reviewPageAction || "";
      const page = pagerTrigger.dataset.reviewPage || "1";
      if (action === "hot-money-modal") {
        updateReviewModalPage(page);
      }
      return;
    }
    const openTrigger = event.target.closest("[data-review-open-analysis]");
    if (openTrigger) {
      closeReviewModal();
      openReviewStockInAnalysis({
        ts_code: openTrigger.dataset.tsCode || "",
        query_name: openTrigger.dataset.name || "",
      });
    }
  });
  els.reviewModal?.addEventListener("submit", (event) => {
    const form = event.target.closest("[data-review-modal-search-form='hot-money']");
    if (!form) return;
    event.preventDefault();
    applyReviewInstitutionModalSearch();
  });
  els.watchtowerModal?.addEventListener("click", (event) => {
    if (event.target.closest("[data-watchtower-modal-close]")) {
      closeWatchtowerModal();
    }
  });
  els.themeBoardModal?.addEventListener("click", (event) => {
    if (event.target.closest("[data-theme-board-modal-close]")) {
      closeThemeBoardModal();
      return;
    }
    const openTrigger = event.target.closest("[data-review-open-analysis]");
    if (openTrigger) {
      closeThemeBoardModal();
      openReviewStockInAnalysis({
        ts_code: openTrigger.dataset.tsCode || "",
        query_name: openTrigger.dataset.name || "",
      });
    }
  });
  els.pickerEastmoneyModal?.addEventListener("click", (event) => {
    if (event.target.closest("[data-picker-eastmoney-close]")) {
      closePickerEastmoneyModal();
      return;
    }
    const deleteTrigger = event.target.closest("[data-picker-eastmoney-submit='delete']");
    if (deleteTrigger) {
      submitPickerEastmoneyBatch("delete");
    }
  });
  els.pickerEastmoneyForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitPickerEastmoneyBatch("add_group");
  });
  els.systemConfigModal?.addEventListener("click", (event) => {
    if (event.target.closest("[data-system-config-modal-close]")) {
      closeSystemConfigModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && els.systemConfigModal && !els.systemConfigModal.hidden) {
      closeSystemConfigModal();
      return;
    }
    if (event.key === "Escape" && els.pickerEastmoneyModal && !els.pickerEastmoneyModal.hidden) {
      closePickerEastmoneyModal();
      return;
    }
    if (event.key === "Escape" && els.reviewModal && !els.reviewModal.hidden) {
      closeReviewModal();
      return;
    }
    if (event.key === "Escape" && els.themeBoardModal && !els.themeBoardModal.hidden) {
      closeThemeBoardModal();
      return;
    }
    if (event.key === "Escape" && els.watchtowerModal && !els.watchtowerModal.hidden) {
      closeWatchtowerModal();
    }
  });

  els.levelTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-level]");
    if (!button) return;
    state.level = button.dataset.level;
    els.levelTabs.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item === button));
    if (state.analysis || state.selectedStock) loadAnalysis();
  });

  els.refreshBtn.addEventListener("click", () => startAnalysisFlow());
  els.analysisWatchlistBtn?.addEventListener("click", addCurrentAnalysisToWatchlist);

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

  els.reviewSideTabs?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-review-side-panel]");
    if (!button) return;
    const targetId = button.dataset.reviewSidePanel;
    els.reviewSideTabs.querySelectorAll("button[data-review-side-panel]").forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    document.querySelectorAll(".reviewSidePane").forEach((panel) => {
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
    } else if (region === "ma") {
      const pattern = klinePatternFromPointer(event, analysis);
      if (pattern) showKlinePatternTooltip(event, pattern);
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
