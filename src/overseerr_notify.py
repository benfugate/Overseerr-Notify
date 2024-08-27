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

        if (not self.args.skip_health_check
                and (not self.args.overseerr_host
                     or not self.args.overseerr_token
                     or not self.args.discord_webhook)):
            print("the following arguments are required: overseerr-host, overseerr-token, discord-webhook")
            exit(1)

        # Some hosts APIs get real fussy about extra slashes
        self.args.overseerr_host = self.args.overseerr_host.rstrip("/")

        self.pending_requests = []
        self.open_issues = []

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

    def find_unapproved(self):
        request_url = f"{self.args.overseerr_host}/api/v1/request?take={self.args.num_requests}&filter=pending"
        pending_requests = self._overseerr_get_request(request_url)["results"]
        self.pending_requests = self.filter_by_time(pending_requests)

    def find_issues(self):
        request_url = f"{self.args.overseerr_host}/api/v1/issue"
        issues = self._overseerr_get_request(request_url)["results"]
        self.open_issues = self.filter_by_time(issues)

    @staticmethod
    def build_message(title, payload):
        discord_msg = {
            "embeds": [
                {
                    "title": title,
                    "color": 16711680,
                    "timestamp": f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}+00:00",
                    "fields": payload
                }
            ]
        }
        return discord_msg

    def notify_discord(self):
        if self.pending_requests:
            # Constructing the message
            pending_requests = []
            for request in self.pending_requests:
                self.print_timestamp_if_docker()
                print(f"{len(self.pending_requests)} pending requests found.")
                request_url = f"- {self.args.overseerr_host}/{request["type"]}/{request["media"]["tmdbId"]}"
                title_request = f"{self.args.overseerr_host}/api/v1/{request["type"]}/{request["media"]["tmdbId"]}"
                title_response = self._overseerr_get_request(title_request)
                title = title_response["title"] if "title" in title_response else title_response["name"]

                pending_requests.append(
                    {
                        "name": title,
                        "value": request_url,
                        "inline": False
                    }
                )
            discord_message = self.build_message("The following requests are in the 'Pending' state",
                                                 [request for request in pending_requests])
            self.print_timestamp_if_docker()
            print("Preparing \"pending requests\" discord notification...")
            requests.post(self.args.discord_webhook, json=discord_message)
            self.print_timestamp_if_docker()
            print("Notification sent!")
        else:
            self.print_timestamp_if_docker()
            print("No pending requests found :)")
        if self.open_issues:
            # Constructing the message
            open_issues = []
            for issue in self.open_issues:
                self.print_timestamp_if_docker()
                print(f"{len(self.open_issues)} open issues found.")


                issue_request = f"{self.args.overseerr_host}/api/v1/issue/{issue["id"]}"
                issue_response = self._overseerr_get_request(issue_request)
                description = (f"- {self.args.overseerr_host}/issues/{issue["id"]}\n"
                               f" - {issue_response["comments"][0]["message"]}")

                title_request = f"{self.args.overseerr_host}/api/v1/{issue["media"]["mediaType"]}/{issue["media"]["tmdbId"]}"
                title_response = self._overseerr_get_request(title_request)
                title = title_response["title"] if "title" in title_response else title_response["name"]

                open_issues.append(
                    {
                        "name": title,
                        "value": description,
                        "inline": False
                    }
                )
            discord_message = self.build_message("The following media issues are open:",
                                                 [issue for issue in open_issues])
            self.print_timestamp_if_docker()
            print("Preparing \"open problems\" discord notification...")
            requests.post(self.args.discord_webhook, json=discord_message)
            self.print_timestamp_if_docker()
            print("Notification sent!")
        else:
            self.print_timestamp_if_docker()
            print("No open issues found :)")

    def filter_by_time(self, items):
        result = []
        ignore_hours = datetime.now(timezone.utc) - timedelta(hours=self.args.ignore_hours)
        for item in items:
            created_at = (datetime.strptime(item["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
                          .replace(tzinfo=timezone.utc))
            if created_at < ignore_hours:
                result.append(item)
        return result


if __name__ == '__main__':
    overseerr_notify = OverseerrNotify()
    overseerr_notify.find_unapproved()
    overseerr_notify.find_issues()
    overseerr_notify.notify_discord()
    overseerr_notify.print_timestamp_if_docker()
    print("Done!\n")
