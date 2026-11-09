"""Load provider settings from a local dotenv file without printing them.

Lookup order: XULAN_ENV_FILE if set, else the project's .env, else ~/.env.
Variables already present in the environment (for example injected by a
container platform's secret manager) always take precedence.
"""

import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def env_file() -> Path | None:
    explicit = os.getenv('XULAN_ENV_FILE')
    candidates = [Path(explicit).expanduser()] if explicit else [ROOT / '.env', Path.home() / '.env']
    return next((p for p in candidates if p.is_file()), None)


def load_credentials():
    path = env_file()
    if path:
        values = dotenv_values(path, interpolate=False)
        for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL'):
            if not os.getenv(name) and values.get(name):
                os.environ[name] = values[name]
