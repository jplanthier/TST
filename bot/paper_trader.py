from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from .utils import DATA_DIR, logger

DB_PATH = DATA_DIR / "paper_trades.db"

@dataclass
class Position:
    id: int
    symbol: str
    side: str           # LONG or SHORT
    entry: float
    qty: float
    status: str         # OPEN or CLOSED

class PaperTrader:
    def __init__(self, starting_balance: float = 10000.0, risk_pct: float = 1.0):
        self.conn = sqlite3.connect(DB_PATH)
        self.ensure_tables()
        self.ensure_balance(starting_balance)
        self.risk_pct = risk_pct

    def ensure_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS balance (
                id INTEGER PRIMARY KEY CHECK (id=1),
                cash REAL NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry REAL NOT NULL,
                qty REAL NOT NULL,
                status TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def ensure_balance(self, start: float):
        cur = self.conn.cursor()
        cur.execute("SELECT cash FROM balance WHERE id=1")
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO balance (id, cash) VALUES (1, ?)", (start,))
            self.conn.commit()

    def get_cash(self) -> float:
        cur = self.conn.cursor()
        cur.execute("SELECT cash FROM balance WHERE id=1")
        return float(cur.fetchone()[0])

    def set_cash(self, amount: float):
        cur = self.conn.cursor()
        cur.execute("UPDATE balance SET cash=? WHERE id=1", (amount,))
        self.conn.commit()

    def open_position(self, symbol: str, side: str, price: float) -> Position:
        # position size: risk_pct of equity, market order approximation
        cash = self.get_cash()
        risk = cash * (self.risk_pct / 100.0)
        qty = max(0.0001, risk / price)  # simplistic sizing
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO positions (symbol, side, entry, qty, status) VALUES (?,?,?,?,?)",
            (symbol, side, price, qty, "OPEN"),
        )
        self.conn.commit()
        pid = cur.lastrowid
        logger.info(f"Opened paper position {pid}: {side} {qty} {symbol} @ {price}")
        return Position(pid, symbol, side, price, qty, "OPEN")

    def close_position(self, pos_id: int, exit_price: float):
        cur = self.conn.cursor()
        cur.execute("SELECT symbol, side, entry, qty FROM positions WHERE id=? AND status='OPEN'", (pos_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Position not found or already closed")
        symbol, side, entry, qty = row
        pnl = (exit_price - entry) * qty * (1 if side == "LONG" else -1)

        cash = self.get_cash()
        self.set_cash(cash + pnl)
        cur.execute("UPDATE positions SET status='CLOSED' WHERE id=?", (pos_id,))
        self.conn.commit()
        logger.info(f"Closed position {pos_id} @ {exit_price} PnL={pnl:.2f}")
        return pnl

    def get_open_positions(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, symbol, side, entry, qty, status FROM positions WHERE status='OPEN'")
        rows = cur.fetchall()
        return [Position(*r) for r in rows]
