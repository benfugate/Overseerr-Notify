#!/usr/bin/env python3

import os
import json
import shutil
import sqlite3
import tempfile
import argparse
import requests
from datetime import datetime, timedelta, timezone


class ShelfmarkNotify:
    def __init__(self):
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/config.json") as f:
            defaults = json.load(f)
        parser = argparse.ArgumentParser()
        parser.add_argument("--skip-health-check", action="store_true",
                            help="skip the pre-run health check")
        parser.add_argument("--shelfmark-db", default=defaults.get("shelfmark_db", ""),
                            help="path to the Shelfmark sqlite database (users.db)")
        parser.add_argument("--shelfmark-webhook", default=defaults.get("shelfmark_webhook", ""),
                            help="discord webhook for shelfmark notifications "
                                 "(falls back to --discord-webhook if unset)")
        parser.add_argument("--discord-webhook", default=defaults.get("discord_webhook", ""),
                            help="fallback discord webhook, shared with overseerr_notify")
        parser.add_argument("--shelfmark-host", default=defaults.get("shelfmark_host", ""),
                            help="shelfmark host url, used to build links in notifications")
        parser.add_argument("--ignore-hours", default=defaults["ignore_hours"],
                            help="ignore notifying requests made in the last X hours")
        self.docker = defaults["DOCKER"]
        self.args = parser.parse_args()

        self.print_timestamp_if_docker()
        print("Starting Check")

        # A dedicated webhook is preferred; fall back to the shared overseerr one.
        self.webhook = self.args.shelfmark_webhook or self.args.discord_webhook

        if (not self.args.skip_health_check
                and (not self.args.shelfmark_db or not self.webhook)):
            print("the following arguments are required: shelfmark-db, "
                  "and one of shelfmark-webhook/discord-webhook")
            exit(1)

        self.args.shelfmark_host = (self.args.shelfmark_host or "").rstrip("/")

        self.pending_requests = []

    def print_timestamp_if_docker(self):
        if self.docker:
            print(f"{datetime.now()}: ", end="")

    def find_pending(self):
        # Shelfmark keeps this DB in WAL mode, which requires write access to the
        # containing directory (to create a -shm coordination file) even for reads.
        # The DB is mounted read-only, so instead we copy the db + WAL sidecars into
        # a scratch dir we own and read from that snapshot. Shelfmark's mount/data
        # is never written to.
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_db = os.path.join(tmp_dir, "users.db")
            shutil.copy2(self.args.shelfmark_db, tmp_db)
            for suffix in ("-wal", "-shm"):
                sidecar = self.args.shelfmark_db + suffix
                if os.path.exists(sidecar):
                    shutil.copy2(sidecar, tmp_db + suffix)

            conn = sqlite3.connect(f"file:{tmp_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    """
                    SELECT dr.id, dr.created_at, dr.content_type, dr.book_data,
                           u.username, u.display_name
                    FROM download_requests dr
                    JOIN users u ON u.id = dr.user_id
                    WHERE dr.status = 'pending'
                    """
                ).fetchall()
            finally:
                conn.close()

        pending = []
        for row in rows:
            item = dict(row)
            item["book_data"] = json.loads(item["book_data"])
            pending.append(item)
        self.pending_requests = self.filter_by_time(pending)

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
            self.print_timestamp_if_docker()
            print(f"{len(self.pending_requests)} pending Shelfmark requests found.")

            fields = []
            for item in self.pending_requests:
                book = item["book_data"]
                title = book.get("title", "Unknown title")
                author = book.get("author")
                name = f"{title} — {author}" if author else title
                requester = item["display_name"] or item["username"]

                value_lines = [f"- Requested by {requester}"]
                if self.args.shelfmark_host:
                    value_lines.append(f"- {self.args.shelfmark_host}/requests")
                elif book.get("source_url"):
                    value_lines.append(f"- {book['source_url']}")

                fields.append(
                    {
                        "name": name,
                        "value": "\n".join(value_lines),
                        "inline": False
                    }
                )

            discord_message = self.build_message(
                "The following Shelfmark requests are still pending:", fields
            )
            self.print_timestamp_if_docker()
            print("Preparing \"pending shelfmark requests\" discord notification...")
            requests.post(self.webhook, json=discord_message, timeout=10)
            self.print_timestamp_if_docker()
            print("Notification sent!")
        else:
            self.print_timestamp_if_docker()
            print("No pending Shelfmark requests found :)")

    def filter_by_time(self, items):
        result = []
        ignore_hours = datetime.now(timezone.utc) - timedelta(hours=int(self.args.ignore_hours))
        for item in items:
            created_at = self._parse_created_at(item["created_at"])
            if created_at < ignore_hours:
                result.append(item)
        return result

    @staticmethod
    def _parse_created_at(value):
        # Shelfmark stores created_at as naive UTC "YYYY-MM-DD HH:MM:SS", but be
        # tolerant of an ISO-8601 variant in case that ever changes.
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        raise ValueError(f"Unrecognized created_at format: {value!r}")


if __name__ == '__main__':
    shelfmark_notify = ShelfmarkNotify()
    shelfmark_notify.find_pending()
    shelfmark_notify.notify_discord()
    shelfmark_notify.print_timestamp_if_docker()
    print("Done!\n")
