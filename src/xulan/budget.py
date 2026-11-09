import sqlite3
import uuid
from pathlib import Path


class BudgetExceeded(Exception):
    pass


AUTHORIZED_CEILING_USD = 5.0
OPERATING_LIMIT_USD = 4.9  # owner-approved 8 Nov 2026 (was 4.50); stays below the authorized ceiling


class BudgetGuard:
    """Atomic reservations; uncertain charges remain reserved across restarts."""

    def __init__(self, path, limit=OPERATING_LIMIT_USD):
        self.path = str(path)
        self.limit = min(limit, OPERATING_LIMIT_USD)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, cost REAL, settled INTEGER)')

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def reserve(self, amount):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            total = db.execute('SELECT COALESCE(SUM(cost),0) FROM calls').fetchone()[0]
            if total + amount > self.limit:
                raise BudgetExceeded('Test budget exhausted; no API call made.')
            token = uuid.uuid4().hex
            db.execute('INSERT INTO calls VALUES (?,?,0)', (token, amount))
            return token

    def settle(self, token, cost):
        with self.connect() as db:
            db.execute('UPDATE calls SET cost=?, settled=1 WHERE id=?', (cost, token))

    def summary(self):
        with self.connect() as db:
            total, pending = db.execute(
                'SELECT COALESCE(SUM(cost),0), COALESCE(SUM(1-settled),0) FROM calls'
            ).fetchone()
        return dict(
            estimated_or_reserved_usd=round(total, 6),
            uncertain_calls=pending,
            operating_limit_usd=self.limit,
            authorized_ceiling_usd=AUTHORIZED_CEILING_USD,
        )
