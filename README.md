# backtest_upstox — Python backtesting of intraday Nifty and BankNifty option strategies

> **Status: personal project, not maintained.** Built in 2024–2026 for the author's own trading research. The companion live-trading component stopped working after the broker changed its API security and new regulatory requirements took effect, and has been retired. The backtesting code is kept here as a record of the software work only. It is not investment advice and not production code; read the [Disclaimer](#disclaimer) before anything else.

The project tests rule-based intraday option-buying strategies on the Nifty 50 and Bank Nifty indices. It pulls historical candles and option-contract data from the [Upstox](https://upstox.com/developer/api-documentation/) broker API, turns each strategy's rules into entry and exit signals, simulates the resulting option trades minute by minute, and produces Excel and PDF reports on how each strategy would have performed. It runs as a container, with a GitHub Actions pipeline that lints, scans for secrets and vulnerabilities, and builds the image.

## How it works

```mermaid
flowchart LR
    A["Instrument master<br/>(current and expired<br/>option contracts, expiries)"] --> C
    B["Historical index candles<br/>1, 3, 5, 15, 30 min, daily"] --> C
    C["Signal creation<br/>indicators + entry rules<br/>per strategy"] --> D
    D["Trade simulation<br/>pick strike and expiry,<br/>replay option candles,<br/>apply exits"] --> E
    E["Reports<br/>Excel dashboards,<br/>PDF charts"] --> F
    F["PnL analysis<br/>stop and target thresholds,<br/>profit left on the table"]
```

1. **Instrument data.** Downloads the exchange instrument master and, for past periods, the expired option contracts and expiry dates for each index.
2. **Historical data.** Fetches index candles at several intervals and stores them as CSV files.
3. **Signals.** For each strategy, calculates indicators (EMA filters, ATR, an adaptive Gaussian moving average, ATR trailing stops) and marks the candles where its entry rules fire.
4. **Trades.** For each signal, selects the option strike (offset from the index price, adjusted near expiry) and the expiry, fetches that contract's minute candles, and replays the trade: lot sizing from the configured investment, exits by ATR stop, trailing stop, profit threshold or a fixed time, and slippage.
5. **Reports.** Produces per-signal, per-trade and aggregate results: realised PnL, win rate, maximum favourable and adverse excursion during each trade, with charts.
6. **Optimisation.** Studies the trade results to find better stop-loss and exit thresholds and how much profit time-based exits left behind.

## Performance design

Years of 1-minute history mean millions of candles per index, so a row-by-row backtest becomes very slow. The signal stage is therefore written as whole-column operations on pandas DataFrames and NumPy arrays rather than Python loops over rows:

- **Vectorised indicators.** EMA, ATR, RMA and the adaptive Gaussian moving average are computed over the entire history in one pass each, with `ewm`, `rolling`, `shift` and NumPy arithmetic.
- **Vectorised entry rules.** Entry conditions (breakouts of the opening range, EMA filters, time windows) are combined as boolean column expressions with `np.where`, so every candle is evaluated at once.
- **Array loops only where the maths requires them.** Indicators in which each value depends on the previous one (Supertrend, ATR trailing stop) cannot be expressed as a single column operation; they run as tight loops over plain NumPy arrays instead of over DataFrame rows.

Trade replay, which follows each signal through its option contract's minute candles, still steps through each trade; vectorising it is the next optimisation.

## Strategies as configuration

Each strategy is a JSON file in `datafiles/Strategies/` (for example `NIFTY_S01.dat`), so a new variant needs no code change. A file sets the index, direction, candle interval, entry window and cut-off, strike offset and adjustment rules, indicator lengths and multipliers, exit and trailing-stop parameters, investment per trade and daily loss limit.

## Project layout

| Path | Contents |
|---|---|
| `upstox_core/data_creators/` | Upstox API wrappers for instruments, expiries and history; signal and trade data creation |
| `upstox_core/data_consumers/` | Market-data and portfolio streaming over WebSocket (protobuf feed), and order calls used by the retired live component |
| `backtest_common/` | Strategy base class and configuration loader, technical-indicator library, report generator, path settings |
| `test_client/` | Entry points: the backtest run and the PnL optimiser |
| `datafiles/Strategies/` | Strategy configuration files |
| `Dockerfile`, `docker-compose.yml` | Multi-stage image (build wheels, then a slim non-root runtime) and a local run definition |
| `.github/workflows/ci.yml` | Pipeline: flake8 lint, TruffleHog secret scan, image build, Trivy vulnerability scan |
| `terraform/` | Amazon ECR repository for the image |

## Technology

Python 3.14, pandas, NumPy, pandas-ta, Upstox Python SDK, WebSocket client with protobuf decoding, Matplotlib, XlsxWriter and openpyxl for Excel dashboards, ReportLab for PDF reports, PyYAML. Docker and Docker Compose, GitHub Actions, TruffleHog, Trivy, Terraform on AWS.

## Running it

An Upstox developer account and an access token are needed. The token is read from the environment variable `UPSTOX_ACCESS_TOKEN` and is never committed: copy `.env.sample` to `.env` (ignored by Git) and put the token there.

```powershell
Copy-Item .env.sample .env
# edit .env and set UPSTOX_ACCESS_TOKEN

docker compose up --build
```

Data, reports and logs are written to the local `datafiles/`, `logs/` and `misc/` folders, which are mounted into the container.

## Known limitations

- No automated tests.
- Settings and file paths live in Python modules rather than a settings file.
- Several experimental variants of the signal and trade classes remain alongside the main ones.
- Backtests ignore brokerage, taxes and liquidity beyond a simple slippage estimate, so live results would differ.

## Disclaimer

- This repository is published only as an example of software engineering work. It is not investment advice, a recommendation to buy or sell any security or derivative, or an offer of any service.
- The strategy files show the configuration format. No claim is made that any strategy is, or was, profitable. Backtested results are hypothetical: they are produced by simulation on past data, do not represent actual trading, and are no indication of future results.
- Trading in derivatives carries a substantial risk of loss.
- The code, configuration and any output are provided "as is", without warranty of any kind, express or implied, including fitness for any purpose and correctness of results. The author accepts no liability for any loss or damage, direct or indirect, arising from their use.
- Anyone who uses any part of this repository does so entirely at their own risk and is solely responsible for complying with the laws, exchange rules and broker terms that apply to them.

## Licence

No licence is granted. All rights are reserved by the author. The code is published for viewing only; no permission is given to copy, modify, distribute or use it, for trading or otherwise.
