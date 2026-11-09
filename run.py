"""Start the backend and frontend together for local development.

    python run.py                  # both, with hot reload
    python run.py --backend        # FastAPI only
    python run.py --frontend       # Next.js only
    python run.py --api-port 8010 --web-port 3010

Standard library only, so it works before any virtualenv exists. The backend
is started through `uv`, which creates backend/.venv on first run.
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
IS_WINDOWS = sys.platform == "win32"


def require(tool: str, hint: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"'{tool}' was not found on PATH. {hint}")
    return path


def backend_cmd(port: int) -> list[str]:
    uv = require("uv", "Install it from https://docs.astral.sh/uv/")
    return [uv, "run", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", str(port)]


def frontend_cmd(port: int) -> list[str]:
    npm = require("npm", "Install Node.js 20+ from https://nodejs.org/")
    if not (FRONTEND / "node_modules").exists():
        print(">> Installing frontend dependencies (first run)...")
        subprocess.run([npm, "install"], cwd=FRONTEND, check=True)
    return [npm, "run", "dev", "--", "--port", str(port)]


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGTERM)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run InstaQuote Studio locally.")
    parser.add_argument("--backend", action="store_true", help="only start the API")
    parser.add_argument("--frontend", action="store_true", help="only start the web app")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-port", type=int, default=3000)
    args = parser.parse_args()
    both = not (args.backend or args.frontend)

    env = os.environ.copy()
    api_url = f"http://localhost:{args.api_port}"
    web_origins = f'["http://localhost:{args.web_port}","http://127.0.0.1:{args.web_port}"]'
    env.setdefault("NEXT_PUBLIC_API_URL", api_url)
    env.setdefault("CORS_ORIGINS", web_origins)

    procs: list[subprocess.Popen] = []
    popen_kwargs = {} if IS_WINDOWS else {"start_new_session": True}
    if both or args.backend:
        procs.append(subprocess.Popen(backend_cmd(args.api_port), cwd=BACKEND, env=env, **popen_kwargs))
    if both or args.frontend:
        procs.append(subprocess.Popen(frontend_cmd(args.web_port), cwd=FRONTEND, env=env, **popen_kwargs))

    print("=" * 60)
    if both or args.frontend:
        print(f"  Web app   http://localhost:{args.web_port}")
    if both or args.backend:
        print(f"  API       {api_url}")
        print(f"  API docs  {api_url}/docs")
    print("  Ctrl+C stops everything")
    print("=" * 60)

    try:
        while all(p.poll() is None for p in procs):
            try:
                procs[0].wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
    except KeyboardInterrupt:
        print("\n>> Shutting down...")
    finally:
        for p in procs:
            stop(p)


if __name__ == "__main__":
    main()
