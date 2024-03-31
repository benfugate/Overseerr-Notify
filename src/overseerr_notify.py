#!/usr/bin/env python3

import os
import json
import argparse
import requests
from datetime import datetime, timedelta, timezone


class OverseerrNotify:
    def __init__(self):
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/config.json") as f:
            defaults = json.load(f)
        parser = argparse.ArgumentParser()
        parser.add_argument("--skip-health-check", action="store_true",
                            help="skip the pre-run health check")
        parser.add_argument("--overseerr-host", default=defaults["overseerr_host"],
                            help="overseerr host url")
        parser.add_argument("--overseerr-token", default=defaults["overseerr_token"],
                            help="overseerr api token")
        parser.add_argument("--discord-webhook", default=defaults["discord_webhook"],
                            help="number of overseerr requests to look through")
        parser.add_argument("--num-requests", default=defaults["num_requests"],
                            help="number of overseerr requests to look through")
        parser.add_argument("--ignore-hours", default=defaults["ignore_hours"],
                            help="ignore notifying requests made in the last X hours")
        self.docker = defaults["DOCKER"]
        self.args = parser.parse_args()

        self.print_timestamp_if_docker()
        print("Starting Check")

        if not self.args.overseerr_host \
                or not self.args.overseerr_token \
                or not self.args.discord_webhook:
            print("the following arguments are required: overseerr-host, overseerr-token, discord-webhook")
            exit(1)

        # Some hosts APIs get real fussy about extra slashes
        self.args.overseerr_host = self.args.overseerr_host.rstrip("/")

        self.pending_requests = []

    def print_timestamp_if_docker(self):
        if self.docker:
            print(f"{datetime.now()}: ", end="")

    def _overseerr_get_request(self, endpoint):
        headers = {
            "Content-type": "application/json",
            "x-api-key": self.args.overseerr_token
        }
        # return json.loads(requests.get(f"{endpoint}", headers=headers).text)
        return requests.get(f"{endpoint}", headers=headers).json()

    def find(self):
        request_url = f"{self.args.overseerr_host}/api/v1/request?take={self.args.num_requests}&filter=pending"
        pending_requests = self._overseerr_get_request(request_url)["results"]
        self.pending_requests = pending_requests

    def build_message(self):
        # Constructing the message
        message_builder = ""
        for request in self.pending_requests:
            # Replace host and protocol in serviceUrl with reverse_proxy_url
            request_url = f"{self.args.overseerr_host}/{request["type"]}/{request["media"]["tmdbId"]}"

            title_request = f"{self.args.overseerr_host}/api/v1/{request["type"]}/{request["media"]["tmdbId"]}"
            title_response = self._overseerr_get_request(title_request)
            title = title_response["title"] if "title" in title_response else title_response["name"]

            message_builder += f"{title}: {request_url}\n"
        return message_builder

    def notify_discord(self, message_content):
        self.print_timestamp_if_docker()
        print("Preparing discord notification...")
        payload = {
            "embeds": [
                {
                    "title": "The following requests are in the 'Pending' state",
                    "description": message_content,
                    "color": 16711680  # Optional: Decimal color value, red in this case
                }
            ]
        }
        requests.post(self.args.discord_webhook, json=payload)
        self.print_timestamp_if_docker()
        print("Notification sent!")

    def filter_by_time(self):
        temp_pending_requests = []
        ignore_hours = datetime.now(timezone.utc) - timedelta(hours=self.args.ignore_hours)
        for pending_request in self.pending_requests:
            created_at = (datetime.strptime(pending_request["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
                          .replace(tzinfo=timezone.utc))
            if created_at < ignore_hours:
                temp_pending_requests.append(pending_request)
        self.pending_requests = temp_pending_requests


if __name__ == '__main__':
    overseerr_notify = OverseerrNotify()
    overseerr_notify.find()
    if overseerr_notify.pending_requests:
        overseerr_notify.filter_by_time()
        overseerr_notify.print_timestamp_if_docker()
        print(f"{len(overseerr_notify.pending_requests)} pending requests found.")
        message = overseerr_notify.build_message()
        overseerr_notify.notify_discord(message)
    else:
        overseerr_notify.print_timestamp_if_docker()
        print("No pending requests found :)")
    overseerr_notify.print_timestamp_if_docker()
    print("Done!\n")
