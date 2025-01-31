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
                'subcategory_index': 0
            },
            'completed': {
                'categories': [],
                'subcategories': {}  # Format: {'category': ['subcategory1', 'subcategory2']}
            },
            'statistics': {
                'total_categories': 0,
                'completed_categories': 0,
                'total_subcategories': 0,
                'completed_subcategories': 0,
                'successful_searches': 0,
                'failed_searches': 0
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

    def update_position(self, category_index: int, subcategory_index: int):
        """Update current search position"""
        self.progress_data['current_position'].update({
            'category_index': category_index,
            'subcategory_index': subcategory_index
        })
        self.save_progress()

    def mark_subcategory_complete(self, category: str, subcategory: str):
        """Mark a subcategory as completed"""
        if category not in self.progress_data['completed']['subcategories']:
            self.progress_data['completed']['subcategories'][category] = []
            
        if subcategory not in self.progress_data['completed']['subcategories'][category]:
            self.progress_data['completed']['subcategories'][category].append(subcategory)
            self.progress_data['statistics']['completed_subcategories'] += 1
            self.save_progress()
            
        self.check_category_completion(category)

    def check_category_completion(self, category: str):
        """Check if all subcategories in a category are complete"""
        if category not in self.progress_data['completed']['categories']:
            if self.is_category_complete(category):
                self.progress_data['completed']['categories'].append(category)
                self.progress_data['statistics']['completed_categories'] += 1
                self.save_progress()

    def is_category_complete(self, category: str) -> bool:
        """Check if a category is completed"""
        completed_subs = self.progress_data['completed']['subcategories'].get(category, [])
        total_subs = self.get_total_subcategories(category)
        return len(completed_subs) == total_subs

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

    def initialize_categories(self, total_categories: int, total_subcategories: int):
        """Initialize category and subcategory counts"""
        self.progress_data['statistics'].update({
            'total_categories': total_categories,
            'total_subcategories': total_subcategories
        })
        self.save_progress()