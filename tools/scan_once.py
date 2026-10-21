"""
Runs one drop scan and exits - the scheduled job that keeps the published feeds fresh.

Needs a display for the tray icon, so run it under xvfb-run on a headless machine.
Usage: python3 tools/scan_once.py [--workdir DIR]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent


async def scan(workdir: Path) -> None:
    # the app derives its working directory from argv[0]: point it at the working directory,
    # otherwise it looks for settings.json and lang/ next to this script
    sys.argv[0] = str(workdir / "main.py")
    sys.path.insert(0, str(workdir))
    from settings import Settings  # noqa: PLC0415
    from translate import _  # noqa: PLC0415
    from twitch import Twitch  # noqa: PLC0415

    _.set_language("English")
    args = SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0)
    client = Twitch(Settings(args))
    started = time.time()
    try:
        await client.get_auth()
        data = await client.scan_drops()
    finally:
        await client.shutdown()
    print(
        json.dumps(
            {
                "took": round(time.time() - started, 1),
                "games_probed": data["games_probed"],
                "channels_asked": data["channels_asked"],
                "campaigns": len(data["campaigns"]),
                "games_with_drops": len(data["games_with_drops"]),
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, default=HERE.parent)
    args = parser.parse_args()
    asyncio.run(scan(args.workdir))


if __name__ == "__main__":
    main()
