class DownloadTracker:
    def __init__(self, log_file, stats_file='download_stats.json'):
        self.stats_file = stats_file
        self.log_file = log_file
        self.stats = self._load_stats()

    def _create_initial_stats(self):
        return {
            "total_downloads": 0,
            "daily_stats": {},
            "category_stats": {},  # New: Track by category
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def record_download(self, category=None, subcategory=None):
        """
        Record download with optional category tracking
        """
        today = datetime.now().strftime("%Y-%m-%d")
        self.stats["total_downloads"] += 1
        
        # Daily stats
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = 0
        self.stats["daily_stats"][today] += 1
        
        # Category stats (if provided)
        if category and subcategory:
            if category not in self.stats["category_stats"]:
                self.stats["category_stats"][category] = {}
            if subcategory not in self.stats["category_stats"][category]:
                self.stats["category_stats"][category][subcategory] = 0
            self.stats["category_stats"][category][subcategory] += 1
        
        self.stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_stats()
        
        self._log_message(f"Download recorded - Category: {category}, Subcategory: {subcategory}, Total: {self.stats['total_downloads']}")

    def print_stats(self):
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