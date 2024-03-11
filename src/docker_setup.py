import os
import json

with open('/usr/src/app/src/config.json') as f:
    config = json.load(f)

config["DOCKER"] = True
config["overseerr_host"] = os.environ.get("overseerr_host")
config["overseerr_token"] = os.environ.get("overseerr_token")
config["discord_webhook"] = os.environ.get("discord_webhook")
config["num_requests"] = int(os.environ.get("num_requests")) if os.environ.get("num_requests") else config["num_requests"]

with open('/usr/src/app/src/config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=4)
