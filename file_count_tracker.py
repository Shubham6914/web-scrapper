import os
import json
from datetime import datetime

class DownloadTracker:
    def __init__(self, log_file, stats_file='download_stats.json'):
        self.stats_file = stats_file
        self.log_file = log_file
        self.stats = self._load_stats()

    def _log_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a') as f:
            f.write(f'[{timestamp}] {message}\n')

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._create_initial_stats()
        return self._create_initial_stats()

    def _create_initial_stats(self):
        return {
            "total_downloads": 0,
            "daily_stats": {},
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _save_stats(self):
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=4)

    def record_download(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.stats["total_downloads"] += 1
        
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = 0
        self.stats["daily_stats"][today] += 1
        
        self.stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_stats()
        
        self._log_message(f"Download recorded. New total: {self.stats['total_downloads']}")

    def get_daily_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.stats["daily_stats"].get(today, 0)

    def get_total_count(self):
        return self.stats["total_downloads"]

    def print_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        stats_message = f"""
Download Statistics:
Total Downloads: {self.stats['total_downloads']}
Today's Downloads ({today}): {self.stats['daily_stats'].get(today, 0)}
Last Updated: {self.stats['last_updated']}
"""
        self._log_message(stats_message)
        return stats_message