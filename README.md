# Drops feeds

Данные, которые Twitch Drops Miner скачивает при запуске. Ветка содержит **только данные**:
исходный код живёт в `master`, и публикация фидов сюда не может притащить в релизную ветку
недоделанные правки.

| Файл | Что внутри | Кто обновляет |
| --- | --- | --- |
| `campaigns.json` | кампании, которые идут или ещё начнутся: игра, даты, число дропов | `tools/publish_site_feed.py`, раз в час |
| `games_seed.json` | игры, для которых кампании когда-либо видели (стартовый каталог свежей установки) | `tools/publish_feeds.py`, раз в 6 часов |
| `history.json` | накопленная история кампаний, найденных собственным сканом | `tools/publish_feeds.py`, раз в 6 часов |

Приложение читает фиды по адресам:

- `https://raw.githubusercontent.com/RoninOnis/TwitchDropsMiner/feeds/campaigns.json`
- `https://raw.githubusercontent.com/RoninOnis/TwitchDropsMiner/feeds/games_seed.json`

## Откуда берутся кампании

Публичный JSON агрегатора `https://twitchdrops.app/api/drops`, который сам опрашивает Twitch
примерно раз в 13 минут. Это единственный известный источник полного списка кампаний: запрос
дашборда кампаний Twitch больше не отвечает (для веб-клиента — `IntegrityCheckFailed`, для
остальных — `null`), а страница `twitch.tv/drops/campaigns` игровых дропов не содержит вообще.

Публикатор не пишет фид, если не проходит health-гейт: данные устарели, источник `dashboard`
у агрегатора пуст или список схлопнулся больше чем вдвое. Привязка аккаунта
(`isAccountConnected`) в фиде отсутствует принципиально — это per-account данные, их умеет
определять только собственный скан на машине пользователя.

## Формат

```json
{
  "generated": "2026-10-23T07:46:44Z",
  "source": {"name": "twitchdrops.app", "scrapedAt": "...",
             "activeCampaigns": 148, "totalCampaigns": 6031},
  "campaigns": [
    {"game": "EVE Online", "gameId": "493057", "name": "Crimson Harvest Drop 4",
     "startAt": "2026-10-22T11:00:00Z", "endAt": "2026-10-23T10:57:59.999Z",
     "drops": 3, "seen": "2026-10-23T07:31:15.675Z"}
  ]
}
```

Лишние ключи (`source`, `drops`, `seen`) старые сборки просто игнорируют; обязательные для них
поля — `campaigns[].game`, `startAt`, `endAt`.
