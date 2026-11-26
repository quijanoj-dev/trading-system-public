"""Sentinel: this repository is research code and must not gain the ability to send orders.

The tests fail when code imports an order surface of a trading SDK, or when a
new file starts talking to the network.

This is NO_TRADE code. Nothing here grants authority to trade.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Policy: block the order surfaces of a trading SDK, not the whole SDK.
# Market-data imports such as alpaca.data.* stay allowed. The price of this
# precision is that an SDK missing from the list enters unnoticed, so a new
# broker or venue dependency must add its order surface here in the same change.
ORDER_CAPABLE_PREFIXES = (
    "alpaca.trading",
    "alpaca.broker",
    "alpaca_trade_api",
    "py_clob_client",
    "ib_insync",
    "ibapi",
)

# Libraries that open a connection. Only the files listed below may import
# them, and each one only reads public or licensed data. A new file that needs
# the network must be added here on purpose, in the same change.
NETWORK_CLIENT_PREFIXES = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib.request",
    "urllib3",
    "http.client",
    "http.server",
    "socket",
    "websocket",
    "websockets",
    "smtplib",
)
NETWORK_READERS = {
    "execution/agents/_tavily.py": "web search for the research agents",
    "execution/market_data/pyth_feed.py": "public price feed, read only",
    "execution/market_data/unusual_whales.py": "licensed market data, read only",
}

SKIP_DIRS = {"node_modules", "__pycache__", "venv", "output"}

# Samples for the controls: a policy that flags nothing, or everything, must fail.
ORDER_SAMPLES = (
    "from alpaca.trading.client import TradingClient",
    "from alpaca import trading",
    "import alpaca.broker.client",
    "import alpaca_trade_api as tradeapi",
    "from py_clob_client.client import ClobClient",
    "from ib_insync import IB",
    "import ibapi.client",
)
ALLOWED_SAMPLES = (
    "from alpaca.data.historical import StockHistoricalDataClient",
    "import alpaca.trading_utils",
    "import pandas as pd",
    "from execution.risk_manager import RiskConfig",
    "from urllib.parse import urlencode",
)


def _matches(module: str, prefixes: tuple) -> bool:
    """Match by whole dotted segments, so "alpaca.trading_utils" is not "alpaca.trading"."""
    return any(module == p or module.startswith(p + ".") for p in prefixes)


def is_order_capable_import(module: str) -> bool:
    return _matches(module, ORDER_CAPABLE_PREFIXES)


def is_network_client_import(module: str) -> bool:
    return _matches(module, NETWORK_CLIENT_PREFIXES)


def _files(suffixes: tuple) -> list:
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        found += [Path(dirpath) / f for f in filenames if f.endswith(suffixes)]
    return sorted(found)


def _imports(source: str, package: tuple = ()) -> list:
    """Absolute dotted names imported by a piece of source, with line numbers."""
    names = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names += [(alias.name, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parent = list(package[: len(package) - (node.level - 1)])
                base = ".".join(parent + ([base] if base else []))
            names.append((base, node.lineno))
            # "from package import submodule" imports a submodule too
            names += [("%s.%s" % (base, alias.name), node.lineno) for alias in node.names]
    return names


def _imports_of(path: Path) -> list:
    source = path.read_text(encoding="utf-8", errors="replace")
    return _imports(source, path.relative_to(REPO).parts[:-1])


def _rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def test_no_order_capable_import():
    offenders = [
        "%s:%d imports %s" % (_rel(f), line, module)
        for f in _files((".py",))
        for module, line in _imports_of(f)
        if is_order_capable_import(module)
    ]
    assert offenders == []


def test_only_listed_readers_import_a_network_client():
    users = sorted({_rel(f) for f in _files((".py",)) for module, _ in _imports_of(f) if is_network_client_import(module)})
    assert users == sorted(NETWORK_READERS)


def test_order_policy_flags_order_surfaces_and_nothing_else():
    """Control: the policy must catch every order sample and none of the allowed ones."""
    missed = [s for s in ORDER_SAMPLES if not any(is_order_capable_import(m) for m, _ in _imports(s))]
    wrongly = [s for s in ALLOWED_SAMPLES if any(is_order_capable_import(m) for m, _ in _imports(s))]
    assert missed == []
    assert wrongly == []


def test_network_policy_flags_clients_and_nothing_else():
    flagged = ("import requests", "from urllib.request import urlopen", "import http.client", "import socket")
    allowed = ("from urllib.parse import urlencode", "import json", "import yfinance as yf")
    assert [s for s in flagged if not any(is_network_client_import(m) for m, _ in _imports(s))] == []
    assert [s for s in allowed if any(is_network_client_import(m) for m, _ in _imports(s))] == []
