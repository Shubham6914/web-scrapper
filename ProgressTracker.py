import json
import datetime
import os
from typing import Dict, List, Any

class ProgressTracker:
    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize Progress Tracker
        
        Parameters:
        - log_dir: Directory to store progress logs
        """
        self.log_dir = log_dir
        self.progress_file = os.path.join(log_dir, 'search_progress.json')
        self.session_log = os.path.join(log_dir, f'session_{self.get_timestamp()}.log')
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Initialize progress data
        self.progress_data = {
            'last_session': self.get_timestamp(),
            'categories': {},
            'statistics': {
                'total_searches': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'documents_found': 0
            },
            'current_position': {
                'category': None,
                'subcategory': None,
                'pattern_index': 0
            }
        }
        
        # Load existing progress if available
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
        """Save current progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=4)
            self.log_message("Progress saved successfully")
        except Exception as e:
            self.log_message(f"Error saving progress: {str(e)}")

    def update_search_progress(self, category: str, subcategory: str, 
                             pattern: str, success: bool, documents: int = 0):
        """
        Update progress for a search attempt
        
        Parameters:
        - category: Current category
        - subcategory: Current subcategory
        - pattern: Search pattern used
        - success: Whether search was successful
        - documents: Number of documents found
        """
        try:
            # Update current position
            self.progress_data['current_position'].update({
                'category': category,
                'subcategory': subcategory
            })

            # Initialize category if not exists
            if category not in self.progress_data['categories']:
                self.progress_data['categories'][category] = {
                    'subcategories': {},
                    'completed': False
                }

            # Initialize subcategory if not exists
            if subcategory not in self.progress_data['categories'][category]['subcategories']:
                self.progress_data['categories'][category]['subcategories'][subcategory] = {
                    'patterns_tried': [],
                    'successful_patterns': [],
                    'documents_found': 0,
                    'completed': False
                }

            # Update statistics
            self.progress_data['statistics']['total_searches'] += 1
            if success:
                self.progress_data['statistics']['successful_searches'] += 1
                self.progress_data['statistics']['documents_found'] += documents
                self.progress_data['categories'][category]['subcategories'][subcategory]['successful_patterns'].append(pattern)
            else:
                self.progress_data['statistics']['failed_searches'] += 1

            # Add pattern to tried patterns
            self.progress_data['categories'][category]['subcategories'][subcategory]['patterns_tried'].append(pattern)

            # Save progress
            self.save_progress()
            self.log_message(f"Progress updated for {category} - {subcategory}")

        except Exception as e:
            self.log_message(f"Error updating progress: {str(e)}")

    def mark_subcategory_complete(self, category: str, subcategory: str):
        """Mark a subcategory as completed"""
        try:
            self.progress_data['categories'][category]['subcategories'][subcategory]['completed'] = True
            self.check_category_completion(category)
            self.save_progress()
            self.log_message(f"Marked subcategory {subcategory} as complete")
        except Exception as e:
            self.log_message(f"Error marking subcategory complete: {str(e)}")

    def check_category_completion(self, category: str):
        """Check if all subcategories in a category are complete"""
        try:
            subcategories = self.progress_data['categories'][category]['subcategories']
            if all(sub['completed'] for sub in subcategories.values()):
                self.progress_data['categories'][category]['completed'] = True
                self.log_message(f"Category {category} marked as complete")
        except Exception as e:
            self.log_message(f"Error checking category completion: {str(e)}")

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of current progress"""
        return {
            'statistics': self.progress_data['statistics'],
            'current_position': self.progress_data['current_position'],
            'completed_categories': sum(1 for cat in self.progress_data['categories'].values() 
                                     if cat['completed']),
            'total_categories': len(self.progress_data['categories'])
        }

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

    def get_resume_point(self) -> Dict[str, Any]:
        """Get the point where search should resume"""
        return {
            'category': self.progress_data['current_position']['category'],
            'subcategory': self.progress_data['current_position']['subcategory'],
            'pattern_index': self.progress_data['current_position']['pattern_index']
        }

    def print_progress_report(self):
        """Print detailed progress report"""
        summary = self.get_progress_summary()
        report = f"""
=== Search Progress Report ===
Total Searches: {summary['statistics']['total_searches']}
Successful Searches: {summary['statistics']['successful_searches']}
Failed Searches: {summary['statistics']['failed_searches']}
Documents Found: {summary['statistics']['documents_found']}
Completed Categories: {summary['completed_categories']}/{summary['total_categories']}
Current Position:
- Category: {summary['current_position']['category']}
- Subcategory: {summary['current_position']['subcategory']}
========================
"""
        print(report)
        self.log_message(report)