import json
import datetime
import os
from typing import Dict, Any

class ProgressTracker:
    def __init__(self, log_dir: str = 'logs'):
        """Initialize Progress Tracker"""
        self.log_dir = log_dir
        self.progress_file = os.path.join(log_dir, 'search_progress.json')
        self.session_log = os.path.join(log_dir, f'session_{self.get_timestamp()}.log')

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        self.progress_data = {
            'last_session': self.get_timestamp(),
            'current_position': {
                'category_index': 0,
                'subcategory_index': 0,
                'category': None,
                'subcategory': None
            },
            'completed': {
                'categories': [],
                'subcategories': {},  # Format: {'category': ['subcategory1', 'subcategory2']}
                'downloads': {}  # Format: {'category': {'subcategory': count}}
            },
            'statistics': {
                'total_categories': 0,
                'completed_categories': 0,
                'total_subcategories': 0,
                'completed_subcategories': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'total_downloads': 0
            },
            'last_processed': {
                'category': None,
                'subcategory': None,
                'timestamp': None
            }
        }
        
        self.load_progress()

    def get_timestamp(self) -> str:
        """Generate timestamp for logging"""
        return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    def load_progress(self):
        """Load existing progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    self.progress_data.update(saved_progress)
                self.log_message("Progress loaded successfully")
        except Exception as e:
            self.log_message(f"Error loading progress: {str(e)}")

    def save_progress(self):
        """Save progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=4)
            self.log_message("Progress saved successfully")
        except Exception as e:
            self.log_message(f"Error saving progress: {str(e)}")
    
        
    def log_message(self, message: str):
        """Log a message with timestamp"""
        timestamp = self.get_timestamp()
        log_entry = f"[{timestamp}] {message}\n"
        try:
            with open(self.session_log, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log: {str(e)}")
        print(log_entry.strip())
        
    def get_total_subcategories(self, category: str) -> int:
        """Get total number of subcategories for a category"""
        try:
            return len(self.progress_data['completed']['downloads'][category])
        except Exception as e:
            self.log_message(f"Error getting total subcategories: {str(e)}")
            return 0

    def update_position(self, category: str, subcategory: str, category_index: int, subcategory_index: int):
        """Update current search position with names and indices"""
        self.progress_data['current_position'].update({
            'category_index': category_index,
            'subcategory_index': subcategory_index,
            'category': category,
            'subcategory': subcategory
        })
        self.progress_data['last_processed'] = {
            'category': category,
            'subcategory': subcategory,
            'timestamp': self.get_timestamp()
        }
        self.save_progress()

    def mark_subcategory_complete(self, category: str, subcategory: str):
        """Mark a subcategory as completed"""
        try:
            if category not in self.progress_data['completed']['subcategories']:
                self.progress_data['completed']['subcategories'][category] = []
                
            if subcategory not in self.progress_data['completed']['subcategories'][category]:
                self.progress_data['completed']['subcategories'][category].append(subcategory)
                self.progress_data['statistics']['completed_subcategories'] += 1
                self.save_progress()
                self.log_message(f"Marked subcategory {subcategory} as complete")
                
                # Check category completion
                self.check_category_completion(category)
        except Exception as e:
            self.log_message(f"Error marking subcategory complete: {str(e)}")
            

    def check_category_completion(self, category: str):
        """Check if all subcategories in a category are complete"""
        try:
            if category not in self.progress_data['completed']['categories']:
                if self.is_category_complete(category):
                    self.progress_data['completed']['categories'].append(category)
                    self.progress_data['statistics']['completed_categories'] += 1
                    self.save_progress()
                    self.log_message(f"Category {category} marked as complete")
        except Exception as e:
            self.log_message(f"Error checking category completion: {str(e)}")

    def is_category_complete(self, category: str) -> bool:
        """Check if a category is completed"""
        try:
            completed_subs = self.progress_data['completed']['subcategories'].get(category, [])
            total_subs = self.get_total_subcategories(category)
            return len(completed_subs) == total_subs and total_subs > 0
        except Exception as e:
            self.log_message(f"Error checking category completion: {str(e)}")
            return False

    def get_current_position(self) -> Dict[str, int]:
        """Get current position in search process"""
        return self.progress_data['current_position']

    def update_search_progress(self, category: str, subcategory: str, success: bool):
        """Update progress for a search attempt"""
        if success:
            self.progress_data['statistics']['successful_searches'] += 1
        else:
            self.progress_data['statistics']['failed_searches'] += 1
        self.save_progress()

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of current progress"""
        return {
            'current_position': self.progress_data['current_position'],
            'statistics': self.progress_data['statistics'],
            'completed_categories': len(self.progress_data['completed']['categories']),
            'total_categories': self.progress_data['statistics']['total_categories']
        }
    def record_download(self, category: str, subcategory: str, count: int = 1):
        """Record successful download"""
        try:
            if category not in self.progress_data['completed']['downloads']:
                self.progress_data['completed']['downloads'][category] = {}
            if subcategory not in self.progress_data['completed']['downloads'][category]:
                self.progress_data['completed']['downloads'][category][subcategory] = 0
                
            self.progress_data['completed']['downloads'][category][subcategory] += count
            self.progress_data['statistics']['total_downloads'] += count
            self.save_progress()
            
        except Exception as e:
            self.log_message(f"Error recording download: {str(e)}")
            
    def initialize_category_tracking(self, categories_data: dict):
        """Initialize tracking with categories data"""
        try:
            total_categories = len(categories_data)
            total_subcategories = sum(len(subcats) for subcats in categories_data.values())
            
            self.progress_data['statistics'].update({
                'total_categories': total_categories,
                'total_subcategories': total_subcategories
            })
            
            # Initialize download tracking
            for category, subcategories in categories_data.items():
                if category not in self.progress_data['completed']['downloads']:
                    self.progress_data['completed']['downloads'][category] = {}
                    for subcategory in subcategories:
                        if subcategory not in self.progress_data['completed']['downloads'][category]:
                            self.progress_data['completed']['downloads'][category][subcategory] = 0
            
            self.save_progress()
            self.log_message(f"Initialized tracking for {total_categories} categories and {total_subcategories} subcategories")
            
        except Exception as e:
            self.log_message(f"Error initializing category tracking: {str(e)}")
            
    def get_resume_point(self) -> Dict[str, Any]:
        """Get point to resume processing"""
        try:
            current_pos = self.progress_data['current_position']
            last_proc = self.progress_data['last_processed']
            
            return {
                'category_index': current_pos['category_index'],
                'subcategory_index': current_pos['subcategory_index'],
                'category': current_pos['category'] or last_proc['category'],
                'subcategory': current_pos['subcategory'] or last_proc['subcategory'],
                'downloads': self.progress_data['completed']['downloads']
            }
            
        except Exception as e:
            self.log_message(f"Error getting resume point: {str(e)}")
            return None
        
    def is_subcategory_complete(self, category: str, subcategory: str) -> bool:
        """Check if subcategory has required downloads"""
        try:
            downloads = self.progress_data['completed']['downloads'].get(category, {}).get(subcategory, 0)
            required_downloads = 2  # Set explicit requirement
            return downloads >= required_downloads
        except Exception as e:
            self.log_message(f"Error checking subcategory completion: {str(e)}")
            return False
        
    def get_subcategory_downloads(self, category: str, subcategory: str) -> int:
        """Get current download count for a subcategory"""
        try:
            return self.progress_data['completed']['downloads'].get(category, {}).get(subcategory, 0)
        except Exception as e:
            self.log_message(f"Error getting subcategory downloads: {str(e)}")
            return 0
    def get_daily_count(self) -> int:
        """Get today's download count"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            daily_count = 0
            
            # Calculate today's downloads from completed downloads
            for category in self.progress_data['completed']['downloads']:
                for subcategory in self.progress_data['completed']['downloads'][category]:
                    daily_count += self.progress_data['completed']['downloads'][category][subcategory]
            
            return daily_count
        except Exception as e:
            self.log_message(f"Error getting daily count: {str(e)}")
            return 0

    def get_total_count(self) -> int:
        """Get total download count"""
        try:
            return self.progress_data['statistics']['total_downloads']
        except Exception as e:
            self.log_message(f"Error getting total count: {str(e)}")
            return 0
    def print_stats(self) -> str:
        """Print detailed statistics"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            stats_message = f"""
            Download Statistics:
            Total Downloads: {self.progress_data['statistics']['total_downloads']}
            Today's Downloads ({today}): {self.get_daily_count()}
            Last Updated: {self.progress_data['last_processed']['timestamp']}

    Category-wise Downloads:
    """
            # Add category statistics
            for category in self.progress_data['completed']['downloads']:
                stats_message += f"\n{category}:"
                for subcategory, count in self.progress_data['completed']['downloads'][category].items():
                    stats_message += f"\n  - {subcategory}: {count}"
                
            # Add completion statistics
            stats_message += f"""

    Completion Status:
    Total Categories: {self.progress_data['statistics']['total_categories']}
    Completed Categories: {self.progress_data['statistics']['completed_categories']}
    Total Subcategories: {self.progress_data['statistics']['total_subcategories']}
    Completed Subcategories: {self.progress_data['statistics']['completed_subcategories']}
    Successful Searches: {self.progress_data['statistics']['successful_searches']}
    Failed Searches: {self.progress_data['statistics']['failed_searches']}
    """
            
            self.log_message(stats_message)
            return stats_message
            
        except Exception as e:
            error_message = f"Error printing stats: {str(e)}"
            self.log_message(error_message)
            return error_message