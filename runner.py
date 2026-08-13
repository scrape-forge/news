# -*- coding: utf-8 -*-
"""
Lightweight production scheduler script for running Scrapy spiders periodically.
Used as the main ENTRYPOINT for the Docker production container.
"""

import os
import sys
import time
import subprocess
import schedule

SPIDERS = [
    'antara', 'detik', 'liputan6', 'okezone',
    'republika', 'sindo', 'tempo', 'tribun',
    'jawapos', 'kompas', 'merdeka', 'suara'
]

INTERVAL_HOURS = int(os.getenv('CRAWL_INTERVAL_HOURS', '6'))
RUN_ENRICH_WORKER_AFTER_CRAWL = os.getenv(
    "RUN_ENRICH_WORKER_AFTER_CRAWL", "true"
).lower() in {"1", "true", "yes", "on"}


def run_all_spiders():
    print(f"🚀 [Scheduler] Starting news crawl cycle for {len(SPIDERS)} spiders...", flush=True)
    start_time = time.time()
    
    for spider in SPIDERS:
        print(f"🕷️ [Scheduler] Running spider: {spider}", flush=True)
        try:
            subprocess.run(["scrapy", "crawl", spider], check=False)
        except Exception as exc:
            print(f"⚠️ [Scheduler] Error executing spider {spider}: {exc}", flush=True)
            
    elapsed = time.time() - start_time
    print(f"✅ [Scheduler] Crawl cycle completed in {elapsed:.1f} seconds.", flush=True)

    # Run Papagon Insight enrichment for newly scraped articles.
    if RUN_ENRICH_WORKER_AFTER_CRAWL and os.getenv("GROQ_API_KEY"):
        print("🤖 [Scheduler] Running Papagon Insight enrichment...", flush=True)
        try:
            subprocess.run(
                [sys.executable, "-m", "news.workers", "enrich"],
                check=False,
            )
        except Exception as exc:
            print(f"⚠️ [Scheduler] Error running enrichment worker: {exc}", flush=True)



def main():
    print(f"📌 [Scheduler] Initializing Scrapy News Scheduler (Interval: every {INTERVAL_HOURS} hours)...", flush=True)
    
    # Run once immediately on container startup
    run_all_spiders()
    
    # Schedule subsequent runs
    schedule.every(INTERVAL_HOURS).hours.do(run_all_spiders)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    main()
