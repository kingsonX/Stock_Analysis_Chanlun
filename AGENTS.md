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

## 运行与验证

本机 Homebrew Python 是 externally managed，优先使用项目内虚拟环境：

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

环境变量：

- `TUSHARE_TOKEN` 必须通过环境变量或本地 `.env` 提供。
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
- `chanlun_app/__init__.py`：Flask app factory，定义 `/`、`/api/stocks/search`、`/api/analysis`。静态资源用文件 mtime 加版本参数，避免浏览器缓存旧 JS/CSS。
- `chanlun_app/config.py`：项目路径、缓存路径、周期配置和日期规范化。
- `chanlun_app/data_provider.py`：Tushare 数据层，负责 token 读取、股票列表缓存、股票搜索、K 线获取和错误封装。
- `chanlun_app/chanlun.py`：缠论核心算法和指标计算。
- `chanlun_app/templates/index.html`：单页工作台结构。
- `chanlun_app/static/app.js`：前端状态管理、API 调用、Canvas 绘图、拖动缩放、tooltip。
- `chanlun_app/static/styles.css`：布局和视觉样式。
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
- MACD 附图显示红绿柱、DIF、DEA，并标注 `趋势背驰/盘整背驰/线段背驰`。
- tooltip 在普通 K 线悬停时显示 OHLC、成交量、BBI、MACD/DIF/DEA；悬停买卖点标记时显示该信号摘要；悬停 MACD 背驰标记时显示背驰理由和证据。

修改前端后至少运行：

```bash
node --check chanlun_app/static/app.js
```

如果改了 API 返回字段，也同步更新 `tests/test_api.py`。

## 开发注意事项

- 不要把 Tushare token 写进代码、README、AGENTS 或测试。
- 不要依赖真实 Tushare 做单元测试；API 测试使用 fake client。
- 真实接口测试可以用 `curl http://127.0.0.1:5000/...`，但不要把敏感配置输出到文档。
- 改后端 Python 代码后需要重启正在运行的 Flask 进程；当前默认 `FLASK_DEBUG=0`，没有自动 reload。
- 页面如果看不到最新 JS/CSS，确认访问的是 `http://127.0.0.1:5000`，并检查首页资源是否带 `?v=` 参数。
- 新增指标时保持 `indicators.<name>` 与 `klines` 长度对齐，缺值用 `null`。
- 新增缠论结构时尽量保持 dataclass -> `asdict` 的返回方式，便于 API 和前端一致消费。
