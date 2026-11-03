# OTCBot --- JDE Migration Specification

**Status:** Initial specification based on the supplied OTCBot source\
**Target:** A new OTCBot version built on JarDiscordEngine (JDE)\
**Compatibility requirement:** The new version must behave the same for
end users unless a change is explicitly approved.

## 1. Purpose

Rebuild OTCBot using JDE instead of organizing the application directly
around Pycord's `discord.Bot` and Cogs. This is primarily an
architectural migration, not a feature redesign. Preserve existing
commands, authorization rules, response wording and visibility,
Discord-side effects, airport workflows, logging expectations, and
console behavior.

Use verified JDE APIs. The document describes required behavior and
target architecture; it does not assume that an unverified JDE API
exists. If JDE lacks a required capability, document the gap and
implement a small, explicit adapter or add the needed framework
capability.

## 2. Goals and non-goals

### Goals

-   Preserve functional parity with the existing bot.
-   Use JDE for supported bot lifecycle, command registration, events,
    entities, extensions, and other framework facilities.
-   Keep application business logic separate from framework integration.
-   Preserve permissions, logging, configuration, airport channel
    management, status embeds, and graceful shutdown.
-   Keep services testable and configuration/secrets centralized.

### Non-goals

Unless explicitly approved, do not rename commands, change permission
requirements, rewrite user-facing text, add features, replace the
logger, add a database, change airport naming, or implement automatic
inactive-channel cleanup. The supplied code defines inactive-channel
interval constants but does not implement automatic cleanup. It also
defines ticket-related constants but contains no ticket workflow in the
supplied source.

## 3. Current feature inventory

### Runtime and lifecycle

The current entry point creates the bot with `create_bot()`, starts it
with `BOT_TOKEN`, waits for readiness, and only then starts a daemon
console-input thread. It supports graceful shutdown through `exit`,
handles keyboard interruption and Discord login failure, cancels/awaits
tasks, and closes the logger with a success/failure result.

The JDE version must preserve equivalent behavior. Readiness and
registration must be idempotent so reconnects do not duplicate command
registrations, console threads, listeners, or status messages.

### Configuration

Configuration is loaded from environment variables using
`python-dotenv`. Current variables include:

-   `OTC_BOT_TOKEN`
-   `OTC_SERVER_ID`, `TEST_SERVER_ID`
-   `OWNER_ROLE_ID`, `CO_OWNER_ROLE_ID`, `EXEC_ADMIN_ROLE_ID`,
    `ADMIN_ROLE_ID`, `EXEC_MOD_ROLE_ID`, `MOD_ROLE_ID`,
    `ENGINEER_ROLE_ID`
-   `OWNER_USER_ID`
-   `TICKET_CATEGORY_ID`, `TICKET_CHANNEL_ID`
-   `ANNOUNCEMENT_CHANNEL_ID`, `AIRPORT_STATUS_CHANNEL_ID`

Keep IDs centralized. Fail clearly on missing/invalid required
configuration. Never commit or log the bot token.

### Existing slash commands

  -----------------------------------------------------------------------
  Command                             Current behavior and constraints
  ----------------------------------- -----------------------------------
  `/ping`                             Defers, measures initial response
                                      time with a performance clock, and
                                      returns an embed titled `Pong!`
                                      with gateway latency and initial
                                      response time in milliseconds to
                                      one decimal place. No additional
                                      application-level restriction is
                                      shown.

  `/help`                             Sends an ephemeral embed listing
                                      visible slash commands and
                                      descriptions, omitting commands
                                      marked hidden when that property is
                                      available. Missing descriptions use
                                      `No description available.`

  `/purge amount`                     Guild-only. `amount` is an integer
                                      from 1 to 100. The user needs
                                      Manage Messages; the bot needs
                                      Manage Messages and Read Message
                                      History in the channel. Defers
                                      ephemerally, purges messages, logs
                                      each deleted message's author, IDs,
                                      timestamp, and content/fallback
                                      marker, then reports the count
                                      ephemerally. Handles permission/API
                                      failures.

  `/logs`                             Guild-only. Requires a configured
                                      moderator or engineer role. Finds
                                      the latest `.jar-log`, formats a
                                      bounded excerpt, escapes triple
                                      backticks, and sends it
                                      ephemerally. Reports when no log
                                      exists and logs read failures.

  `/log-flush`                        Guild-only. Requires a configured
                                      moderator or engineer role. Flushes
                                      buffered logs, logs the
                                      request/result, and responds
                                      ephemerally.

  `/bot-maint [message]`              Engineer-only, guild-only
                                      announcement for scheduled
                                      maintenance.

  `/bot-up [message]`                 Engineer-only, guild-only
                                      announcement that the bot is
                                      operational.

  `/bot-down [message]`               Engineer-only, guild-only
                                      announcement that the bot is going
                                      offline.

  `/bot-issue [message]`              Engineer-only, guild-only
                                      announcement of a bot issue.

  `/bot-update [message]`             Engineer-only, guild-only
                                      announcement of an update.

  `/bot-test [message]`               Engineer-only, guild-only test
                                      announcement.

  `/open airport_code position`       Guild-only; bot needs Manage
                                      Channels. Validates a four-letter
                                      airport code and a managed position
                                      or `ALL`; creates or reuses a
                                      category and requested voice
                                      channels; refreshes airport status.

  `/close airport_code [force]`       Guild-only; bot needs Manage
                                      Channels. Without force, refuses
                                      closure if any voice channel in the
                                      airport category is occupied.
                                      `force=True` additionally requires
                                      a configured moderator role.
                                      Deletes only managed voice channels
                                      and deletes the category only when
                                      empty. Refreshes status after
                                      successful changes.
  -----------------------------------------------------------------------

### Announcement behavior

All six announcement commands use the same helper. The user must have a
configured engineer role. The optional message is limited to 1,500
characters and is stripped before use. The configured announcement
channel must exist and be a text channel. The embed uses the exact
title, description, funny message, and color in `ANNOUNCEMENTS`; it may
include an "Additional Information" field, always includes an "OTCBot
says" field, uses the bot avatar for author/thumbnail when available,
includes a requester footer and avatar, has a UTC timestamp, and is sent
with mentions disabled. The command responds ephemerally and logs
success/failures.

Preserve the existing announcement strings and colors exactly; copy them
from the source rather than rephrasing them.

### Greeting reaction

The `General` Cog listens for messages. It ignores bot authors and empty
content. It reacts with `👋` if the message contains one of `hi`,
`hello`, `hey`, `hiya`, `heya`, `howdy`, `hallo`, or `bonjour`,
case-insensitively and as a whole word. Permission and HTTP failures are
logged without crashing the bot.

### Airport service

Airport codes are stripped, uppercased, and must match exactly four
ASCII letters. Category names use `AIRPORT_CATEGORY_NAME_FORMAT`
(currently `{airport_code}`); voice channel names use
`AIRPORT_VOICE_CHANNEL_NAME_FORMAT` (currently
`{airport_code} - {position}`). Managed positions are `GND`, `TWR`,
`DEP`, `APP`, and `CTR`.

`/open` reuses matching categories/channels and creates missing ones.
`ALL` means all five managed positions. `/close` only deletes voice
channels whose names match the managed naming scheme for that airport. A
category is deleted only if it has no channels remaining. Without force,
closure is blocked if any voice channel in the category has members.
Forced closure requires a moderator. Keep this service separate from
command handlers and make pure validation/formatting logic
unit-testable.

### Airport status embed

On readiness, the bot attempts to refresh airport status in each
connected guild. It locates/fetches the configured status channel and
requires a text channel. It includes valid airport categories sorted
alphabetically, lists voice-channel mentions or `_No voice channels._`,
uses title `Airport Voice Status` and footer `OTCBot Airport Status v1`,
and respects a 4,000-character description limit with an omission
notice. It edits an existing status embed where possible, creates one
only when absent, and removes duplicate status embeds and recognized
legacy messages beginning `**Airport status:`. Avoid duplicate messages
on reconnect.

### Logging

The existing adapter uses `jarbin_toolkit_log`. It exposes DEBUG, INFO,
NOTICE, WARNING, ERROR, CRITICAL, and exception helpers. Logs live under
`logs/`, use `otcbot_<UTC date>` naming and `.jar-log` format, and
include `application: OTCBot` metadata. A background thread flushes
periodically (60 seconds by default), rotates at UTC midnight, and
removes logs older than seven days. `/logs`, `/log-flush`, and console
commands depend on this behavior.

Retain this logger behind the current wrapper API unless a JDE
integration provides a compatible replacement and the change is
approved. Keep flush/rotation/shutdown synchronized and do not silently
hide operational failures where a safe fallback is possible.

### Local console

After readiness, support: - `help`: display available console
commands. - `logs`: print the latest log. - `log-flush`: flush buffered
logs. - `exit`: request graceful shutdown.

Input must not block the async event loop. EOF/input errors should end
the input loop cleanly.

## 4. Authorization matrix

  -----------------------------------------------------------------------
  Feature                             Required authorization
  ----------------------------------- -----------------------------------
  `/ping`, `/help`                    No additional application-level
                                      restriction shown

  Greeting reaction                   Ignore bot-authored messages

  `/purge`                            User has Manage Messages; bot has
                                      Manage Messages and Read Message
                                      History

  `/logs`, `/log-flush`               Configured moderator **or**
                                      engineer role

  Announcement commands               Configured engineer role

  `/open`                             Bot has Manage Channels

  `/close` without force              Bot has Manage Channels; all voice
                                      channels in the airport category
                                      must be empty

  `/close force=True`                 Bot has Manage Channels; invoking
                                      member has a configured moderator
                                      role
  -----------------------------------------------------------------------

Do not treat moderator and engineer roles as interchangeable. A
moderator may force-close an airport and use log commands, but does not
gain announcement permission unless also assigned an engineer role.
Enforce permissions in handlers/services, not just in `/help`.

## 5. Target JDE architecture

Confirm the installed JDE version and inspect its actual API before
implementing. The intended separation is:

-   **Entry point:** configuration, bot construction, startup, readiness
    wait, console startup, shutdown coordination, final logger closure
    and process result.
-   **Bot composition/lifecycle:** create the JDE bot, register
    features, handle lifecycle events, ensure command
    registration/synchronization is idempotent.
-   **Command handlers:** validate context/permissions, call services,
    map results to equivalent responses, and log events.
-   **Services:** airport channel lifecycle, airport status,
    announcement building/sending, and logging adapter.
-   **JDE adapter boundary:** isolate any required low-level
    Pycord/Discord access when JDE lacks a suitable high-level
    abstraction.

Use JDE extensions/modules if that is its supported pattern. Do not copy
Pycord Cogs mechanically unless JDE explicitly supports that model.

Before porting, verify JDE support for: - Slash command registration and
synchronization. - Required/optional arguments, defaults, choices,
min/max values, and string length limits. - Guild-only commands and
ephemeral responses. - Deferral, follow-up responses, and response-state
checks. - Guild/member/role/channel lookup and fetch. - Permission
checks and voice-channel occupancy. - Message history, purge, deletion,
and reactions. - Text/category/voice channel creation and deletion. -
Embed creation, sending, and editing. - Event listeners and lifecycle
callbacks. - Application-command error handling. - Command registry
access for `/help`. - Extension loading and reconnect-safe registration.

Record each unsupported capability as a framework gap and resolve it
explicitly. Do not invent API names or assume a method exists without
verifying the installed JDE version.

## 6. Functional requirements

### FR-01 --- Startup and readiness

-   Load and validate configuration.
-   Authenticate with `OTC_BOT_TOKEN`.
-   Start the console only after readiness.
-   Initialize airport status as the current version does.
-   Ensure reconnects do not duplicate registrations, listeners, console
    threads, or status messages.
-   A status failure for one guild must be logged without unnecessarily
    disabling the bot.

### FR-02 --- Shutdown

-   Console `exit` requests async shutdown safely from the input thread.
-   Keyboard interruption is treated as a user-requested shutdown.
-   Cancel and await pending tasks appropriately, then close the Discord
    client.
-   Close the logger exactly once.
-   Normal shutdown returns a success result; fatal unexpected failures
    return failure.
-   Do not misreport normal task cancellation as an unexpected error.

### FR-03 --- `/ping`

Preserve the command name/description, `Pong!` green embed, gateway
latency and initial response time in milliseconds to one decimal place,
and lack of extra role restrictions.

### FR-04 --- `/help`

List visible registered slash commands and descriptions in an ephemeral
embed. Use `No description available.` when needed. Build the list from
JDE's authoritative command registry.

### FR-05 --- `/purge`

Preserve integer bounds 1--100, guild-only behavior, all user/bot
permission checks, ephemeral deferral and final response,
deleted-message logging, and permission/API failure handling.

### FR-06 --- `/logs`

Preserve role checks, latest-log selection, no-log response, ephemeral
visibility, and bounded excerpt settings: 20 head lines, 20 tail lines,
1,800 total characters, and 250 characters per line. Escape triple
backticks before sending.

### FR-07 --- `/log-flush`

Preserve guild and role checks, flush operation, logging, ephemeral
response, and failure handling.

### FR-08 --- Announcements

Register all six commands with optional `message` up to 1,500
characters. Preserve guild/engineer checks, exact configured content and
colors, embed fields/author/thumbnail/footer/timestamp, mention
suppression, logs, and ephemeral confirmations/errors.

### FR-09 --- Greeting listener

Preserve ignored authors/empty content, case-insensitive whole-word
matching, configured greeting list, `👋` reaction, and logged
permission/API failures.

### FR-10 --- `/open`

Preserve guild and Manage Channels checks; four-letter code validation;
position validation; `ALL`; category/channel reuse; creation of missing
resources; result message; logging; status refresh; and ephemeral
interaction behavior. Validate before making changes wherever possible.

### FR-11 --- `/close`

Preserve guild and Manage Channels checks; airport validation;
missing-category response; occupied-channel protection; moderator
requirement for `force=True`; deletion of only managed channels;
deletion of only empty categories; count/category result; status
refresh; logs and error handling. Check force authorization before
destructive actions.

### FR-12 --- Airport status

Preserve channel validation, category filtering/sorting, voice-channel
listing, empty-airport message, title/footer, 4,000-character
description limit, omission notice, edit-before-create behavior,
duplicate cleanup, and recognized legacy-message cleanup. Do not delete
unrelated messages.

### FR-13 --- Console

Preserve `help`, `logs`, `log-flush`, and `exit`; run input outside the
async event loop; start after readiness; and make shutdown idempotent.

### FR-14 --- Logging

Preserve log levels, `.jar-log` format, directory/naming/metadata, UTC
daily rotation, periodic flushing, seven-day retention, traceback
logging, and the logger wrapper API.

## 7. Error-handling requirements

-   Handle expected Discord permission and HTTP errors near the
    operation that can raise them.
-   Log unexpected exceptions with traceback information.
-   Keep stack traces, tokens, environment values, and secrets out of
    user-facing responses.
-   Ensure interactions receive a valid initial or follow-up response.
-   Keep one guild's status failure from unnecessarily preventing other
    startup work.
-   Do not register commands/listeners more than once after reconnect.
-   Validate authorization and destructive-operation constraints before
    changes.
-   Do not silently claim a channel operation failed merely because the
    subsequent status refresh failed; report the status refresh problem
    separately.

## 8. Testing and acceptance criteria

### Lifecycle/configuration

-   [ ] Valid configuration starts the bot.
-   [ ] Missing/invalid configuration fails clearly.
-   [ ] Readiness is detected and console starts only afterward.
-   [ ] All four console commands work.
-   [ ] `exit` and keyboard interruption shut down cleanly.
-   [ ] Logger closes once with the correct run result.
-   [ ] Reconnects do not duplicate registrations, threads, listeners,
    or status embeds.

### Commands and permissions

-   [ ] `/ping` matches the existing latency response.
-   [ ] `/help` lists visible commands ephemerally.
-   [ ] `/purge` enforces bounds, guild context, user permission, and
    bot permissions; deletes/logs/reports correctly.
-   [ ] `/logs` and `/log-flush` reject unauthorized users.
-   [ ] All six announcement commands reject non-engineers and preserve
    embed content.
-   [ ] `/open` rejects invalid codes/positions, reuses existing
    resources, and handles `ALL`.
-   [ ] `/close` refuses occupied airports without force and rejects
    non-moderators when forced.
-   [ ] `/close` deletes only managed channels and only deletes empty
    categories.
-   [ ] Airport status refresh follows successful open/close operations.

### Events/status/logging

-   [ ] Greeting behavior matches the existing whole-word,
    case-insensitive matching.
-   [ ] Bot messages and empty messages are ignored.
-   [ ] Reaction permission/API errors are logged without crashing.
-   [ ] Status initialization, editing, creation, sorting, size limits,
    and duplicate cleanup work.
-   [ ] Log excerpts respect all configured limits and safely escape
    code fences.
-   [ ] Logger rotation, flushing, retention, and shutdown remain
    reliable.

### Parity test

Run equivalent scenarios against the old and new versions in a test
server. Compare command options, validation, permissions, Discord-side
effects, response text, response visibility, and log behavior. Any
difference must be fixed or explicitly approved and documented.

## 9. Recommended implementation phases

1.  **JDE capability audit:** confirm version and verify all required
    API operations. Document adapters and gaps.
2.  **Application skeleton:** port configuration, lifecycle, readiness,
    shutdown, console, and logging integration.
3.  **Simple features:** implement `/ping`, `/help`, and greeting
    reaction.
4.  **Moderation/logging:** implement `/purge`, `/logs`, and
    `/log-flush`.
5.  **Announcements:** port shared announcement logic and six commands.
6.  **Airport management:** port open/close and status reconciliation.
7.  **Parity/release:** complete acceptance tests in a test server and
    document unavoidable differences.

Do not proceed past a phase until its behavior is verified.

## 10. Suggested project organization

Adapt this structure to JDE's actual extension conventions:

``` text
otc_bot/
├── __main__.py
├── core/
│   ├── bot.py                 # JDE bot composition and lifecycle
│   ├── config.py              # Environment/configuration validation
│   ├── constants.py           # IDs, roles, strings and limits
│   ├── models.py              # Immutable application models
│   └── logging.py             # Existing logging adapter/lifecycle
├── commands/
│   ├── general.py             # ping, help
│   ├── moderation.py          # purge, logs, log-flush
│   ├── announcements.py      # announcement commands
│   └── voice_channels.py     # open and close
├── events/
│   └── messages.py             # Greeting reaction
├── services/
│   ├── airport.py              # Airport resource lifecycle
│   ├── airport_status.py       # Status embed reconciliation
│   └── announcements.py       # Announcement composition/sending
└── adapters/
    └── discord_api.py          # Only if a real low-level bridge is needed
```

Follow JDE conventions if they differ. Avoid abstraction layers that do
not isolate a real compatibility boundary.

## 11. Cautions

1.  Do not assume JDE API names or signatures; verify the installed
    version.
2.  Keep command registration distinct from Discord command
    synchronization.
3.  Preserve moderator/engineer role distinctions.
4.  Preserve both user and bot permission checks for purge.
5.  Limit airport deletion to managed channels and preserve non-empty
    categories.
6.  Keep `AllowedMentions.none()` behavior for announcements.
7.  Keep logger flush/rotation/shutdown synchronized.
8.  Do not infer implemented behavior from unused constants.
9.  Never log the bot token.
10. Keep traceback details in logs, not public responses.

## 12. Decisions to confirm

-   Exact JDE version/API surface to target.
-   JDE's support for command option constraints and interaction
    response lifecycle.
-   How JDE exposes permissions, roles, channels, messages, embeds,
    reactions, and command registry.
-   Whether JDE supports extensions and reconnect-safe registration.
-   Whether low-level Pycord access is available for operations not
    abstracted by JDE.
-   Whether to retain `jarbin_toolkit_log` unchanged; this specification
    assumes yes unless approved otherwise.
-   Whether `/help` should continue listing all visible commands from
    the authoritative registry.
-   Whether ticket-related constants remain reserved; no ticket workflow
    was present in the supplied source.
-   Whether inactive-channel interval constants remain reserved; no
    automatic cleanup implementation was present in the supplied source.

## 13. Definition of done

The migration is complete when:

1.  All current commands and the greeting listener work through verified
    JDE integration.
2.  All current authorization checks are preserved.
3.  User-facing text, embeds, and visibility match the old version
    unless a difference is explicitly approved.
4.  Airport channels and status embeds behave according to the existing
    rules.
5.  Startup, reconnect, console, logging, and shutdown are reliable.
6.  The acceptance checklist passes in a test server.
7.  No secrets are committed or exposed.
8.  No unverified JDE API assumptions remain.
9.  Any unavoidable differences are documented.
10. The old version remains available until the new version passes
    parity testing.

**Final principle:** JDE should change how OTCBot is structured
internally, not what users experience when interacting with it.
