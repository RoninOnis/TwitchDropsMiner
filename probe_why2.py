"""Разбор по частям, почему _check_drops_enabled даёт False."""
import asyncio, sys
from types import SimpleNamespace
sys.path.insert(0, ".")
from constants import GQL_QUERIES
from settings import Settings
from translate import _
from twitch import Twitch

async def main():
    _.set_language("English")
    c = Twitch(Settings(SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0)))
    try:
        await c.get_auth()
        await c.fetch_inventory()
        campaign = next(x for x in c.inventory if x.game.name == "Marbles on Stream" and x.active and x.drops)
        print("кампания:", campaign.name, "| id:", campaign.id)
        print("  allowed_channels:", len(campaign.allowed_channels or []),
              "| каналы в ACL:", [ch._login for ch in (campaign.allowed_channels or [])][:5])
        channels = await c.get_live_streams(campaign.game, drops_enabled=True)
        for channel in list(channels)[:3]:
            resp = await c.gql_request(GQL_QUERIES["AvailableDrops"].with_variables({"channelID": str(channel.id)}))
            drops = resp["data"]["channel"]["viewerDropCampaigns"] or []
            data = drops[0] if drops else {}
            known = c._campaigns.get(data.get("id"))
            print(f"\nканал {channel._login}: кампаний от Twitch={len(drops)}")
            print("  id из ответа:", data.get("id"), "| найден в приложении:", known is not None,
                  "| тот же объект:", known is campaign if known else None)
            print("  в ACL кампании:", channel in (campaign.allowed_channels or []))
            print("  campaign._base_can_earn(channel, True):", campaign._base_can_earn(channel, True))
            print("  campaign._base_can_earn(None, True):", campaign._base_can_earn(None, True))
            print("  any(drop._base_can_earn()):", any(d._base_can_earn() for d in (known or campaign).drops))
            print("  known.can_earn(channel, True):", known.can_earn(channel, True) if known else None)
            print("  _check_drops_enabled:", channel._check_drops_enabled(drops))
            break
    finally:
        await c.shutdown()

asyncio.run(main())
