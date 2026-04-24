"""
Entrypoint du worker : lance arq avec les WorkerSettings.

Équivalent CLI : `arq src.worker.worker_settings.WorkerSettings`
On l'embarque ici pour avoir un seul `python -m src.worker.main` partout.
"""

from __future__ import annotations

from arq.worker import run_worker

from src.worker.worker_settings import WorkerSettings


def main() -> None:
    run_worker(WorkerSettings)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()