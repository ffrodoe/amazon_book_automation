import gc
import os
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator

_REGISTRY_LOCK = threading.Lock()
_PATH_LOCKS: Dict[str, threading.RLock] = {}
_DIR_LOCKS: Dict[str, threading.RLock] = {}

# Windows sharing/access violation error codes that can occur transiently
_TRANSIENT_WINERRORS = {5, 32}


def _norm_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def get_path_lock(path: Path) -> threading.RLock:
    """Returns a reentrant lock dedicated to a specific normalized file path."""
    key = _norm_key(path)
    with _REGISTRY_LOCK:
        lock = _PATH_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _PATH_LOCKS[key] = lock
        return lock


def get_dir_lock(directory: Path) -> threading.RLock:
    """Returns a reentrant lock dedicated to a specific normalized directory path."""
    key = _norm_key(directory)
    with _REGISTRY_LOCK:
        lock = _DIR_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _DIR_LOCKS[key] = lock
        return lock


@contextmanager
def lock_directories(*directories: Path) -> Iterator[None]:
    """
    Acquires directory locks in deterministic sorted order to prevent deadlocks
    when input and output directories differ.
    """
    unique_keys = sorted({_norm_key(d) for d in directories if d is not None})
    locks = []
    with _REGISTRY_LOCK:
        for key in unique_keys:
            lock = _DIR_LOCKS.get(key)
            if lock is None:
                lock = threading.RLock()
                _DIR_LOCKS[key] = lock
            locks.append(lock)

    acquired = []
    try:
        for lock in locks:
            lock.acquire()
            acquired.append(lock)
        yield
    finally:
        for lock in reversed(acquired):
            lock.release()


def is_hidden_or_temp_file(path: Path) -> bool:
    """Returns True for dotfiles and internal temporary files (e.g. .tmp_upscale_8.png)."""
    return path.name.startswith(".")


def make_temp_path(target_path: Path, prefix: str = ".tmp_") -> Path:
    """Creates a unique temporary file path in the same directory as target_path."""
    token = uuid.uuid4().hex[:8]
    return target_path.with_name(f"{prefix}{token}_{target_path.name}")


def _is_transient_lock_error(exc: OSError) -> bool:
    if isinstance(exc, PermissionError):
        return True
    winerr = getattr(exc, "winerror", None)
    return winerr in _TRANSIENT_WINERRORS


def safe_unlink(path: Path, retries: int = 8, initial_delay: float = 0.05) -> None:
    """Removes a file if it exists, tolerating transient Windows file locks."""
    delay = initial_delay
    for attempt in range(retries):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            if not _is_transient_lock_error(exc) or attempt == retries - 1:
                return
            if attempt == 0:
                gc.collect()
            time.sleep(delay)
            delay = min(0.25, delay * 1.4)


def atomic_replace(
    temp_path: Path,
    target_path: Path,
    retries: int = 20,
    initial_delay: float = 0.05,
) -> None:
    """
    Atomically replaces target_path with temp_path under a per-file lock,
    retrying transient Windows sharing violations ([WinError 32] / [WinError 5]).
    Cleans up temp_path if replacement fails.
    """
    file_lock = get_path_lock(target_path)
    delay = initial_delay
    last_exc: OSError | None = None

    try:
        for attempt in range(retries):
            try:
                with file_lock:
                    os.replace(temp_path, target_path)
                return
            except OSError as exc:
                last_exc = exc
                if not _is_transient_lock_error(exc) or attempt == retries - 1:
                    raise
                if attempt == 0:
                    gc.collect()
                time.sleep(delay)
                delay = min(0.25, delay * 1.3)
        if last_exc is not None:
            raise last_exc
    except Exception:
        safe_unlink(temp_path)
        raise


def read_file_bytes_safe(path: Path, retries: int = 10, initial_delay: float = 0.03) -> bytes:
    """
    Reads entire file into memory under a per-file lock and immediately closes the OS handle.
    Prevents long-lived HTTP FileResponse handles from blocking os.replace on Windows.
    """
    file_lock = get_path_lock(path)
    delay = initial_delay
    for attempt in range(retries):
        try:
            with file_lock:
                with open(path, "rb") as f:
                    return f.read()
        except FileNotFoundError:
            raise
        except OSError as exc:
            if not _is_transient_lock_error(exc) or attempt == retries - 1:
                raise
            time.sleep(delay)
            delay = min(0.2, delay * 1.4)
    raise FileNotFoundError(str(path))

