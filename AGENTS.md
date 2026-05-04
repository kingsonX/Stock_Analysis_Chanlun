# AGENTS.md

本文件是给后续开发者和智能体使用的项目工作指南。根目录下的所有代码都按这里的约定维护。

## 项目概览

这是一个 Flask + 原生 HTML/CSS/JS 的 A 股缠论分析网站。用户在页面输入股票名称、代码或拼音缩写，后端通过 Tushare 获取 K 线，计算缠论结构和指标，前端用 Canvas 画交互式行情图。

核心能力：

- 支持 A 股个股 `min30`、`min60`、`daily`、`weekly`、`monthly` 五个级别。
- Tushare 接口使用 `stock_basic`、`daily`、`weekly`、`monthly`、`stk_mins`。
- 主图绘制 K 线、分型、笔、中枢、买卖点、BBI。
- 附图绘制 MACD，并标注趋势背驰、盘整背驰、线段内背驰。
- 图表支持横向拖动、鼠标滚轮缩放、历史回放、图层开关、悬浮查看 K 线和指标。
- API 返回多级别联动摘要、线段、走势类型、中枢生命周期、买卖点状态和背驰证据。
- API 返回信号复盘统计和失效价风险卡，用于训练和复盘，不用于自动交易。
- 可选接入东方财富妙想 `mx-data`，在后端汇总行情、资金、估值、财务和公司资料，作为缠论之外的辅助信息。
- 已接入基于 `mx-data`、`mx-search`、`mx-xuangu` 的综合交易画像，把缠论结构、养家情绪、章盟主容量和风险边界合成一张结论卡。
- 已接入智能选股模块：按全 A 股范围执行条件筛选，生成候选池，支持候选详情、自选联动和右侧情报侧栏。
- 已接入 Claude 兼容 AI 解释层，用于把三视角规则摘要改写成更像研究员写给交易员的结论。
- 当前综合交易画像仍是“规则引擎 + 外部数据 + 模板化解释”，不是完整自主 AI 投顾，不可视为直接交易指令。

## 运行与验证

本机 Homebrew Python 是 externally managed，优先使用项目内虚拟环境：

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

若 `5000` 端口已占用，可临时改用：

```bash
PORT=5001 .venv/bin/python run.py
```

环境变量：

- `TUSHARE_TOKEN` 必须通过环境变量或本地 `.env` 提供。
- `MX_APIKEY` 可选；配置后右侧“数据”页会加载妙想金融数据增强卡片。
- `CLAUDE_BASE_URL`、`CLAUDE_API_KEY`、`CLAUDE_MODEL` 用于智能选股候选详情中的 AI 研究解读。
- `.env` 已在 `.gitignore` 中，绝不要提交真实 token。
- `.env.example` 只保留占位符。
- `PORT` 默认 `5000`，`FLASK_DEBUG=1` 才开启 debug。

验证命令：

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check chanlun_app/static/app.js
.venv/bin/python -m compileall chanlun_app tests
```

访问页面必须用 Flask 服务地址：

```text
http://127.0.0.1:5000
```

不要直接打开 `file:///.../templates/index.html`，那样不会经过 Flask 模板、静态版本参数和 API。

## 代码结构

- `run.py` / `chanlun_app/__main__.py`：启动 Flask 应用，读取 `PORT` 和 `FLASK_DEBUG`。
- `chanlun_app/__init__.py`：Flask app factory，定义 `/`、`/api/stocks/search`、`/api/analysis`、`/api/mx/summary`。静态资源用文件 mtime 加版本参数，避免浏览器缓存旧 JS/CSS。
- `chanlun_app/config.py`：项目路径、缓存路径、周期配置和日期规范化。
- `chanlun_app/data_provider.py`：Tushare 数据层，负责 token 读取、股票列表缓存、股票搜索、K 线获取和错误封装。
- `chanlun_app/mx_provider.py`：东方财富妙想数据层，负责读取 `MX_APIKEY`、请求 `mx-data` 接口、宽容解析表格并隐藏密钥。
- `chanlun_app/trading_profile.py`：综合交易画像服务，负责调用 `mx-data`、`mx-search`、`mx-xuangu`，并把缠论结构、情绪、容量和风险合成为统一结论卡。
- `chanlun_app/smart_picker.py`：智能选股服务，负责市场环境、条件筛选、候选池、自选联动和候选详情。
- `chanlun_app/ai_profile.py`：Claude 兼容 AI 解释层，负责消费事实层摘要并生成三视角研究解读。
- `chanlun_app/chanlun.py`：缠论核心算法和指标计算。
- `chanlun_app/templates/index.html`：单页工作台结构。
- `chanlun_app/static/app.js`：前端状态管理、API 调用、Canvas 绘图、拖动缩放、tooltip。
- `chanlun_app/static/styles.css`：布局和视觉样式。
- `render.yaml`：Render 蓝图配置，当前生产入口使用 `gunicorn run:app --bind 0.0.0.0:$PORT`。
- `tests/`：标准库 `unittest` 测试；API 测试使用 fake client，不依赖真实 Tushare。

忽略目录：

- `.venv/`、`.env`、`cache/`、`__pycache__/` 都不应提交。
- `cache/stocks.csv` 是 Tushare 股票列表本地缓存，TTL 当前为 24 小时。

## API 约定

`GET /api/stocks/search?q=&limit=`

- 按 `symbol`、`ts_code`、`name`、`cnspell` 做精确和模糊匹配。
- 返回 `items`，每项包含 `ts_code/symbol/name/area/industry/market/exchange/list_date/cnspell`。

`GET /api/analysis?ts_code=&level=min30|min60|daily|weekly|monthly&start_date=&end_date=`

- `ts_code` 参数也可传股票名称或代码，后端会解析为 Tushare `ts_code`。
- 日期可传 `YYYY-MM-DD` 或 `YYYYMMDD`。
- 返回主要字段：
  - `stock`：股票信息。
  - `query`：实际查询周期和日期。
  - `klines`：升序 K 线，字段为 `index/date/open/high/low/close/vol/amount`；分钟线 `date` 为 `YYYYMMDDHHMM`。
  - `indicators.macd`：`index/date/dif/dea/hist`。
  - `indicators.bbi`：`index/date/value`；前 23 根因 MA24 不足为 `null`。
  - `merged_klines/fractals/strokes/centers/divergences/signals`：缠论结构。
  - `segments`：由笔组合出的线段第一版近似结构。
  - `trend`：当前级别走势类型、方向、最后中枢位次和说明。
  - `level_context`：当前级别与上级别的结构摘要；分钟线包含月线/周线/日线，日线包含月线/周线，周线包含月线。
  - `backtest`：买卖点出现后固定窗口的顺向/逆向空间复盘统计。
  - `risk_cards`：最近买卖点的失效价、风险比例和纪律说明。

`GET /api/mx/summary?ts_code=&name=`

- 后端使用 `MX_APIKEY` 调用东方财富妙想金融数据，不把密钥返回给浏览器。
- 返回 `cards`，固定包含行情、资金、估值、财务、公司五类卡片。
- 单个卡片失败时只标记该卡片 `status=error`，不影响其它卡片，也不影响主图缠论分析。

`POST /api/trading-profile`

- 请求体包含 `stock` 与当前 `/api/analysis` 返回的 `analysis`，服务端不重复请求 Tushare。
- 返回 `profile`：综合交易画像结论卡，含 `结构/情绪与主流/容量与资金/风险边界` 四个维度。
- `profile` 顶层包含 `stance/stance_label/headline/decision/conclusion/tags`。
- `profile.structure`、`profile.emotion`、`profile.capacity`、`profile.risk` 每块都返回：
  - `summary`：该维度摘要。
  - `verdict`：一句话结论，例如 `候选观察`、`可以看，但别追高`、`容量够看，别冲动重仓`。
  - `action`：明确写出“是否值得买”的当前判断。
  - `detail`：理由说明。
  - `basis`：判断依据列表。
  - `conditions`：后续升级/降级观察条件。
  - `tone`：`positive/neutral/caution`，供前端样式使用。
- 同时返回 `mx_summary`、`news`、`market_scan` 作为证据层数据；任一外部源失败时允许部分降级。
- 当前 `POST /api/trading-profile` 是规则化画像接口，不是大模型推理接口；它依赖前端先调用 `/api/analysis` 再把结构结果传入。

`GET /api/smart-picker/overview`

- 返回智能选股首页所需的市场环境、主流扫描、资讯催化与全 A 股范围摘要。
- `universe.total` 代表当前本地股票库可扫描的 A 股总数。

`POST /api/smart-picker/screen`

- 请求体包含 `query_text`、`level`、`limit`。
- 条件筛选默认在全 A 股范围执行，但深度结构扫描只对命中的前 `limit` 只股票执行，这是为速度和稳定性做的工程折中。
- 返回 `candidates`，每项包含 `stock/quote/structure/emotion/capacity/overall` 六类信息，可供前端排序和筛选。

`POST /api/smart-picker/candidate`

- 请求体包含 `stock` 与 `level`。
- 返回单只候选股的 `/api/analysis` 结构结果、综合交易画像和自选状态。

`GET/POST /api/smart-picker/watchlist`

- `GET` 用于读取东方财富自选概览。
- `POST` 用于执行加入/移出自选操作。

`POST /api/smart-picker/ai-brief`

- 请求体包含 `stock`、`analysis`、`profile`。
- 该接口只消费事实层和规则层结果，不自行请求 Tushare 主图结构。
- 返回 `analysis.summary/overall_verdict/buy_judgement/confidence/chan_view/yangjia_view/zhang_view/risks/watch_points`。
- 当前协议已切到 Claude 兼容接口，不再使用 OpenAI Responses API。

错误统一返回：

```json
{"error": {"message": "...", "status_code": 400}}
```

## 缠论与指标口径

当前实现是“可解释的内置严谨口径”，仍保留进一步精修空间。

缠论流程：

1. 原始 K 线转 `RawBar`。
2. 包含关系处理生成 `MergedBar`。
3. 识别顶/底分型，并压缩连续同类分型，只保留更极端者。
4. 成笔规则：顶底分型交替，且跨度至少 `MIN_RAW_BARS_PER_STROKE = 5` 根原始 K 线。
5. 中枢：连续三笔价格区间存在重叠时生成，记录上下沿、起止笔和方向。
6. 线段：第一版按三笔一组、前后衔接生成，用于显示更高一层推进结构；不是完整特征序列线段。
7. 中枢生命周期：按后续笔是否延伸、离开、回抽回中枢，标记 `新生/延伸中/离开中/离开确认/扩张或升级观察`。
8. 背驰：
   - 趋势背驰：两个以上同向中枢后，最后中枢离开段与进入段同向比较，价格继续创新高/新低但综合力度低于前段 `88%`。
   - 盘整背驰：盘整/单中枢中，离开段与进入段同向比较，价格继续创新高/新低但力度减弱。
   - 线段内背驰：同方向后一笔与前一同向笔比较，价格创新高/新低但力度减弱。
9. 买卖点：
   - 一类买卖点来自背驰候选。
   - 二类买卖点来自一类点后的回踩/反弹确认。
   - 三类买卖点来自离开中枢后的回踩/反抽不回中枢。
   - 每个信号都有 `candidate/confirmed/invalid` 状态、失效价和观察说明。

力度计算：

- 每笔 `price_strength = abs(price_change) / start_price`。
- 每笔 `momentum_strength = 当前笔区间内 MACD hist 绝对值求和`。
- 综合力度为 `price_strength + momentum_strength * 0.01`。
- 背驰证据同时拆分 `MACD` 红柱面积、绿柱面积、`DIF`、`DEA`、柱端值和零轴位置，前端逐项展示。

指标：

- MACD 使用 EMA12、EMA26、DEA9，`hist = (DIF - DEA) * 2`。
- BBI 使用 `(MA3 + MA6 + MA12 + MA24) / 4`。

## 综合交易画像口径

综合交易画像不是单纯拼文案，而是四层规则判断：

1. `structure`：读取 `trend`、`signals`、`divergences`、`risk_cards`，回答缠论维度“是否值得买”。
2. `emotion`：读取市场热度、活跃成交、行业活跃扫描和资讯催化，回答养家维度“是否值得买”。
3. `capacity`：读取成交额、换手率、总市值、主力净额，回答章盟主维度“是否值得买”。
4. `risk`：扫描减持/问询/处罚/监管/解禁等风险词，并叠加失效价与信号状态，给出风险边界。

重要约束：

- 顶部总卡必须服从“风险优先”原则，不能出现分块写“先控风险”，总卡却写“结构与环境共振”的自相矛盾。
- 当最后买点仅为 `candidate` 时，总卡应优先落在 `候选观察/先观察`，不能直接升级成强确认。
- 资讯催化要区分 `板块级/政策级催化`、`公司经营催化`、`一般资讯催化`，不能把所有公告都当成主线级利好。
- 当前三视角结论是规则解释，不是席位级、盘口级、真人交易员级复现。

可靠性边界：

- 当前系统适合做“结构定位、环境观察、风险边界提醒”，不适合直接替代下单判断。
- 缠论、养家、章盟主三视角目前都建立在可解释规则和外部数据之上，尚未引入真正的大模型语义推理。
- 结论更接近“研究助理给出的观察结论”，不是“AI 投顾最终意见”。

后续如果引入 AI，推荐采用两层结构：

1. **事实层 / 规则层**：继续保留当前 `chanlun.py`、`mx_provider.py`、`trading_profile.py` 负责抽取可验证事实。
2. **LLM 解释层**：新增独立接口，例如 `/api/ai-profile`，只消费结构化摘要，再输出三视角解释、置信度、关键依据和否定条件。

不要让 LLM 直接替代规则层；正确方向是“规则给事实，LLM 做解释、比较和归纳”。

当前 AI 接入约束：

- 智能选股详情页的“AI 研究解读”已默认走 `Claude` 兼容消息接口，变量名为 `CLAUDE_BASE_URL`、`CLAUDE_API_KEY`、`CLAUDE_MODEL`、可选 `CLAUDE_API_VERSION`。
- 兼容层当前按 `POST /v1/messages`、`x-api-key`、`anthropic-version` 口径发起请求，并要求模型直接返回合法 JSON。
- 如果上游返回“第三方客户端禁止调用”“官方 Max 渠道禁止第三方接入”之类错误，应视为通道限制，而不是本地代码问题。
- 出现此类限制时，不要继续硬编码绕过；应改用允许第三方调用的 Claude 网关，或切回官方 Anthropic API。

## 前端绘图约定

前端无 Node 构建链，所有交互在 `chanlun_app/static/app.js` 中。

图表约定：

- Canvas 分为主图和 MACD 附图。
- 主图默认显示最近一段 K 线，不把全量数据压缩到一屏。
- 拖动 Canvas 横向浏览历史，滚轮缩放可见 K 线数量。
- 回放模式下，图表和右侧中枢/背驰/风险列表只显示回放游标之前已经出现的结构。
- 中国市场颜色：上涨 K 线和上涨笔为红色，下跌 K 线和下跌笔为绿色。
- 主图叠加 BBI 紫色线、分型三角、笔、中枢矩形、`买1/买2/买3/卖1/卖2/卖3`。
- 线段用更粗的虚线叠加在笔之上，帮助区分笔级噪音和更大一级推进。
- 侧栏显示级别联动、走势类型、中枢生命周期和风险纪律；不常驻展示信号摘要或背驰候选。
- 侧栏显示风险纪律卡和信号复盘统计；这些是后验训练辅助，不是交易指令。
- 侧栏“数据”页异步显示 `mx-data` 增强信息；加载失败时只显示卡片错误，不阻塞主图。
- 侧栏“数据”页顶部优先显示综合交易画像卡，再显示市场扫描、资讯催化和原始妙想表格卡片。
- 侧栏“数据”页中的综合交易画像卡要优先强调 `decision`、各分块 `verdict`、`basis`、`conditions`，避免只展示一句空泛立场。
- 三视角标题统一使用 `缠论结构`、`养家视角`、`章盟主视角`、`风控边界`，不要再混用旧的“情绪与主流 / 容量与资金 / 风险边界”口号式标题。
- MACD 附图显示红绿柱、DIF、DEA，并标注 `趋势背驰/盘整背驰/线段背驰`。
- tooltip 在普通 K 线悬停时显示 OHLC、成交量、BBI、MACD/DIF/DEA；悬停买卖点标记时显示该信号摘要；悬停 MACD 背驰标记时显示背驰理由和证据。
- 智能选股页采用后台工作台布局：左侧为主菜单；内容区顶部先显示选股条件，候选池紧跟查询区下方；右侧先显示候选详情，再通过 `市场/催化/自选` tab 切换情报面板。
- 智能选股页不要再把 `市场环境`、`资讯催化`、`我的自选` 平铺在主内容区中间；它们已经迁移到右侧侧栏，避免候选池被挤到页面下方。

修改前端后至少运行：

```bash
node --check chanlun_app/static/app.js
```

如果改了 API 返回字段，也同步更新 `tests/test_api.py`。

## 开发注意事项

- 不要把 Tushare token 写进代码、README、AGENTS 或测试。
- 不要把 `MX_APIKEY` 写进代码、README、AGENTS 或测试；只写 `.env` 或部署平台环境变量。
- 不要把 `CLAUDE_API_KEY` 写进代码、README、AGENTS 或测试；只写 `.env` 或部署平台环境变量。
- 当前 Render 生产配置依赖 `render.yaml`，并要求部署环境至少配置 `TUSHARE_TOKEN`、可选配置 `MX_APIKEY`。
- 当前 Render 生产配置还支持 `CLAUDE_BASE_URL`、`CLAUDE_API_KEY`、`CLAUDE_MODEL`、`CLAUDE_API_VERSION`；若切换 AI 通道后未生效，需重新部署。
- `render.yaml` 当前固定使用 `PYTHON_VERSION=3.11.11`；不要随手切回过新的 Python 版本，否则 `tushare/pandas/matplotlib` 兼容性风险会升高。
- Render 修改环境变量后，如未自动触发新进程加载，应手动重新部署一次。
- 不要依赖真实 Tushare 做单元测试；API 测试使用 fake client。
- 不要依赖真实 `mx-data` 做单元测试；用 fake provider 或解析样例测试。
- 不要依赖真实 `mx-search`、`mx-xuangu` 做单元测试；综合交易画像测试应优先用 fake provider 覆盖结论口径。
- 真实接口测试可以用 `curl http://127.0.0.1:5000/...`，但不要把敏感配置输出到文档。
- 改后端 Python 代码后需要重启正在运行的 Flask 进程；当前默认 `FLASK_DEBUG=0`，没有自动 reload。
- 页面如果看不到最新 JS/CSS，确认访问的是 `http://127.0.0.1:5000`，并检查首页资源是否带 `?v=` 参数。
- 新增指标时保持 `indicators.<name>` 与 `klines` 长度对齐，缺值用 `null`。
- 新增缠论结构时尽量保持 dataclass -> `asdict` 的返回方式，便于 API 和前端一致消费。
