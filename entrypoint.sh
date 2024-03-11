#!/bin/bash
python3 /usr/src/app/src/docker_setup.py
# Run once at startup
python3 /usr/src/app/src/overseerr_notify.py
cron
tail -f /var/log/cron.log
