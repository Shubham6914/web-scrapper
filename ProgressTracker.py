import json
import datetime
import os
from typing import Dict, List, Any

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
            'pattern_data': {},
            'statistics': {
                'total_patterns': 0,
                'completed_patterns': 0,
                'total_urls': 0,
                'downloaded_urls': 0,
                'failed_urls': 0
            },
            'current_position': {
                'category': None,
                'subcategory': None,
                'pattern_index': 0,
                'current_pattern': None
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
        """Save current progress to file"""
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
    
    
    def initialize_pattern_tracking(self, category: str, subcategory: str, pattern: str, urls: list) -> str:
        """Initialize tracking for a specific pattern"""
        try:
            # Initialize nested structure if not exists
            if category not in self.progress_data['pattern_data']:
                self.progress_data['pattern_data'][category] = {}
            
            if subcategory not in self.progress_data['pattern_data'][category]:
                self.progress_data['pattern_data'][category][subcategory] = {}
            
            # Generate pattern key
            pattern_key = f"pattern_{len(self.progress_data['pattern_data'][category][subcategory]) + 1}"
            
            # Create pattern entry
            self.progress_data['pattern_data'][category][subcategory][pattern_key] = {
                'pattern': pattern,
                'status': 'in_progress',
                'urls': {
                    'total': len(urls),
                    'downloaded': [],
                    'pending': urls.copy(),
                    'failed': []
                }
            }
            
            # Update current position
            self.progress_data['current_position'].update({
                'category': category,
                'subcategory': subcategory,
                'pattern_index': len(self.progress_data['pattern_data'][category][subcategory]),
                'current_pattern': pattern
            })
            
            # Update statistics
            self.progress_data['statistics']['total_patterns'] += 1
            self.progress_data['statistics']['total_urls'] += len(urls)
            
            self.save_progress()
            return pattern_key
            
        except Exception as e:
            self.log_message(f"Error initializing pattern tracking: {str(e)}")
            return None

    def update_pattern_progress(self, category: str, subcategory: str, pattern_key: str, url: str, success: bool):
        """Update progress for a specific pattern"""
        try:
            pattern_data = self.progress_data['pattern_data'][category][subcategory][pattern_key]
            
            if success:
                # Move URL from pending to downloaded
                if url in pattern_data['urls']['pending']:
                    pattern_data['urls']['pending'].remove(url)
                    pattern_data['urls']['downloaded'].append(url)
                    self.progress_data['statistics']['downloaded_urls'] += 1
                
                # Remove from failed if it was there
                if url in pattern_data['urls']['failed']:
                    pattern_data['urls']['failed'].remove(url)
            else:
                # Add to failed if not already there
                if url not in pattern_data['urls']['failed']:
                    pattern_data['urls']['failed'].append(url)
                    self.progress_data['statistics']['failed_urls'] += 1
            
            # Update pattern status if complete
            if not pattern_data['urls']['pending']:
                pattern_data['status'] = 'completed'
                self.progress_data['statistics']['completed_patterns'] += 1
            
            self.save_progress()
            
        except Exception as e:
            self.log_message(f"Error updating pattern progress: {str(e)}")

    def get_pattern_status(self, category: str, subcategory: str, pattern: str) -> dict:
        """Get status of a specific pattern"""
        try:
            patterns = self.progress_data['pattern_data'].get(category, {}).get(subcategory, {})
            for pattern_key, data in patterns.items():
                if data['pattern'] == pattern:
                    return data
            return None
        except Exception as e:
            self.log_message(f"Error getting pattern status: {str(e)}")
            return None

    def is_pattern_completed(self, category: str, subcategory: str, pattern: str) -> bool:
        """Check if a pattern's downloads are completed"""
        try:
            pattern_status = self.get_pattern_status(category, subcategory, pattern)
            return pattern_status and pattern_status['status'] == 'completed'
        except Exception as e:
            self.log_message(f"Error checking pattern completion: {str(e)}")
            return False

    def get_next_pending_pattern(self, category: str, subcategory: str) -> dict:
        """Get next pattern that needs processing"""
        try:
            patterns = self.progress_data['pattern_data'].get(category, {}).get(subcategory, {})
            for pattern_key, data in patterns.items():
                if data['status'] == 'in_progress':
                    return {
                        'pattern_key': pattern_key,
                        'pattern_data': data
                    }
            return None
        except Exception as e:
            self.log_message(f"Error getting next pending pattern: {str(e)}")
            return None
    def get_resume_point(self) -> Dict[str, Any]:
        """Get the point where processing should resume"""
        try:
            current_position = self.progress_data['current_position']
            
            # Get the last active pattern
            if current_position['category'] and current_position['subcategory']:
                pattern_data = self.get_next_pending_pattern(
                    current_position['category'],
                    current_position['subcategory']
                )
                
                if pattern_data:
                    return {
                        'category': current_position['category'],
                        'subcategory': current_position['subcategory'],
                        'pattern': current_position['current_pattern'],
                        'pattern_index': current_position['pattern_index']
                    }
            
            # If no active pattern, return default position
            return {
                'category': None,
                'subcategory': None,
                'pattern': None,
                'pattern_index': 0
            }
            
        except Exception as e:
            self.log_message(f"Error getting resume point: {str(e)}")
            return {
                'category': None,
                'subcategory': None,
                'pattern': None,
                'pattern_index': 0
            }

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of current progress"""
        try:
            return {
                'current_position': self.progress_data['current_position'],
                'statistics': self.progress_data['statistics'],
                'pattern_summary': self._get_pattern_summary()
            }
        except Exception as e:
            self.log_message(f"Error getting progress summary: {str(e)}")
            return {}

    def _get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of pattern progress"""
        try:
            summary = {}
            for category, subcategories in self.progress_data['pattern_data'].items():
                if category not in summary:
                    summary[category] = {}
                    
                for subcategory, patterns in subcategories.items():
                    if subcategory not in summary[category]:
                        summary[category][subcategory] = []
                        
                    for pattern_key, data in patterns.items():
                        pattern_info = {
                            'pattern': data['pattern'],
                            'status': data['status'],
                            'urls': {
                                'total': data['urls']['total'],
                                'downloaded': len(data['urls']['downloaded']),
                                'pending': len(data['urls']['pending']),
                                'failed': len(data['urls']['failed'])
                            }
                        }
                        summary[category][subcategory].append(pattern_info)
            
            return summary
        except Exception as e:
            self.log_message(f"Error getting pattern summary: {str(e)}")
            return {}

    def print_progress_report(self):
        """Print detailed progress report"""
        try:
            summary = self.get_progress_summary()
            
            report = "\n=== Progress Report ===\n"
            
            # Current Position
            report += "\nCurrent Position:\n"
            report += f"Category: {summary['current_position']['category']}\n"
            report += f"Subcategory: {summary['current_position']['subcategory']}\n"
            report += f"Current Pattern: {summary['current_position']['current_pattern']}\n"
            
            # Statistics
            report += "\nOverall Statistics:\n"
            report += f"Total Patterns: {summary['statistics']['total_patterns']}\n"
            report += f"Completed Patterns: {summary['statistics']['completed_patterns']}\n"
            report += f"Total URLs: {summary['statistics']['total_urls']}\n"
            report += f"Downloaded URLs: {summary['statistics']['downloaded_urls']}\n"
            report += f"Failed URLs: {summary['statistics']['failed_urls']}\n"
            
            # Pattern Progress
            if 'pattern_summary' in summary:
                report += "\nPattern Progress:\n"
                for category, subcategories in summary['pattern_summary'].items():
                    report += f"\n{category}:\n"
                    for subcategory, patterns in subcategories.items():
                        report += f"  {subcategory}:\n"
                        for pattern in patterns:
                            report += f"    Pattern: {pattern['pattern']}\n"
                            report += f"    Status: {pattern['status']}\n"
                            report += f"    URLs - Total: {pattern['urls']['total']}, "
                            report += f"Downloaded: {pattern['urls']['downloaded']}, "
                            report += f"Pending: {pattern['urls']['pending']}, "
                            report += f"Failed: {pattern['urls']['failed']}\n"
                            report += "    ---\n"
            
            report += "\n=====================\n"
            
            print(report)
            self.log_message(report)
            
        except Exception as e:
            self.log_message(f"Error printing progress report: {str(e)}")
            
            
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
