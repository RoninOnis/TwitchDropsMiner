"""
Checks what the priority game selector actually ends up listing.

Usage: xvfb-run -a ./env/bin/python probe_gamelist.py
"""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace

from settings import Settings
from translate import _
from twitch import Twitch

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
args = SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0)


async def main() -> None:
    _.set_language("English")
    settings = Settings(args)  # type: ignore[arg-type]
    print(f"scan_drops={settings.scan_drops} priority={settings.priority!r}")
    client = Twitch(settings)
    try:
        await client.get_auth()
        await client.fetch_inventory()
        campaigns = list(client.inventory)
        games = {
            campaign.game
            for campaign in campaigns
            if not campaign.game.is_channel_drops()
        }
        print(f"campaigns: {len(campaigns)}, distinct games: {len(games)}")
        scan_data, stale = client.load_scan_cache()
        print(f"scan cache: {'present' if scan_data else 'MISSING'}, stale={stale}, "
              f"games in cache={len(scan_data.get('games_with_drops') or [])}")
        client.gui.set_games(games)
        listed = client.gui.settings._game_names
        print(f"\ngame selector would list {len(listed)} game(s):")
        for name in sorted(listed):
            print(f"  {name}")
    finally:
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
