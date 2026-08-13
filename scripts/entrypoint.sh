#!/bin/sh
set -e

# CRON_WORKERS is a comma-separated list of registered worker names. Set it to
# an empty string to disable cron. WORKER_CRON_<NAME> overrides a schedule.
if [ -n "${CRON_WORKERS-enrich}" ]; then
    python scripts/install_worker_crontab.py \
        --project-dir /app \
        --python /usr/local/bin/python \
        --log-dir /var/log/news-workers \
        --crontab-file /etc/crontabs/root

    echo "⏰ [Docker] Starting Alpine crond service..."
    crond -b -l 2
else
    echo "ℹ️ [Docker] Worker cron is disabled."
fi

exec "$@"
