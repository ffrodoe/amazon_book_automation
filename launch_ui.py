import os
import sys
import time
import socket
import threading
import webbrowser
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DEPS_DIR = ROOT_DIR / ".deps"


def setup_paths():
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    if DEPS_DIR.exists():
        if str(DEPS_DIR) not in sys.path:
            sys.path.insert(0, str(DEPS_DIR))
        dll_dirs = [
            DEPS_DIR,
            DEPS_DIR / "pymupdf",
            DEPS_DIR / "fitz",
            DEPS_DIR / "PIL",
            DEPS_DIR / "numpy.libs",
            DEPS_DIR / "pillow.libs",
        ]
        existing = [str(d) for d in dll_dirs if d.is_dir()]
        if existing:
            os.environ["PATH"] = os.pathsep.join(existing) + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                for d in existing:
                    try:
                        os.add_dll_directory(d)
                    except OSError:
                        pass


def get_free_port(host: str = "127.0.0.1", default_port: int = 8000) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        if s.connect_ex((host, default_port)) != 0:
            return default_port
    for port in range(8001, 8010):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex((host, port)) != 0:
                return port
    return default_port


def open_browser_when_ready(url: str, host: str, port: int):
    for _ in range(50):
        time.sleep(0.1)
        try:
            with socket.create_connection((host, port), timeout=0.3):
                webbrowser.open(url)
                return
        except OSError:
            pass


def main():
    setup_paths()

    # Fast path: import directly in current process without spawning extra subprocesses
    try:
        import uvicorn
        from src.web.app import app
    except ImportError as exc:
        print(f"[INFO] Missing dependency ({exc}). Installing requirements...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(ROOT_DIR / "requirements.txt")])
        setup_paths()
        import uvicorn
        from src.web.app import app

    host = "127.0.0.1"
    port = get_free_port(host, 8000)
    url = f"http://{host}:{port}"

    print(f"Starting server at {url} ...", flush=True)

    threading.Thread(
        target=open_browser_when_ready,
        args=(url, host, port),
        daemon=True
    ).start()

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
