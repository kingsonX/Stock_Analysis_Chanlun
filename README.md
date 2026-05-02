# 缠论分析网站

一个基于 Flask + 原生前端的 A 股缠论分析网站。输入股票名称或代码后，通过 Tushare 获取日线、周线、月线 K 线，并生成分型、笔、中枢、背驰和买卖点候选。

## 启动

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
export TUSHARE_TOKEN="你的 Tushare Pro Token"
.venv/bin/python run.py
```

打开浏览器访问 `http://127.0.0.1:5000`。

也可以复制 `.env.example` 为 `.env`，把 `TUSHARE_TOKEN` 填进去后再启动；`.env` 已被 Git 忽略。

## 功能

- 股票搜索：支持股票名称、代码、拼音缩写、`ts_code`。
- 周期切换：日线、周线、月线。
- 缠论结构：包含处理、顶/底分型、笔、中枢、背驰。
- 买卖点：输出一/二/三类买卖点候选和触发说明。
- 图表：Canvas 交互 K 线图，叠加分型、笔、中枢和买卖点。

## 说明

- 第一版只支持 A 股个股，不支持指数、港股、美股、分钟线和复权行情。
- Token 从 `TUSHARE_TOKEN` 环境变量读取，不会写入代码。
- 缠论规则存在社区口径差异，本项目把主要规则集中在 `chanlun_app/chanlun.py`，后续可继续细化。
