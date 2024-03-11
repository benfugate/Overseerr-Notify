# Overseerr Notification Tool

This Python script is designed to check for pending requests in an Overseerr instance and notify Discord about them.

## Prerequisites

- Python 3.x
- Requests library (`pip install -r requirements.txt`)

## Usage

1. Clone the repository or download the `overseerr_notify.py` file.
2. Create a `config.json` file with the following structure:

```json
{
  "overseerr_host": "YOUR_OVERSEERR_HOST_URL",
  "overseerr_token": "YOUR_OVERSEERR_API_TOKEN",
  "discord_webhook": "YOUR_DISCORD_WEBHOOK_URL",
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

## Functionality
- The script retrieves pending requests from Overseerr and constructs a message.
- It sends the message to a specified Discord webhook.