from __future__ import annotations

from typing import Any, TypedDict, TYPE_CHECKING

from yarl import URL

from utils import json_load, json_save
from constants import SETTINGS_PATH, DEFAULT_LANG, DEFAULT_CLIENT_TYPE, PriorityMode

if TYPE_CHECKING:
    from main import ParsedArgs


class SettingsFile(TypedDict):
    proxy: URL
    language: str
    dark_mode: bool
    exclude: set[str]
    priority: list[str]
    autostart_tray: bool
    connection_quality: int
    tray_notifications: bool
    enable_badges_emotes: bool
    available_drops_check: bool
    priority_mode: PriorityMode
    client_type: str
    campaign_discovery: bool
    scan_drops: bool
    scan_interval_hours: int
    scan_top_games: int
    channel_campaigns: str
    channel_campaigns_limit: int
    auto_add_scanned_games: bool


default_settings: SettingsFile = {
    "proxy": URL(),
    "priority": [],
    "exclude": set(),
    "dark_mode": False,
    "autostart_tray": False,
    "connection_quality": 1,
    "language": DEFAULT_LANG,
    "tray_notifications": True,
    "enable_badges_emotes": False,
    "available_drops_check": True,
    "priority_mode": PriorityMode.PRIORITY_ONLY,
    "client_type": DEFAULT_CLIENT_TYPE,
    "campaign_discovery": True,
    # how the games that have drops are found (Twitch stopped listing campaigns at all)
    "scan_drops": True,
    "scan_interval_hours": 6,
    "scan_top_games": 120,
    # "off" | "relevant" (channels of the games in the priority list and of the games
    # already being mined) | "all" (every watch-based channel campaign found)
    # NOTE: off by default - every channel campaign seen so far is a subscriber reward
    # campaign (isRewardCampaign), and Twitch does not credit watch minutes for those
    # unless the account is subscribed to the channel. Turn on to try, if subscribed.
    "channel_campaigns": "off",
    "channel_campaigns_limit": 50,
    "auto_add_scanned_games": False,
}


class Settings:
    # from args
    log: bool
    tray: bool
    dump: bool
    # args properties
    debug_ws: int
    debug_gql: int
    logging_level: int
    # from settings file
    proxy: URL
    language: str
    dark_mode: bool
    exclude: set[str]
    priority: list[str]
    autostart_tray: bool
    connection_quality: int
    tray_notifications: bool
    enable_badges_emotes: bool
    available_drops_check: bool
    priority_mode: PriorityMode
    client_type: str
    campaign_discovery: bool
    scan_drops: bool
    scan_interval_hours: int
    scan_top_games: int
    channel_campaigns: str
    channel_campaigns_limit: int
    auto_add_scanned_games: bool

    PASSTHROUGH = ("_settings", "_args", "_altered")

    def __init__(self, args: ParsedArgs):
        self._settings: SettingsFile = json_load(SETTINGS_PATH, default_settings)
        self._args: ParsedArgs = args
        self._altered: bool = False

    # default logic of reading settings is to check args first, then the settings file
    def __getattr__(self, name: str, /) -> Any:
        if name in self.PASSTHROUGH:
            # passthrough
            return getattr(super(), name)
        elif hasattr(self._args, name):
            return getattr(self._args, name)
        elif name in self._settings:
            return self._settings[name]  # type: ignore[literal-required]
        return getattr(super(), name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        if name in self.PASSTHROUGH:
            # passthrough
            return super().__setattr__(name, value)
        elif name in self._settings:
            self._settings[name] = value  # type: ignore[literal-required]
            self._altered = True
            return
        raise TypeError(f"{name} is missing a custom setter")

    def __delattr__(self, name: str, /) -> None:
        raise RuntimeError("settings can't be deleted")

    def alter(self) -> None:
        self._altered = True

    def save(self, *, force: bool = False) -> None:
        if self._altered or force:
            json_save(SETTINGS_PATH, self._settings, sort=True)
