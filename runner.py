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

    # Run AI Tag Worker to batch-tag untagged articles
    if os.getenv("GROQ_API_KEY"):
        print("🤖 [Scheduler] Running Groq AI Tag Worker for newly scraped articles...", flush=True)
        try:
            subprocess.run([sys.executable, "scripts/tag_worker.py"], check=False)
        except Exception as exc:
            print(f"⚠️ [Scheduler] Error running tag worker: {exc}", flush=True)



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
