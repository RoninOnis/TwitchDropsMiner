"""Сколько каналов реально отдают дропы и что про них думает приложение."""
import asyncio, sys
from types import SimpleNamespace
sys.path.insert(0, ".")
from constants import GQL_QUERIES
from settings import Settings
from translate import _
from twitch import Twitch

async def main():
    _.set_language("English")
    s = Settings(SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0))
    c = Twitch(s)
    try:
        await c.get_auth()
        await c.fetch_inventory()
        print("wanted_games:", sorted(c.wanted_games)[:5], "| всего:", len(c.wanted_games))
        target = next((x for x in c.inventory if x.active and x.drops and not x.game.is_special()), None)
        print("игра:", target.game.name, "| кампания:", target.name)
        channels = await c.get_live_streams(target.game, drops_enabled=True)
        channels = sorted(channels, key=lambda ch: ch._stream.viewers if ch._stream else 0, reverse=True)[:15]
        print(f"взяли {len(channels)} самых популярных каналов")
        answered = 0
        app_true = 0
        mismatch = 0
        for channel in channels:
            resp = await c.gql_request(GQL_QUERIES["AvailableDrops"].with_variables({"channelID": str(channel.id)}))
            drops = resp["data"]["channel"]["viewerDropCampaigns"] or []
            before = channel.drops_enabled
            channel.update_available_drops(drops)
            after = channel.drops_enabled
            if drops:
                answered += 1
            if after:
                app_true += 1
            if bool(drops) != after:
                mismatch += 1
                print(f"  {channel._login:20} зрителей={channel._stream.viewers if channel._stream else 0:6} "
                      f"кампаний от Twitch={len(drops)} значок: было={before} стало={after}")
            await asyncio.sleep(0.3)
        print(f"\nитог: Twitch вернул кампании у {answered} из {len(channels)}; "
              f"приложение считает «можно фармить» у {app_true}; расхождений {mismatch}")
    finally:
        await c.shutdown()

asyncio.run(main())
