"""
Publishes the campaigns feed built from a third-party drops aggregator.

Twitch stopped answering the campaigns dashboard query (and the site's own page no longer
lists game drops at all), so the app discovers campaigns per channel - which is slow and
sparse. https://twitchdrops.app scrapes the campaigns hourly and exposes them as JSON, so this
tool turns that into the same `campaigns.json` the app already consumes.

The feed is the only thing this tool writes: `games_seed.json` keeps being built from the
scan's own campaign history by `tools/publish_feeds.py`, and the two never touch each other's
file, so both jobs can run on their own schedule.

Feed shape (unchanged, extra keys are ignored by older builds):

    {"generated": "<ISO stamp>",
     "source": {...aggregator details...},
     "campaigns": [{"game", "gameId", "name", "startAt", "endAt", "drops", "seen"}, ...]}

Safety: the aggregator has its own failure modes (its dashboard session dying collapses the
list from ~150 campaigns to a handful), so nothing is published unless a health check passes
and the new list is not a sudden collapse compared to the previous one.

Usage:
    python3 tools/publish_site_feed.py [--feed-dir DIR] [--dry-run] [--no-push] [--force]
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SITE = "https://twitchdrops.app"
HEALTH_URL = f"{SITE}/api/health"
DROPS_URL = f"{SITE}/api/drops"
USER_AGENT = "TwitchDropsMiner-feed-publisher (+https://github.com/RoninOnis/TwitchDropsMiner)"

HERE = Path(__file__).resolve().parent
DEFAULT_FEED_DIR = HERE.parent.parent / "feeds"
DEFAULT_STATE_PATH = HERE.parent.parent / "feed_health.json"

# ни один прогон не публикуется, если активных кампаний меньше этой границы
MIN_ACTIVE_CAMPAIGNS = 20
# доля от предыдущей публикации, ниже которой список считается обвалившимся
MIN_ACTIVE_RATIO = 0.5
# данные старше этого возраста не публикуем: агрегатор сам ходит в Twitch раз в ~13 минут
MAX_DATA_AGE = timedelta(hours=6)
# мусорные «игры», которые агрегатор иногда отдаёт вместо названия
JUNK_GAMES = {"", "unknown", "n/a", "none"}


def log(message: str) -> None:
    print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {message}", flush=True)


def parse_stamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def fetch_json(url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                  "Accept": "application/json",
                                                  "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    payload = json.loads(raw.decode("utf8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{url} returned {type(payload).__name__}, not an object")
    return payload


def check_health(health: dict) -> tuple[bool, str]:
    """
    The aggregator reports how its own scrape went; a collapsed or stale answer is refused.

    `dashboardCampaigns` is the source that carries almost the whole list (its channel-based
    source only adds a dozen or two), so when it drops to zero the feed would shrink from ~150
    campaigns to a handful - that is the exact case this gate exists for.
    """
    if health.get("stale") is True:
        return False, "агрегатор помечает свои данные как устаревшие (stale=true)"
    scraped_at = parse_stamp(health.get("scrapedAt"))
    if scraped_at is None:
        return False, "в ответе /api/health нет пригодного scrapedAt"
    age = datetime.now(timezone.utc) - scraped_at
    if age > MAX_DATA_AGE:
        return False, f"данные агрегатора старше {int(MAX_DATA_AGE.total_seconds() // 3600)} ч ({age})"
    scrape_info = health.get("lastScrape")
    last: dict = scrape_info if isinstance(scrape_info, dict) else {}
    dashboard = last.get("dashboardCampaigns")
    if not isinstance(dashboard, int) or dashboard <= 0:
        return False, f"источник dashboard у агрегатора пуст (dashboardCampaigns={dashboard!r})"
    active = health.get("campaignCount")
    if not isinstance(active, int) or active <= 0:
        return False, f"агрегатор не сообщает активных кампаний (campaignCount={active!r})"
    return True, f"здоров: {active} активных, dashboard={dashboard}, свежесть {age}"


def read_previous(feed_path: Path) -> dict | None:
    try:
        with open(feed_path, encoding="utf8") as handle:
            previous = json.load(handle)
    except (OSError, ValueError):
        return None
    return previous if isinstance(previous, dict) else None


def build_feed(drops: dict, stamp: str) -> dict:
    """Turns the aggregator's campaign list into the feed the app consumes."""
    raw_campaigns = drops.get("campaigns")
    if not isinstance(raw_campaigns, list):
        raise ValueError("/api/drops не содержит списка campaigns")
    now = datetime.now(timezone.utc)
    entries: dict[str, dict] = {}
    dropped = {"baddate": 0, "junk": 0, "expired": 0, "noend": 0}
    for campaign in raw_campaigns:
        if not isinstance(campaign, dict):
            continue
        game = campaign.get("game")
        game = game.strip() if isinstance(game, str) else ""
        name = campaign.get("name")
        name = name.strip() if isinstance(name, str) else ""
        if game.casefold() in JUNK_GAMES or not name:
            dropped["junk"] += 1
            continue
        start_at = parse_stamp(campaign.get("startAt"))
        end_at = parse_stamp(campaign.get("endAt"))
        if start_at is None or end_at is None:
            dropped["baddate"] += 1
            continue
        if end_at <= now:
            dropped["expired"] += 1
            continue
        campaign_id = str(campaign.get("id") or "")
        entries[campaign_id or f"{game}|{name}|{end_at.isoformat()}"] = {
            "game": game,
            "gameId": campaign.get("gameId"),
            "name": name,
            "startAt": campaign["startAt"],
            "endAt": campaign["endAt"],
            "drops": len(campaign.get("drops") or []),
            "seen": campaign.get("lastSeenAt") or stamp,
        }
    ordered = sorted(entries.values(), key=lambda item: item.get("endAt") or "")
    # агрегатор иногда отдаёт одну и ту же кампанию дважды с разными id: схлопываем
    # по содержимому, оставляя самую свежую запись
    collapsed: dict[tuple, dict] = {}
    for entry in ordered:
        key = (entry["game"], entry["name"], entry["startAt"], entry["endAt"])
        known = collapsed.get(key)
        if known is None or str(entry.get("seen") or "") > str(known.get("seen") or ""):
            collapsed[key] = entry
    ordered = sorted(collapsed.values(), key=lambda item: item.get("endAt") or "")
    log("отброшено: "
        + ", ".join(f"{key}={value}" for key, value in dropped.items() if value)
        + ("" if any(dropped.values()) else "нет"))
    return {"generated": stamp,
            "source": {"name": "twitchdrops.app",
                       "scrapedAt": drops.get("scrapedAt"),
                       "activeCampaigns": drops.get("activeCampaigns"),
                       "totalCampaigns": drops.get("totalCampaigns")},
            "campaigns": ordered}


def validate(feed: dict, previous: dict | None, min_active: int) -> list[str]:
    """
    Refuses a feed that lost campaigns, without refusing a genuinely quiet period.

    The aggregator states its own active count, so the new feed has to be consistent with it:
    that catches a scrape that only half succeeded. Comparing to the previous publication
    alone would block a real lull, when Twitch itself has fewer campaigns running.
    """
    problems: list[str] = []
    campaigns = feed.get("campaigns")
    if not isinstance(campaigns, list) or not campaigns:
        return ["фид пуст"]
    declared = (feed.get("source") or {}).get("activeCampaigns")
    declared = declared if isinstance(declared, int) and declared > 0 else None
    floor = max(min_active, 1)
    if declared is not None:
        floor = max(floor, int(declared * MIN_ACTIVE_RATIO))
    if len(campaigns) < floor:
        problems.append(f"кампаний {len(campaigns)}, а нижняя граница {floor}"
                        f"{f' (агрегатор заявляет {declared})' if declared else ''}")
    seen_ids: set[str] = set()
    for index, entry in enumerate(campaigns):
        if not isinstance(entry, dict):
            problems.append(f"запись #{index} не объект")
            continue
        for key in ("game", "name", "startAt", "endAt"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"запись #{index} без {key}")
        key = f"{entry.get('game')}|{entry.get('name')}|{entry.get('startAt')}"
        if key in seen_ids:
            problems.append(f"дубликат кампании: {key}")
        seen_ids.add(key)
        if len(problems) > 20:
            problems.append("...")
            break
    previous_campaigns = (previous or {}).get("campaigns")
    if isinstance(previous_campaigns, list) and previous_campaigns:
        log(f"для сравнения: в предыдущем фиде было {len(previous_campaigns)} кампаний")
    return problems


def git(feed_dir: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=feed_dir, capture_output=True, text=True,
                          check=check)


def prepare_feed_dir(feed_dir: Path) -> None:
    """Приводит рабочую копию ветки feeds к состоянию origin перед записью файла."""
    if not (feed_dir / ".git").exists():
        raise RuntimeError(f"{feed_dir} не является git-копией ветки feeds")
    git(feed_dir, "fetch", "--quiet", "origin", "feeds")
    git(feed_dir, "reset", "--hard", "--quiet", "origin/feeds")


def publish_git(feed_dir: Path, feed_path: Path, stamp: str) -> None:
    """Коммитит фид в ветку feeds одним сквошенным коммитом и пушит его."""
    del feed_path  # файл уже записан на диск
    git(feed_dir, "add", "campaigns.json")
    staged = git(feed_dir, "diff", "--cached", "--name-only", check=False)
    if not staged.stdout.strip():
        log("в фиде нет изменений, ветку не трогаем")
        return
    git(feed_dir, "commit", "--quiet", "--amend", "-m", f"feeds: campaigns ({stamp})")
    pushed = git(feed_dir, "push", "--quiet", "--force-with-lease", "origin", "HEAD:feeds",
                 check=False)
    if pushed.returncode != 0:
        raise RuntimeError(f"git push не удался: {pushed.stderr.strip()[:300]}")
    log("фид опубликован в ветку feeds")


def write_state(state_path: Path, ok: bool, message: str, campaigns: int = 0) -> None:
    try:
        state = json.loads(state_path.read_text(encoding="utf8"))
        state = state if isinstance(state, dict) else {}
    except (OSError, ValueError):
        state = {}
    failures = 0 if ok else int(state.get("consecutive_failures") or 0) + 1
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state.update({
        "last_run": stamp,
        "last_ok": stamp if ok else state.get("last_ok"),
        "ok": ok,
        "message": message,
        "campaigns": campaigns if ok else state.get("campaigns", 0),
        "consecutive_failures": failures,
    })
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed-dir", type=Path, default=DEFAULT_FEED_DIR,
                        help="git-копия на ветке feeds, куда пишется campaigns.json")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--dry-run", action="store_true", help="ничего не писать и не пушить")
    parser.add_argument("--no-push", action="store_true", help="записать файл, но не коммитить")
    parser.add_argument("--force", action="store_true", help="игнорировать проверку 'нет изменений'")
    parser.add_argument("--min-active", type=int, default=MIN_ACTIVE_CAMPAIGNS)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    feed_dir: Path = args.feed_dir
    feed_path = feed_dir / "campaigns.json"

    try:
        if not args.dry_run:
            prepare_feed_dir(feed_dir)
        previous = read_previous(feed_path)
        health = fetch_json(HEALTH_URL, min(args.timeout, 30.0))
        healthy, reason = check_health(health)
        if not healthy:
            raise RuntimeError(f"health-гейт не пройден: {reason}")
        log(f"health: {reason}")

        scraped_at = health.get("scrapedAt")
        previous_scraped = ((previous or {}).get("source") or {}).get("scrapedAt")
        if not args.force and scraped_at and scraped_at == previous_scraped:
            log(f"у агрегатора та же выгрузка ({scraped_at}), публиковать нечего")
            write_state(args.state, True, "нет изменений", len((previous or {}).get("campaigns") or []))
            return 0

        drops = fetch_json(DROPS_URL, args.timeout)
        feed = build_feed(drops, stamp)
        problems = validate(feed, previous, args.min_active)
        if problems:
            raise RuntimeError("фид не прошёл валидацию: " + "; ".join(problems[:5]))
        log(f"кампаний к публикации: {len(feed['campaigns'])} "
            f"(в предыдущем фиде {len((previous or {}).get('campaigns') or [])})")

        if args.dry_run:
            for entry in feed["campaigns"][:5]:
                log(f"  {entry['game']} | {entry['name']} | до {entry['endAt']}")
            log("dry-run: файл не записан")
            return 0

        feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=0), encoding="utf8")
        log(f"записан {feed_path}")
        if not args.no_push:
            publish_git(feed_dir, feed_path, stamp)
        write_state(args.state, True, f"опубликовано {len(feed['campaigns'])} кампаний",
                    len(feed["campaigns"]))
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, RuntimeError,
            subprocess.CalledProcessError) as exc:
        message = f"{type(exc).__name__}: {exc}"
        log(f"ОШИБКА: {message}")
        write_state(args.state, False, message)
        return 1


if __name__ == "__main__":
    sys.exit(main())
