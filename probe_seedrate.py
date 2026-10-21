"""How many new games do N consecutive category-search queries bring in?"""
from __future__ import annotations
import asyncio, json, sys, uuid
from types import SimpleNamespace
sys.path.insert(0, ".")
from constants import CATALOGUE_SEED_QUERIES, GQL_QUERIES
from settings import Settings
from translate import _
from twitch import Twitch

args = SimpleNamespace(log=False, tray=False, dump=False, debug_ws=False, debug_gql=False, _verbose=0)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20

async def main():
    _.set_language("English")
    client = Twitch(Settings(args))
    try:
        await client.get_auth()
        known = set(client.load_game_catalogue())
        seed = client.load_catalogue_seed_state()
        start = int(seed.get("term_index") or 0)
        print(f"catalogue: {len(known)} games, seed starts at term {start} ({CATALOGUE_SEED_QUERIES[start]!r})")
        new = []
        for i in range(N):
            term = CATALOGUE_SEED_QUERIES[(start + i) % len(CATALOGUE_SEED_QUERIES)]
            variables = {"platform": "web", "query": term,
                         "options": {"targets": None, "shouldSkipDiscoveryControl": False},
                         "requestID": str(uuid.uuid4())}
            try:
                resp = await client.gql_request(GQL_QUERIES["SearchCategories"].with_variables(variables))
            except Exception as exc:
                print(f"  {term!r}: failed: {str(exc)[:80]}")
                continue
            gf = ((resp.get("data") or {}).get("searchFor") or {}).get("games") or {}
            names = [(e.get("item") or {}).get("displayName") for e in (gf.get("edges") or [])]
            fresh = [n for n in names if n and n not in known]
            known.update(fresh)
            new.extend(fresh)
            print(f"  {term!r}: {len(names)} items, {len(fresh)} new")
        print(f"\n{N} queries -> {len(new)} new games ({len(new)/N:.1f} per query)")
    finally:
        await client.shutdown()

asyncio.run(main())
