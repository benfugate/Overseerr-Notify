# Overseerr Notification Tool

This Python script is designed to check for pending requests and open issues in an Overseerr instance and notify Discord about them. It also includes a companion script that checks for pending [Shelfmark](https://github.com/calibrain/shelfmark) book/audiobook requests.

<center>
<img src="https://github.com/benfugate/Overseerr-Notify/blob/main/.github/resources/sample.png?raw=true" width="448" height="303">
</center>

## Prerequisites

- Python 3.x
- Requests library (`pip install -r requirements.txt`)

## Usage

### Docker

```shell
docker run
  -e overseerr_host=<OVERSEERR_HOST>
  -e overseerr_token=<OVERSEERR_API_TOKEN>
  -e num_requests=<NUM_REQUESTS>
  -e discord_webhook=<DISCORD_WEBHOOK>
  -e ignore_hours=<NUM_IGNORE_HOURS>
  -v /path/to/shelfmark/appdata:/data/shelfmark:ro
  -e shelfmark_webhook=<SHELFMARK_DISCORD_WEBHOOK>
  -e shelfmark_host=<SHELFMARK_HOST>
  benfugate/overseerr-notify
```

#### Shelfmark integration

Shelfmark has no API token auth (session-cookie only), so this tool instead reads Shelfmark's
sqlite database directly and **read-only**. Mount Shelfmark's whole appdata directory
(not just `users.db`) so the WAL sidecar files (`users.db-wal`, `users.db-shm`) are visible
alongside it — this is required for a consistent read while Shelfmark is running:

```shell
-v /mnt/user/appdata/shelfmark:/data/shelfmark:ro
```

- `shelfmark_webhook` is optional. If unset, Shelfmark notifications fall back to `discord_webhook`.
- `shelfmark_host` is optional and only used to build links back to the Shelfmark UI in notifications.
- `shelfmark_db` defaults to `/data/shelfmark/users.db` and normally doesn't need to be set.

### Python

1. Clone the repository or download the `overseerr_notify.py` file.
2. Create a `config.json` file with the following structure:

```json
{
  "overseerr_host": "YOUR_OVERSEERR_HOST_URL",
  "overseerr_token": "YOUR_OVERSEERR_API_TOKEN",
  "discord_webhook": "YOUR_DISCORD_WEBHOOK_URL",
  "ignore_hours": "REQUEST_AGE_BEFORE_NOTIFY",
  "num_requests": "NUMBER_OF_REQUESTS_TO_LOOK_THROUGH",
  "shelfmark_db": "PATH_TO_SHELFMARK_USERS_DB",
  "shelfmark_webhook": "SHELFMARK_DISCORD_WEBHOOK_URL",
  "shelfmark_host": "SHELFMARK_HOST_URL",
  "DOCKER": true/false
}
```

3. Run the scripts using the following commands:
```commandline
python3 overseerr_notify.py
python3 shelfmark_notify.py
```

## Command-line Arguments

### overseerr_notify.py
- `--skip-health-check`: Skips the pre-run health check.
- `--overseerr-host`: Overseerr host URL.
- `--overseerr-token`: Overseerr API token.
- `--discord-webhook`: Discord webhook URL.
- `--num-requests`: Number of Overseerr requests to look through.
- `--ignore-hours`: Number of hours old a request must be before triggering a notification

### shelfmark_notify.py
- `--skip-health-check`: Skips the pre-run health check.
- `--shelfmark-db`: Path to Shelfmark's `users.db` sqlite database (read-only).
- `--shelfmark-webhook`: Discord webhook for Shelfmark notifications. Falls back to `--discord-webhook` if unset.
- `--discord-webhook`: Fallback Discord webhook, shared with `overseerr_notify.py`.
- `--shelfmark-host`: Shelfmark host URL, used to build links in notifications.
- `--ignore-hours`: Number of hours old a request must be before triggering a notification

## Functionality
- `overseerr_notify.py` retrieves pending requests and open issues from Overseerr and constructs a message, then sends it to a specified Discord webhook
- `shelfmark_notify.py` reads pending requests directly from Shelfmark's sqlite database (read-only) and sends a similar notification to Discord