# Twitch Drops Miner

> **Unofficial fix build (fork)** - a fork of [DevilXD/TwitchDropsMiner](https://github.com/DevilXD/TwitchDropsMiner)
> carrying the fixes for the September-October 2026 Twitch API changes, which left the
> upstream `development build` unable to log in and unable to see any campaign
> (upstream issue [#1165](https://github.com/DevilXD/TwitchDropsMiner/issues/1165)).
> All credit for the application goes to DevilXD and the upstream contributors; this fork
> only carries the fixes and the packaging needed to actually run it.
> See [Fork notes](#fork-notes-what-this-build-changes) below.

**Which build to take:** the versioned releases here (e.g. `v16.1`) are complete -
Windows, macOS, Linux AppImage (x86_64/aarch64) and Linux PyInstaller (x86_64/aarch64), each
named exactly like upstream's, so a build can be unpacked over an existing installation to
update it while keeping `settings.json` and the saved login. The `dev-build` pre-release is
the rolling build of this fork's `master`, rebuilt on every push, same as upstream's.

This application allows you to AFK mine timed Twitch drops, without having to worry about switching channels when the one you were watching goes offline, claiming the drops, or even receiving the stream data itself. This helps you save on bandwidth and hassle.

### How It Works:

Every several seconds, the application pretends to watch a particular stream by fetching stream metadata - this is enough to advance the drops. Note that this completely bypasses the need to download any actual stream video and sound. To keep the status (ONLINE or OFFLINE) of the channels up-to-date, there's a websocket connection established that receives events about streams going up or down, or updates regarding the current amount of viewers.

### Features:

- Stream-less drop mining - save on bandwidth.
- Game priority and exclusion lists, allowing you to focus on mining what you want, in the order you want, and ignore what you don't want.
- Sharded websocket connection, allowing for tracking up to `199` channels at the same time.
- Automatic drop campaigns discovery based on linked accounts (requires you to do [account linking](https://www.twitch.tv/drops/campaigns) yourself though).
- Stream tags and drop campaign validation, to ensure you won't end up mining a stream that can't earn you the drop.
- Automatic channel stream switching, when the one you were currently watching goes offline, as well as when a channel streaming a higher priority game goes online.
- Login session is saved in a cookies file, so you don't need to login every time.
- Mining is automatically started as new campaigns appear, and stopped when the last available drops have been mined.

### Usage:

- Download and unzip [the latest release](https://github.com/DevilXD/TwitchDropsMiner/releases) - it's recommended to keep it in the folder it comes in.
- Run it and login/connect the miner to your Twitch account by using the in-app login form.
- After a successful login, the app should fetch a list of all available campaigns and games you can mine drops for - you can then select and add games of choice to the Priority List available on the Settings tab, and then press on the `Reload` button to start processing. It will fetch a list of all applicable streams it can watch, and start mining right away. You can also manually switch to a different channel as needed.
- If you wish to keep the miner occupied with mining anything it can, beyond what you've selected via the Priority List, you can use the Priority Mode setting to specify the mining order for the rest of the games.
- Make sure to link your Twitch account to game accounts on the [campaigns page](https://www.twitch.tv/drops/campaigns), to enable more games to be mined.

### Pictures:

![Main](https://user-images.githubusercontent.com/4180725/164298155-c0880ad7-6423-4419-8d73-f3c053730a1b.png)
![Inventory](https://user-images.githubusercontent.com/4180725/164298315-81cae0d2-24a4-4822-a056-154fd763c284.png)
![Settings](https://user-images.githubusercontent.com/4180725/164298391-b13ad40d-3881-436c-8d4c-34e2bbe33a78.png)

### Notes:

> [!WARNING]  
> Due to how Twitch handles the drop progression on their side, watching a stream in the browser (or by any other means) on the same account that is actively being used by the miner, will usually cause the miner to misbehave, reporting false progress and getting stuck mining the current drop.  
> 
> Using the same account to watch other streams during mining is thus discouraged, in order to avoid any problems arising from it.

> [!CAUTION]  
> Persistent cookies will be stored in the `cookies.jar` file, from which the authorization (login) information will be restored on each subsequent run. Make sure to keep your cookies file safe, as the authorization information it stores can give another person access to your Twitch account, even without them knowing your password!

> [!IMPORTANT]  
> Successfully logging into your Twitch account in the application may cause Twitch to send you a "New Login" notification email. This is normal - you can verify that it comes from your own IP address. The detected browser during the login will be "Chrome", as that's what the miner currently presents itself to the Twitch server.

> [!NOTE]  
> The time remaining timer always countdowns a single minute and then stops - it is then restarted only after the application redetermines the remaining time. This "redetermination" can happen at any time Twitch decides to report on the drop's progress, but not later than 20 seconds after the timer reaches zero. The seconds timer is only an approximation and does not represent nor affect actual mining speed. The time variations are due to Twitch sometimes not reporting drop progress at all, or reporting progress for the wrong drop - these cases have all been accounted for in the application though.

> [!NOTE]  
> The source code requires Python 3.10 or higher to run.

### Notes about the Windows build:

- To achieve a portable-executable format, the application is packaged with PyInstaller into an `EXE`. Some antivirus engines (including Windows Defender) might report the packaged executable as a trojan, because PyInstaller has been used by others to package malicious Python code in the past. These reports can be safely ignored. If you absolutely do not trust the executable, you'll have to install Python yourself and run everything from source.
- The executable uses the `%TEMP%` directory for temporary runtime storage of files, that don't need to be exposed to the user (like compiled code and translation files). For persistent storage, the directory the executable resides in is used instead.
- The autostart feature is implemented as a registry entry to the current user's (`HKCU`) autostart key. It is only altered when toggling the respective option. If you relocate the app to a different directory, the autostart feature will stop working, until you toggle the option off and back on again

### Notes about the Linux build:

- The Linux app is built and distributed using two distinct portable-executable formats: [AppImage](https://appimage.org/) and [PyInstaller](https://pyinstaller.org/).
- There are no major differences between the two formats, but if you're looking for a recommendation, use the AppImage.
- The Linux app should work out of the box on any modern distribution, as long as it has `glibc>=2.35`, plus a working display server.
- Every feature of the app is expected to work on Linux just as well as it does on Windows. If you find something that's broken, please [open a new issue](https://github.com/DevilXD/TwitchDropsMiner/issues/new).
- The size of the Linux app is significantly larger than the Windows app due to the inclusion of the `gtk3` library (and its dependencies), which is required for proper system tray/notifications support.
- As an alternative to the native Linux app, you can run the Windows app via [Wine](https://www.winehq.org/) instead. It works really well!

### Notes about the macOS build:

- The macOS version is packaged using PyInstaller into a standalone `.app` bundle, distributed as a ZIP archive.
- Since this application is not signed with a paid Apple Developer Certificate, **macOS Gatekeeper will block it** on the first run (saying it "The application is damaged and can't be opened").
  - **To fix this**: Either open the Terminal in the folder the app is in (or navigating with `cd path/to/folder`) and enter `xattr -cr Twitch Drops Miner (by DevilXD).app` or just type `xattr -cr ` (make sure to put a space at the end), drag and drop the `Twitch Drops Miner (by DevilXD).app` file into the terminal window (this will auto-fill the path) and enter
- Persistent files (like `cookies.jar`, `settings.json`, `lock.file` and the `cache` folder) are stored inside the application bundle in `Twitch Drops Miner (by DevilXD).app/Contents/MacOS` (to access them Right-click the application and select `Show Package Contents`)

### Advanced Usage:

If you'd be interested in running the latest master from source or building your own executable, see the wiki page explaining how to do so: https://github.com/DevilXD/TwitchDropsMiner/wiki/Setting-up-the-environment,-building-and-running

### Support

If you'd encounter any issues with the miner:

- Please see the [troubleshooting page](https://github.com/DevilXD/TwitchDropsMiner/wiki/Troubleshooting) for some common issues and their explanation.  
- Please [search the issues page](https://github.com/DevilXD/TwitchDropsMiner/issues?q=sort%3Aupdated-desc%20is%3Aissue) to see if your issue hasn't been reported yet.  
- If it's not been reported yet, feel free to open a new issue, describing your problem.

If you like the application and found it useful, please consider donating a small amount of money to support me. Thank you!

<div align="center">

[![Buy me a coffee](https://i.imgur.com/cL95gzE.png)](
    https://www.buymeacoffee.com/DevilXD
)
[![Support me on Patreon](https://i.imgur.com/Mdkb9jq.png)](
    https://www.patreon.com/bePatron?u=26937862
)

</div>

### Project goals:

Twitch Drops Miner (TDM for short) has been designed with a couple of simple goals in mind. These are, specifically:

- Twitch Drops oriented - it's in the name. That's what I made it for.
- Easy to use for an average person. Includes a nice looking GUI and is packaged as a ready-to-go executable, without requiring an existing Python installation to work.
- Intended as a helper tool that starts together with your PC, runs in the background through out the day, and then closes together with your PC shutting down at the end of the day. If it can run continuously for 24 hours at minimum, and not run into any errors, I'd call that good enough already.
- Requiring a minimum amount of attention during operation - check it once or twice through out the day to see if everything's fine with it.
- Underlying service friendly - the amount of interactions done with the Twitch site is kept to the minimum required for reliable operation, at a level achievable by a diligent site user.

TDM is not intended for/as:

- Mining channel points - again, it's about the drops: only.
- Mining anything else besides Twitch drops - no, I won't be adding support for a random 3rd party site that also happens to rely on watching Twitch streams.
- Unattended operation: worst case scenario, it'll stop working and you'll hopefully notice that at some point. Hopefully.
- 100% uptime application, due to the underlying nature of it, expect fatal errors to happen every so often.
- Being hosted on a remote server as a 24/7 miner.
- Being used with more than one managed account.
- Mining campaigns the managed account isn't linked to.

This means that features such as:

- It being possible to run it without a GUI, or with only a console attached.
- Any form of automatic restart when an error happens.
- Docker or any other form of remote deployment.
- Using it with more than one managed account.
- Making it possible to mine campaigns that the managed account isn't linked to.
- Anything that increases the site processing load caused by the application.
- Any form of additional notifications system (email, webhook, etc.), beyond what's already implemented.

..., are most likely not going to be a feature, ever. You're welcome to search through the existing issues to comment on your point of view on the relevant matters, where applicable. Otherwise, most of the new issues that go against these goals will be closed and the user will be pointed to this paragraph.

For more context about these goals, please check out these issues: [#161](https://github.com/DevilXD/TwitchDropsMiner/issues/161), [#105](https://github.com/DevilXD/TwitchDropsMiner/issues/105), [#84](https://github.com/DevilXD/TwitchDropsMiner/issues/84)

### Credits:

<!---
Note: The translations credits are sorted alphabetically, based on their English language name.
When adding a new entry, please ensure to insert it in the correct place in the second section.
Non-translations related credits should be added to the first section instead.

Note: When adding a new credits line below, please add two trailing spaces at the end
of the previous line, if they aren't already there. Doing so ensures proper markdown
rendering on Github. In short: Each credits line should end with two trailing spaces,
placed past the period character at the end.

• Last line can have the two trailing spaces omitted.
• Please ensure your editor won't trim the trailing spaces upon saving the file.
• Please ensure to leave a single empty new line at the end of the file.
-->

@guihkx - For the CI script, CI maintenance, and everything related to Linux builds.  
@kWAYTV - For the implementation of the dark mode theme.  
@crocchetto - For the macOS port.  

@Bamboozul - For the entirety of the Arabic (العربية) translation.  
@Suz1e - For the entirety of the Chinese (简体中文) translation and revisions.  
@wwj010, @zhangminghao1989, @Self4215 - For the Chinese (简体中文) translation corrections and revisions.  
@Ricky103403 - For the entirety of the Traditional Chinese (繁體中文) translation.  
@LusTerCsI - For the Traditional Chinese (繁體中文) translation corrections and revisions.  
@nwvh - For the entirety of the Czech (Čeština) translation.  
@Kjerne - For the entirety of the Danish (Dansk) translation.  
@lmdpocus - For the entirety of the Dutch (Nederlandse) translation.  
@Rensoraa - For the Traditional Dutch (Nederlandse) translation corrections and revisions.  
@roobini-gamer - For the entirety of the French (Français) translation.  
@Calvineries - For the French (Français) translation revisions.  
@ThisIsCyreX - For the entirety of the German (Deutsch) translation.  
@Nagyhoho1234 - For the entirety of the Hungarian (Magyar) translation.  
@Eriza-Z - For the entirety of the Indonesian translation.  
@casungo - For the entirety of the Italian (Italiano) translation.  
@ShimadaNanaki - For the entirety of the Japanese (日本語) translation.  
@biroman -  For the entirety of the Norwegian (Norsk) translation.  
@Patriot99 - For the Polish (Polski) translation and revisions (co-authored with @DevilXD).  
@zarigata - For the entirety of the Portuguese (Português) translation.  
@Sergo1217 - For the entirety of the Russian (Русский) translation.  
@kilroy98, @flamesv - For the Russian (Русский) translation corrections and revisions.  
@Shofuu - For the entirety of the Spanish (Español) translation and revisions.  
@Forero-0 - For the Spanish (Español) translation revisions.  
@alikdb - For the entirety of the Turkish (Türkçe) translation.  
@DogancanYr, @Elderly-Emre, @Hweord - For the Turkish (Türkçe) translation corrections and revisions.  
@Nollasko - For the entirety of the Ukrainian (Українська) translation and revisions.  
@kilroy98 - For the Ukrainian (Українська) translation corrections and revisions.  

## Fork notes: what this build changes

Twitch changed several things between September and October 2026, which broke the
upstream application in three separate places. This fork carries the fixes:

- **Login works again.** The device code flow stopped accepting the Android app client
  ID in September 2026 (`{"status":400,"message":"invalid client"}`), which surfaced as
  `KeyError: 'device_code'`. The client is now a setting (`client_type` in
  `settings.json`, default `SMARTBOX`) and every known client is tried in turn during
  login, with the first accepted one saved back into the settings. A future rotation of
  client IDs is a config change instead of a broken release.
- **Campaigns are found again.** `ViewerDropsDashboard` and `DropCampaignDetails` are
  now behind an integrity check and return nothing for any client the application can
  use, so the campaign list came back empty. The per-channel available drops query still
  works, so campaigns are now discovered from the live channels of the games you care
  about. Any game listed in the priority list, plus the games of campaigns already in
  progress, are searched. The queries that are gated no longer abort the whole inventory
  fetch when they fail.
- **Drop progress counts again.** Twitch stopped counting the watch payloads of
  non-browser clients in October 2026; mining now keeps the drop timer moving by
  requesting the stream's playlist chunks (upstream commit `f693b0c`).
- **Mining only happens where drops exist.** A channel can be listed as drops-enabled in
  the game directory and still have no drops available for your account, in which case
  mining it looks fine while the drop never moves. The available drops of the channels
  about to be watched are checked first, and the check fails open (if no channel reports
  any drops at all, the channels are used as before).
- The channel page is always fetched from `www.twitch.tv`, regardless of the API client
  in use.

### Getting started with this build

1. Start the application and log in at `twitch.tv/activate` with the code shown.
2. **Add the game you want to farm** to the priority list in the Settings tab (the entry
   field next to the list) - that game is what campaign discovery searches for. Games of
   campaigns you already have progress on are searched automatically.
3. Set the priority mode to `Priority only` if you want to farm nothing but those games.

If nothing shows up, the log (start with `--log -vvvv`, file `log.txt` next to the
executable) contains a `Campaign discovery:` line telling how many campaigns were found.

### Finding the games that have drops (drop scan)

Twitch stopped answering the campaigns dashboard query entirely in September 2026, so
nothing can be looked up by campaign anymore, and the game selector cannot be filled from
it either. The application therefore scans for the games that have drops available:

1. the popular games are enumerated through the Helix API (`/helix/games/top`), which
   still answers and uses the same account session;
2. every one of them is checked for live drops-enabled channels through the game
   directory;
3. each of those channels is asked what drops are available on it, and the answers are
   turned into campaigns.

The scan runs in the background (never blocking the mining), refreshes every
`scan_interval_hours` (6 by default), and its results are cached in `drops_scan.json`
next to the executable. Games it finds with drops available are listed in the priority
game selector, so they can be picked from a list instead of typed in. The scan is
configured in `settings.json`:

- `scan_drops` (default `true`) - run the scan at all;
- `scan_interval_hours` (default `6`) - how often to refresh the results;
- `scan_top_games` (default `120`) - how many popular games to check; a scan over 120
  games asks about ~500 channels and takes a minute or so;
- `auto_add_scanned_games` (default `false`) - put every scanned game into the priority
  list automatically instead of just listing them;
- `channel_campaigns` (default `"off"`) - also mine the campaigns that individual
  channels offer (badges, emotes). **Every one of those seen so far is a subscriber
  reward campaign**, and Twitch does not credit watch minutes for it unless the account is
  subscribed to that channel - so this does nothing for the usual case. Modes: `off`,
  `relevant` (channels of the games being farmed), `all` (plus the most watched
  drops-enabled channels overall, capped by `channel_campaigns_limit`);
- `available_drops_check` (default `true`) - verify that a channel actually has drops for
  the account before mining it.

An empty priority list means "mine whatever drops are available", which is the useful
default now that the game list is built automatically. Note that adding a game to the
priority list restricts mining to that game only while the priority mode is
`Priority only`.
