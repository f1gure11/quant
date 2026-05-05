# Quant ETF Data Project

本项目只用于中国市场 ETF 数据采集、清洗、本地缓存和质量检查，供学习、研究和后续回测验证使用。不构成投资建议，不连接券商接口，不生成买卖信号，不承诺收益。

## 数据源与合规边界

优先使用 BaoStock，其次使用 AKShare 公开接口；下载过程低频串行执行，并将结果保存到本地 CSV 缓存。项目不绕过验证码、登录限制、签名参数、App 私有接口或付费/Level-2 数据限制，也不将数据二次分发为商业接口。

## 安装依赖

```powershell
cd "D:\AI REASONER\codex_quant_pack\quant_etf_project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 下载 ETF 数据

默认使用 BaoStock、日线、最近 5 年：

```powershell
python scripts/download_etf_data.py
```

指定数据源和日期区间：

```powershell
python scripts/download_etf_data.py --source baostock --start 2019-01-01 --end 2024-12-31
python scripts/download_etf_data.py --source akshare --start 2019-01-01 --end 2024-12-31
```

强制重下本地已有数据：

```powershell
python scripts/download_etf_data.py --force-update
```

## ETF 标的池

自动模式会优先尝试从数据源获取 ETF 列表，并保存到：

```text
data/processed/etf_universe.csv
```

可以在 `src/config.py` 中切换标的池模式：

```python
UNIVERSE_MODE = "auto"    # 自动获取 ETF 列表
UNIVERSE_MODE = "manual"  # 只使用手工配置列表
```

如果设置为手动模式，或自动获取失败，会使用 `src/config.py` 中的 `MANUAL_ETF_CODES`：

```python
MANUAL_ETF_CODES = ["510300", "510500", "159915", "588000", "512100"]
```

## 数据文件

单只 ETF 原始/标准化缓存：

```text
data/raw/baostock/{code}.csv
data/raw/akshare/{code}.csv
```

合并后的处理数据：

```text
data/processed/etf_daily_baostock.csv
data/processed/etf_daily_akshare.csv
```

标准字段：

```text
date, code, name, open, high, low, close, volume, amount, pct_chg, source
```

## 数据质量报告

下载完成后会自动生成：

```text
reports/etf_data_quality_report.md
```

也可以单独运行：

```powershell
python scripts/validate_etf_data.py --source baostock
python scripts/validate_etf_data.py --source akshare
```

报告包含重复交易日、OHLC 缺失、`high < low`、`close <= 0`、负成交量、每只 ETF 起止日期和数据条数等检查。

## 日志

下载日志保存到：

```text
logs/data_download.log
```

日志记录下载开始时间、数据源、成功数量、失败代码、失败原因和保存路径。

## 数据源限制

- BaoStock 的 ETF 列表完整性和 ETF 复权字段支持可能有限，代码中会用 AKShare 或手工配置兜底。
- AKShare 接口字段可能随公开网站页面调整而变化，需要保留本地缓存并低频使用。
- 本模块不随意填补价格缺失；发现缺失会写入质量报告，由研究者按明确规则处理。
- 本模块只处理历史日线研究数据，不做实时行情、高频抓取、会员数据或自动交易。

## 后续阶段

完成数据采集和质量检查后，可在新的模块中进入因子计算、策略生成和回测阶段。进入下一阶段前，应先确认质量报告中的问题已被解释或按规则处理，并继续遵守信号日期与执行日期分离、无未来函数、交易成本和滑点等约束。
