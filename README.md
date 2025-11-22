# BTC AI Market Assistant

A lightweight command-line helper that fetches live Bitcoin market data and produces a concise trading recommendation.

## Features
- Pulls real-time Bitcoin metrics (price, 24h high/low, market cap, volume) from CoinGecko.
- Summarizes short, daily, and weekly price momentum.
- Generates a simple action suggestion (buy/hold/reduce exposure) with rationale.

## Quickstart
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the assistant:
   ```bash
   python -m btc_ai_api.cli
   ```
3. Disable ANSI colors if your terminal does not support them:
   ```bash
   python -m btc_ai_api.cli --no-color
   ```

## 即开即用的网页版本
无需安装额外依赖，直接打开 `web/index.html` 即可查看实时行情和操作建议。

如果想在本机开启简易预览，可在仓库根目录运行：

```bash
python -m http.server 8080
```

然后在浏览器访问 `http://localhost:8080/web/`。

## Testing
Run the unit tests to verify the analysis logic:
```bash
pytest
```
