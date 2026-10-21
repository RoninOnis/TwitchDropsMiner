"""Почему кампания с живыми каналами считается невыгодной."""
import asyncio, sys
from types import SimpleNamespace
sys.path.insert(0, ".")
from settings import Settings
from translate import _
from twitch import Twitch

async def main():
    _.set_language("English")
    c = Twitch(Settings(SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0)))
    try:
        await c.get_auth()
        await c.fetch_inventory()
        for campaign in c.inventory:
            if campaign.game.name != "Marbles on Stream" or not campaign.active:
                continue
            print(f"кампания: {campaign.name}")
            print(f"  eligible={campaign.eligible} linked={campaign.linked} active={campaign.active} "
                  f"finished={campaign.finished} upcoming={campaign.upcoming} expired={campaign.expired}")
            print(f"  starts={campaign.starts_at:%Y-%m-%d %H:%M} ends={campaign.ends_at:%Y-%m-%d %H:%M} "
                  f"required_minutes={campaign.required_minutes}")
            print(f"  can_earn_without_channel={campaign._base_can_earn()}")
            for drop in campaign.drops:
                print(f"   дроп {drop.name[:34]:34} claimed={drop.is_claimed} req={drop.required_minutes} "
                      f"current={drop.current_minutes} base={drop._base_can_earn()} "
                      f"ends={drop.ends_at:%Y-%m-%d}")
        # сводка: сколько кампаний вообще «можно фармить»
        bad = [x for x in c.inventory if x.active and x.drops and not x._base_can_earn()]
        good = [x for x in c.inventory if x.active and x.drops and x._base_can_earn()]
        print(f"\nвсего активных кампаний с дропами: {len(good) + len(bad)}; можно фармить: {len(good)}; "
              f"нельзя: {len(bad)}")
        for x in bad[:8]:
            reasons = []
            if not x.eligible: reasons.append("не eligible (нет привязки)")
            if x.finished: reasons.append("finished (все дропы собраны или 0 минут)")
            print(f"   {x.game.name[:24]:24} {x.name[:30]:30} -> {', '.join(reasons) or 'другое'}")
    finally:
        await c.shutdown()

asyncio.run(main())
