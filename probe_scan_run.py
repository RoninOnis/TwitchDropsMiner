"""
Run a real drop scan with the user's own settings/catalogue and report what it cost.

Usage: PYTHONPATH=. xvfb-run -a ./env/bin/python probe_scan_run.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from types import SimpleNamespace

from settings import Settings
from translate import _
from twitch import Twitch

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
args = SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0)


async def main() -> None:
    _.set_language("English")
    settings = Settings(args)
    print(
        f"priority={len(settings.priority)} games, depth {settings.scan_channels_per_game}"
        f"/{settings.scan_priority_channels}, interval={settings.scan_interval_minutes} min"
    )
    client = Twitch(settings)
    try:
        await client.get_auth()
        started = time.time()
        scan_data = await client.scan_drops()
        elapsed = time.time() - started
        print(f"\nscan took {elapsed:.1f}s")
        print(f"games probed: {scan_data.get('games_probed')}, channels asked: {scan_data.get('channels_asked')}")
        print(f"games with drops ({len(scan_data.get('games_with_drops') or [])}): {scan_data.get('games_with_drops')}")
        for cid, campaign in (scan_data.get("campaigns") or {}).items():
            print(f"  campaign: {campaign['game']['displayName']} | {campaign['name']} | ends {campaign['endAt']}")
    finally:
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
