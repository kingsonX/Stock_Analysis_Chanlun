# 缠论分析网站

一个基于 Flask + 原生前端的 A 股缠论分析网站。输入股票名称或代码后，通过 Tushare 获取 30/60 分钟、日线、周线、月线 K 线，并生成分型、笔、线段、中枢、背驰和买卖点候选。

## 启动

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
export TUSHARE_TOKEN="你的 Tushare Pro Token"
export MX_APIKEY="你的东方财富妙想 API Key"
export CLAUDE_BASE_URL="https://code.newcli.com/claude"
export CLAUDE_API_KEY="你的 Claude API Key"
.venv/bin/python run.py
```

如果你希望在智能选股候选详情里生成 `Claude` 研究解读，还可以额外配置：

```bash
export CLAUDE_MODEL="Claude Sonnet 4.6"
```

打开浏览器访问 `http://127.0.0.1:5000`。

也可以复制 `.env.example` 为 `.env`，把 `TUSHARE_TOKEN` 和可选的 `MX_APIKEY` 填进去后再启动；`.env` 已被 Git 忽略。

## 功能

- 股票搜索：支持股票名称、代码、拼音缩写、`ts_code`。
- 周期切换：30分钟、60分钟、日线、周线、月线。
- 缠论结构：包含处理、顶/底分型、笔、中枢、背驰。
- 多级别联动：分钟线自动参考日/周/月结构，日线自动参考周/月结构，周线自动参考月线结构。
- 走势类型：输出线段、当前走势类型、中枢位次和中枢生命周期。
- 买卖点：输出一/二/三类买卖点候选、确认/失效状态、失效价和触发说明。
- 背驰证据：展示比较笔、价格力度、MACD 红绿柱面积、DIF/DEA、零轴位置和力度阈值。
- 复盘与纪律：统计信号后固定窗口内的顺向/逆向空间，并生成失效价风险卡。
- 妙想数据：通过后端读取 `MX_APIKEY`，在右侧数据页展示行情、资金、估值、财务摘要和公司资料，不向浏览器暴露密钥。
- 综合交易画像：把缠论结构、妙想行情卡、资讯催化、市场扫描合成一张结论卡，输出“结构/情绪/容量/风险”四个维度的综合判断。
- 智能选股：按全 A 股范围执行条件筛选，支持候选池排序、三视角筛选、自选联动和候选详情展开。
- AI 研究解读：在智能选股候选详情里，调用 Claude 兼容接口把缠论、养家、章盟主三视角改写成更接近研究员的解释。
- 图表：Canvas 交互 K 线图，叠加分型、笔、线段、中枢、买卖点、BBI 和 MACD；支持拖动、缩放、图层开关和历史回放。

## 说明

- 当前只支持 A 股个股，不支持指数、港股、美股和自动交易。
- 分钟线接口可能需要单独 Tushare 权限，权限不足时页面会返回清晰错误。
- 复权功能已从第一版界面和后端移除，所有 K 线按当前 Tushare 基础行情接口返回。
- Token 从 `TUSHARE_TOKEN` 环境变量读取，不会写入代码。
- 妙想数据从 `MX_APIKEY` 环境变量读取；缺少或调用失败时只影响右侧数据页，不影响缠论主功能。
- `Claude` 研究解读从 `CLAUDE_API_KEY` 环境变量读取；建议同时配置 `CLAUDE_BASE_URL` 和 `CLAUDE_MODEL`；缺少时不影响候选池和缠论结构，只会让 AI 解读按钮无法生成内容。
- 缠论规则存在社区口径差异，本项目把主要规则集中在 `chanlun_app/chanlun.py`，后续可继续细化。
