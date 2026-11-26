# Trading System

ICT-SMC PO3-AMD intraday futures trading system — ES/NQ on 1m execution, Silver Bullet V1.
A+ setups only. 6-gate decision framework. Designed around prop-firm style evaluation risk limits.

**Primary decision doc:** `04_Current_System_and_Indicators/Current_System_Map.md`

## Disclaimer

Research and backtesting only. Not financial advice. No order execution included.

See `LICENSE` (MIT), `THIRD_PARTY_NOTICES.md` and `SECURITY.md`.

## System Summary

| Attribute | Value |
|-----------|-------|
| Markets | ES, NQ (1m execution) |
| Session | London or New York only |
| Framework | ICT-SMC PO3-AMD — 6-gate A+ checklist |
| Entry window | New York Silver Bullet: 10:00–11:00 ET |
| Signals required | 3 required: stop hunt + iFVG/FVG + CHoCH/MSS. SMT divergence = booster (★★★ when present) |
| Risk:Reward | ≥ 1:2 (min). Backtest to validate optimal threshold. |
| Risk per trade | 0.5–1.5% equity (★★★ = 1.5%, ★★ = 0.5–1%) |
| Stop | Extreme of sweep candle wick ± 1 tick (ES) / 3 ticks (NQ) |

## Platform Stack

| Layer | Tool |
|-------|------|
| Charting + signals | TradingView (Pine Script v6) |
| Backtesting + validation | Python (pandas, numpy, hmmlearn) |
| Market data | Alpaca (historical bars), Pyth, OpenBB, UnusualWhales |

## Repository Structure

```
08_TradingView_Indicators/
  mmt/
    CVD_Divergence.pine      # Cumulative Volume Delta divergence + alerts
    OI_Analysis.pine         # Open Interest regime classification
execution/
  backtester.py              # OHLCV backtesting engine (slippage, commission, metrics)
  risk_manager.py            # Position sizing + circuit breakers (daily loss, max drawdown)
  silver_bullet/             # Silver Bullet V1 signal + backtest pipeline
  hmm_regime/                # HMM regime detection
  ml_signals/                # LSTM signal (walk-forward, requires 500+ bars)
  market_data/               # Alpaca + Pyth feed, CandleStore
  agents/                    # Research orchestrator + 5 researchers (TradingAgents wired)
  tests/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your own keys locally
```

### Not included

Some private research inputs and reference material are not part of this repository.

## Testing

```bash
pytest execution/tests/
```

## TradingView Indicators

Pine Script v6. Five active indicators, each mapped to a decision gate.

| Indicator | Gate(s) | Purpose |
|-----------|---------|---------|
| Market Session Lines | 1 | Session time markers |
| Premarket Levels | 2, 5 | Multi-TF OHLC reference + TP targets (not included in this public release) |
| OTE-OR-HTF-PO3 | 2, 3, 4 | OTE Fibonacci + Opening Range + HTF PO3 (not included in this public release) |
| SMC-FVG-ICT-DOB-SH | 3, 4 | BOS/CHoCH + FVG + OB + Stop Hunt (not included in this public release) |
| SMT-CD Divergence | 3, 4 | Confirmed SMT inter-market divergence (MPL-2.0, see `THIRD_PARTY_NOTICES.md`) |

## Silver Bullet V1 Backtest

```bash
python -m execution.silver_bullet.run_backtest --source alpaca --start 2024-01-01 --atr-stop 2.0 --save
```
Results auto-saved to `06_Backtesting_and_Validation/Backtest_Results.md`.

## Environment Variables

Names only; see `.env.example`. Keep values in a local `.env` (git-ignored).

```bash
ANTHROPIC_API_KEY=            # Research agents
TAVILY_API_KEY=               # Web research agent
ALPACA_API_KEY=               # Alpaca historical market data
ALPACA_SECRET_KEY=
UNUSUAL_WHALES_API_KEY=       # Options flow + dark pool (paid subscription required)
```

## Knowledge Base

- `Framework_Master_Index.md` — index of all framework docs, gate-to-doc mapping
- `Framework_Working_Principles.md` — decision guardrails, system rules
- `04_Current_System_and_Indicators/Current_System_Map.md` — **6-gate A+ decision framework**

## Built with Claude Code

Designed and built end-to-end using [Claude Code](https://claude.ai/code).
