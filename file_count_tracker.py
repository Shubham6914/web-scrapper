import os
import json
from datetime import datetime

class DownloadTracker:
    def __init__(self, log_file, stats_file='download_stats.json'):
        self.stats_file = stats_file
        self.log_file = log_file
        self.stats = self._load_stats()

    def _log_message(self, message):
        """Internal logging method"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.log_file, 'a') as f:
                f.write(f'[{timestamp}] {message}\n')
            print(f'[{timestamp}] {message}')
        except Exception as e:
            print(f"Error writing to log: {str(e)}")
            print(f"Message was: {message}")

    def _load_stats(self):
        """Load existing stats or create new ones"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self._log_message("Error reading stats file, creating new stats")
                return self._create_initial_stats()
            except Exception as e:
                self._log_message(f"Error loading stats: {str(e)}")
                return self._create_initial_stats()
        return self._create_initial_stats()

    def _create_initial_stats(self):
        """Create initial stats structure"""
        return {
            "total_downloads": 0,
            "daily_stats": {},
            "category_stats": {},  # Track by category
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _save_stats(self):
        """Save stats to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            self._log_message(f"Error saving stats: {str(e)}")

    def record_download(self, category=None, subcategory=None):
        """Record download with category tracking"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            self.stats["total_downloads"] += 1
            
            # Daily stats
            if today not in self.stats["daily_stats"]:
                self.stats["daily_stats"][today] = 0
            self.stats["daily_stats"][today] += 1
            
            # Category stats
            if category and subcategory:
                if category not in self.stats["category_stats"]:
                    self.stats["category_stats"][category] = {}
                if subcategory not in self.stats["category_stats"][category]:
                    self.stats["category_stats"][category][subcategory] = 0
                self.stats["category_stats"][category][subcategory] += 1
            
            self.stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_stats()
            
            self._log_message(
                f"Download recorded - Category: {category}, "
                f"Subcategory: {subcategory}, "
                f"Total: {self.stats['total_downloads']}"
            )
        except Exception as e:
            self._log_message(f"Error recording download: {str(e)}")

    def get_daily_count(self):
        """Get today's download count"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.stats["daily_stats"].get(today, 0)

    def get_total_count(self):
        """Get total download count"""
        return self.stats["total_downloads"]

    def print_stats(self):
        """Print detailed statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            stats_message = f"""
Download Statistics:
Total Downloads: {self.stats['total_downloads']}
Today's Downloads ({today}): {self.stats['daily_stats'].get(today, 0)}
Last Updated: {self.stats['last_updated']}

Category-wise Downloads:
"""
            # Add category statistics if available
            if self.stats.get("category_stats"):
                for category, subcats in self.stats["category_stats"].items():
                    stats_message += f"\n{category}:"
                    for subcat, count in subcats.items():
                        stats_message += f"\n  - {subcat}: {count}"
                    
            self._log_message(stats_message)
            return stats_message
        except Exception as e:
            self._log_message(f"Error printing stats: {str(e)}")
            return "Error getting statistics"