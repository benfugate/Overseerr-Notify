# Overseerr Notification Tool

This Python script is designed to check for pending requests and open issues in an Overseerr instance and notify Discord about them.

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
  benfugate/overseerr-notify
```

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
  "DOCKER": true/false
}
```

3. Run the script using the following command:
```commandline
python3 overseerr_notify.py
```

## Command-line Arguments
- `--skip-health-check`: Skips the pre-run health check.
- `--overseerr-host`: Overseerr host URL.
- `--overseerr-token`: Overseerr API token.
- `--discord-webhook`: Discord webhook URL.
- `--num-requests`: Number of Overseerr requests to look through.
- `--ignore-hours`: Number of hours old a request must be before triggering a notification

## Functionality
- The script retrieves pending requests and open issues from Overseerr and constructs a message
- It sends the messages to a specified Discord webhook