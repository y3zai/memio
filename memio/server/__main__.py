"""Entry point for ``python -m memio.server`` and ``memio-server`` CLI."""

from __future__ import annotations

import sys


def main() -> None:
    missing = []
    for mod in ("fastapi", "uvicorn", "yaml"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(
            f"memio server dependencies not installed (missing: {', '.join(missing)}).\n"
            "Install with: pip install memio[server]",
            file=sys.stderr,
        )
        sys.exit(1)

    import uvicorn

    from memio.server.config import load_config

    config = load_config()
    uvicorn.run(
        "memio.server.app:create_app",
        factory=True,
        host=config.host,
        port=config.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
