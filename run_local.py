"""Start the local-only studio using the installed virtual environment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
if __name__ == '__main__':
    import uvicorn

    uvicorn.run('xulan.app:app', host='127.0.0.1', port=8000)
