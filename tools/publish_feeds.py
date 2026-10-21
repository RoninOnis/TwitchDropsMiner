"""
Publishes the two feeds the app refreshes from the repository.

- games_seed.json  - every game a drops campaign has ever been seen for
- campaigns.json   - the campaigns themselves, with their dates, so the app knows which games
                     to probe deep instead of walking the whole catalogue

Run it where the app has been running (a working directory with games_catalogue.json and
drops_scan.json); it keeps its own campaign history next to the script and merges it in.

Usage: python3 tools/publish_feeds.py [--workdir DIR] [--out DIR] [--git-commit]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_WORKDIR = HERE.parent
HISTORY_PATH = HERE / "campaigns_history.json"


def load_json(path: Path) -> dict | list | None:
    try:
        with open(path, encoding="utf8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def merge_campaigns(history: dict[str, dict], scan_data: dict | list | None) -> dict[str, dict]:
    """Adds the campaigns of a fresh scan to the accumulated history."""
    campaigns = scan_data.get("campaigns") if isinstance(scan_data, dict) else None
    if not isinstance(campaigns, dict):
        return history
    for campaign_id, campaign in campaigns.items():
        if not isinstance(campaign, dict):
            continue
        game = campaign.get("game") or {}
        game_name = game.get("displayName") or game.get("name")
        if not game_name:
            continue
        history[campaign_id] = {
            "game": game_name,
            "gameId": game.get("id"),
            "name": campaign.get("name"),
            "startAt": campaign.get("startAt"),
            "endAt": campaign.get("endAt"),
            "drops": len(campaign.get("timeBasedDrops") or []),
            "seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    return history


def build_games(catalogue: dict[str, dict], previous_seed: dict | None) -> list[str]:
    """The seed: games from the catalogue first, then whatever the previous seed knew."""
    names: dict[str, None] = {}
    for name in catalogue:
        names.setdefault(name, None)
    previous = previous_seed.get("games") if isinstance(previous_seed, dict) else None
    for name in previous or []:
        if isinstance(name, str):
            names.setdefault(name, None)
    return list(names)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, default=DEFAULT_WORKDIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_WORKDIR)
    parser.add_argument("--git-commit", action="store_true")
    args = parser.parse_args()

    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    catalogue_data = load_json(args.workdir / "games_catalogue.json") or {}
    catalogue = catalogue_data.get("games") if isinstance(catalogue_data, dict) else {}
    catalogue = catalogue if isinstance(catalogue, dict) else {}
    scan_data = load_json(args.workdir / "drops_scan.json")

    history = load_json(HISTORY_PATH) or {}
    history = history if isinstance(history, dict) else {}
    history = merge_campaigns(history, scan_data)
    HISTORY_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf8"
    )

    # кампании, которые ещё идут или только начнутся - их и публикуем первыми
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    active: list[dict] = []
    for campaign in history.values():
        end_at = campaign.get("endAt") or ""
        if end_at and end_at < now:
            continue
        active.append(campaign)
    active.sort(key=lambda entry: entry.get("endAt") or "")

    campaigns_path = args.out / "campaigns.json"
    campaigns_path.write_text(
        json.dumps(
            {"generated": stamp, "campaigns": active + [
                c for c in history.values() if c not in active
            ]},
            ensure_ascii=False,
            indent=0,
        ),
        encoding="utf8",
    )

    seed_path = args.out / "games_seed.json"
    games = build_games(catalogue, load_json(seed_path))
    seed_path.write_text(
        json.dumps({"generated": stamp, "games": games}, ensure_ascii=False, indent=0),
        encoding="utf8",
    )

    print(f"campaigns: {len(active)} active / {len(history)} known -> {campaigns_path}")
    print(f"games: {len(games)} -> {seed_path}")

    if args.git_commit:
        for path in (campaigns_path, seed_path):
            subprocess.run(["git", "add", str(path)], cwd=args.out, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"Update the drops feeds ({stamp})"], cwd=args.out
        )
        if result.returncode == 0:
            subprocess.run(["git", "push", "origin", "HEAD"], cwd=args.out, check=False)
        print("git:", "committed" if result.returncode == 0 else "nothing to commit")


if __name__ == "__main__":
    main()
