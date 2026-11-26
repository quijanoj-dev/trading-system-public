# Trading System Architecture v1

**Stack:** Futures data feed / execution platform (not included) / TradingView PineScript v6
**Methodology:** ICT-SMC PO3-AMD + volume divergence
**Status:** Phase 1 complete (paper trading). Phase 2: analyze 30+ live fills.

> **Public release note:** the execution, bridge, copy-trading and circuit-breaker layers below are
> design notes only. No order-execution code is included in this repository.

---

## System Architecture — Data Flow

```
╔══════════════════════════════════════════════════════════════════╗
║               TRADING SYSTEM — INTEGRATED DATA FLOW              ║
╚══════════════════════════════════════════════════════════════════╝

                        [CME Exchange]
                      ES / NQ futures tick
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
  [Futures data feed]                 [TradingView CME Sub]
  [Prop-firm account]                   (analysis / replay)
   live tick + L2 data                         │
          │                                    │
          ▼                                    ▼
  [Execution platform]         [PineScript v6 Indicators]
   ├ Signal detection            ├ CVD_Divergence.pine
   ├ Order routing               ├ SMC-FVG-ICT-DOB-SH.pine (not included)
   └ Risk management             ├ Silver_Bullet_V1_Strategy.pine
          │                      └ Market_Internals.pine
          │                                    │
          │                             [TV Alert fired]
          │                                    │
          │                          [TradingView MCP]
          │                           (webhook bridge)
          │◄──────────────────────────────────-┘
          │     order instruction (JSON)
          ▼
  [Execution platform — Execution]
   order → CME
          │
    ┌─────┴─────────────────┐
    ▼                       ▼
[Trade copier]        [Manual override]
[Primary→Mirror]      (discretionary)
    │
    ▼
[Cross-broker copier]
 └ Cross-broker multi-account scaling
```

---

## Layer Definitions

### Layer 1 — Data (Source)

| Feed | Provider | Protocol | Purpose |
|------|----------|----------|---------|
| ES / NQ live tick | Prop-firm data feed | Broker API | Execution + signal detection |
| ES / NQ 1m bars | TradingView CME subscription | WebSocket | Strategy analysis, replay, alerts |
| ES=F / NQ=F historical | Alpaca (SPY/QQQ proxy) | REST | Python backtesting (proxy only) |

**Phase 3 upgrade path:** Replace Alpaca proxy with real ES/NQ 1m from a futures data vendor
(e.g. IBKR via `ib_insync`). Target: 3+ years × 30+ signals/year for statistical validity.

### Layer 2 — Analysis & Strategy (Brain)

**Platform:** TradingView PineScript v6
**Core indicators** (`08_TradingView_Indicators/`):

| File | Purpose |
|------|---------|
| `Silver_Bullet_V1_Strategy.pine` | SBV1 — 10:00–11:00 ET setup, all gates |
| `mmt/CVD_Divergence.pine` | Cumulative volume delta divergence signal |
| `SMC-FVG-ICT-DOB-SH.pine` | FVG / stop hunt / order block detection (not included in this public release) |
| `Market_Internals.pine` | Breadth / internals overlay |
| `Premarket Levels.pine` | PDH/PDL/ON levels (not included in this public release) |

**Methodology:** ICT-SMC PO3-AMD 6-gate framework
1. HTF bias confirmation (15m EMA-20)
2. Session window gate (10:00–11:00 ET, dead zone 10:30–10:45 excluded)
3. Stop hunt detection (60-bar lookback)
4. FVG entry ≥0.05 pts
5. SMT divergence (ES vs NQ booster — A+ grade)
6. Expiry gate (20 bars max)

**Research layer:** Python backtester (`execution/silver_bullet/`) + TradingAgents
(Python 3.12+ virtualenv, `ta_multi.py`) for fundamental/news bias on top 10 NASDAQ names.

### Layer 3 — Execution (Action) — design only, not included

**Platform:** Execution platform connected to a prop-firm account
**Order type:** Bracket order (stop + target pre-wired)
**Position sizing:** 1 micro contract (MES/MNQ) during evaluation

### Layer 4 — Bridge (TradingView → execution platform) — design only, not included

Two options; Option A for production:

**Option A — Webhook listener (production):**
```
Pine alertcondition fires
  → TV sends HTTP POST to cloudflare/ngrok tunnel
  → Execution-platform add-on listener receives payload:
    {"symbol":"ES","action":"BUY","qty":1,"stop":4580.25,"target":4595.75}
  → Bracket order executes
Latency: ~50–150ms
```

**Option B — TradingView MCP (paper / testing):**
```
TradingView MCP polls chart state every 500ms
  → Reads data_get_pine_labels / chart_get_state for signal
  → Calls the execution platform's local API with a bracket order
Latency: ~300–500ms (MCP poll gap — acceptable for paper only)
```

### Layer 5 — Copy-Trading & Scaling — design only, not included

**Trade copier (same platform):**
```
Primary account (1 MES/MNQ)
  └── Mirror → account 2
  └── Mirror → account 3
  └── Mirror → Evaluation accounts
```
All mirrors execute at identical sizing. The copier copies fills, not signals.

**Cross-broker copier:**
```
Primary account → copier webhook
  └── Broker B
  └── Hedge accounts
```
Use when scaling beyond accounts on the primary platform.

---

## Strategy Enhancement — Backtest Findings

From `06_Backtesting_and_Validation/Backtest_Results.md` (Alpaca SPY proxy, 2024–2026):

| Gate added | Signals | Win% | PF | Sharpe |
|------------|---------|------|----|--------|
| Baseline | 65 | 24.2% | 0.86 | -0.36 |
| + HTF EMA-20 | 25 | 40.9% | 2.24 | 5.94 |
| + Dead zone cut (10:30–10:45) | **14** | **58.3%** | **3.71** | **9.23** |

**Critical finding:** The 10:30–10:45 dead zone exclusion is the single highest-impact gate.
Removing losing signals with no winners cut is the correct approach — do not relax this gate.

**Pine Script parameter equivalents (must stay in sync with Python backtester):**

```pine
// ─── SBV1 Gate Parameters ───────────────────────────────────
int   SH_BARS     = 60      // stop hunt lookback
int   SWING_LEN   = 10      // swing high/low detection
float FVG_MIN     = 0.05    // min FVG size (SPY proxy pts)
                             // ES equivalent: ~1.25 pts (×25 scaling)
int   EXPIRY_BARS = 20      // signal expiry
float ATR_STOP    = 2.0     // stop distance in ATR(14) multiples
float R_TARGET    = 3.0     // reward:risk
int   HTF_EMA     = 20      // HTF EMA period (15m)

// ─── Session Gate ────────────────────────────────────────────
bool inWindow = (hour == 10 and minute >= 0 and minute < 30)
             or (hour == 10 and minute >= 46)  // skip 10:30-10:45

// ─── HTF Bias Gate ───────────────────────────────────────────
float htfEma = request.security(syminfo.tickerid, "15", ta.ema(close, HTF_EMA))
bool longBias  = close > htfEma
bool shortBias = close < htfEma
```

---

## Circuit Breakers — design only, not included

Design target for a live session monitor (not included in this public release).

| Breaker | Threshold | Response |
|---------|-----------|----------|
| Daily max loss | −$300 (2R on 1 MES) | Halt orders, write to Forward_Test_Notes.md |
| Consecutive losses | 3 in a row | Pause + manual review |
| Session drawdown | −1% account balance | Kill switch — flatten all positions |
| Out-of-gate signal | Trade outside 10:00–11:00 ET | Auto-reject at the execution platform |
| Prop-firm daily loss limit | Account-specific (check the firm's rules) | Hard stop — a breach fails the evaluation |

**Implementation target:** `execution/silver_bullet/circuit_breaker.py`
- Polls the execution platform's account P&L every 60s during session
- Writes a local `circuit_breaker_state.json`
- The session monitor reads state and fires an alert if any breaker tripped

---

## Phase Roadmap

| Phase | Status | Gate |
|-------|--------|------|
| 1 — Monitor + Paper Executor | ✓ DONE (not included in this public release) | Auto-detect + paper trading |
| 2 — Analyze Paper Results | Next | 30+ trades in Forward_Test_Notes.md |
| 3 — Real Futures Data | Blocked | ES/NQ 1m from a futures data vendor |
| 4 — Live execution | Future | Phase 2 metrics hold + prop-firm evaluation passed |
| 5 — Copy-trading scaling | Future | 1 funded account profitable for 60+ days |

---

## Key File Paths

```
<PROJECT_ROOT>/
├── 08_TradingView_Indicators/          # Pine Script files
│   ├── Silver_Bullet_V1_Strategy.pine
│   └── mmt/CVD_Divergence.pine
├── execution/silver_bullet/
│   ├── signals.py                      # Python signal detection
│   └── run_backtest.py                 # Backtest runner
├── execution/silver_bullet/ta_multi.py # TradingAgents batch (10 tickers)
├── 06_Backtesting_and_Validation/
│   ├── Backtest_Results.md             # Optimized params + walk-forward results
│   └── Forward_Test_Notes.md           # Paper trade log
└── control-plane/trading-system-docs/
    └── architecture-v1.md              # This file
```
