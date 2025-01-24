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
            
        self.progress_data = {
    'last_session': self.get_timestamp(),
    'pattern_data': {},  # Instead of categories
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
        """Save current progress to file with detailed logging"""
        try:
            # Create a summary of what's being saved
            summary = {
                'categories_saved': list(self.progress_data['pattern_data'].keys()),
                'current_position': self.progress_data['current_position'],
                'statistics': self.progress_data['statistics'],
                'timestamp': self.get_timestamp()
            }
            
            # Save the actual data
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=4)
            
            # Create detailed log message
            log_message = f"""
    Progress Saved Successfully:
    - Timestamp: {summary['timestamp']}
    - Categories: {', '.join(summary['categories_saved']) if summary['categories_saved'] else 'None'}
    - Current Position: 
    * Category: {summary['current_position']['category']}
    * Subcategory: {summary['current_position']['subcategory']}
    * Pattern: {summary['current_position']['current_pattern']}
    - Statistics:
    * Total Patterns: {summary['statistics']['total_patterns']}
    * Completed Patterns: {summary['statistics']['completed_patterns']}
    * Total URLs: {summary['statistics']['total_urls']}
    """
            self.log_message(log_message)
            
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

    def update_search_progress(self, category: str, subcategory: str, 
                         pattern: str, success: bool, documents: int = 0):
        """Update progress for a search attempt"""
        try:
            # Update current position
            self.progress_data['current_position'].update({
                'category': category,
                'subcategory': subcategory
            })

            # Initialize pattern_data if not exists
            if category not in self.progress_data['pattern_data']:
                self.progress_data['pattern_data'][category] = {}

            if subcategory not in self.progress_data['pattern_data'][category]:
                self.progress_data['pattern_data'][category][subcategory] = {}

            # Update statistics
            if 'statistics' not in self.progress_data:
                self.progress_data['statistics'] = {
                    'total_searches': 0,
                    'successful_searches': 0,
                    'failed_searches': 0,
                    'documents_found': 0
                }

            self.progress_data['statistics']['total_searches'] = self.progress_data['statistics'].get('total_searches', 0) + 1
            if success:
                self.progress_data['statistics']['successful_searches'] = self.progress_data['statistics'].get('successful_searches', 0) + 1
                self.progress_data['statistics']['documents_found'] = self.progress_data['statistics'].get('documents_found', 0) + documents

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

   

    def get_resume_point(self) -> Dict[str, Any]:
        """Get the point where search should resume"""
        try:
            current_position = self.progress_data['current_position']
            category = current_position['category']
            subcategory = current_position['subcategory']
            
            if category and subcategory:
                # Check if there are any pending URLs in current pattern
                patterns = self.progress_data['pattern_data'].get(category, {}).get(subcategory, {})
                for pattern_key, data in patterns.items():
                    if data['status'] == 'in_progress' and data['urls']['pending']:
                        return {
                            'category': category,
                            'subcategory': subcategory,
                            'pattern_index': current_position['pattern_index'],
                            'pattern_key': pattern_key,
                            'pending_urls': data['urls']['pending']
                        }
            
            # If no pending URLs, return current position to start next pattern
            return {
                'category': current_position['category'],
                'subcategory': current_position['subcategory'],
                'pattern_index': current_position['pattern_index']
            }
            
        except Exception as e:
            self.log_message(f"Error getting resume point: {str(e)}")
            return {
                'category': None,
                'subcategory': None,
                'pattern_index': 0
            }


    def update_download_progress(self, category: str, subcategory: str, url: str, success: bool):
        """Update download progress for a URL"""
        download_data = self.progress_data['download_progress'][category][subcategory]
        
        if success:
            if url in download_data['pending_urls']:
                download_data['pending_urls'].remove(url)
            if url in download_data['failed_urls']:
                download_data['failed_urls'].remove(url)
            if url not in download_data['downloaded_urls']:
                download_data['downloaded_urls'].append(url)
        else:
            if url not in download_data['failed_urls']:
                download_data['failed_urls'].append(url)
        
        download_data['last_processed_index'] = len(download_data['downloaded_urls'])
        
        # Update status
        if not download_data['pending_urls'] and not download_data['failed_urls']:
            download_data['status'] = 'completed'
        elif download_data['downloaded_urls']:
            download_data['status'] = 'in_progress'
        
        self.save_progress()

    def get_download_status(self, category: str, subcategory: str) -> dict:
        """Get download status for a subcategory"""
        try:
            return self.progress_data['download_progress'][category][subcategory]
        except KeyError:
            return None   

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
    
    def initialize_pattern_tracking(self, category: str, subcategory: str, pattern: str, urls: list) -> str:
        """Initialize tracking for a specific pattern"""
        try:
             # Initialize nested structure if not exists
            if 'pattern_data' not in self.progress_data:
                self.progress_data['pattern_data'] = {}
            # Initialize nested structure if not exists
            if category not in self.progress_data['pattern_data']:
                self.progress_data['pattern_data'][category] = {}
            
            if subcategory not in self.progress_data['pattern_data'][category]:
                self.progress_data['pattern_data'][category][subcategory] = {}
            
            # Generate pattern key
            pattern_key = f"pattern_{len(self.progress_data['pattern_data'][category][subcategory]) + 1}"
            
            # Create pattern entry with simplified structure
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

    # def get_pattern_status(self, category: str, subcategory: str, pattern: str) -> dict:
    #     """Get status of a specific pattern"""
    #     try:
    #         # Check if category exists
    #         if category not in self.progress_data['pattern_data']:
    #             return None
                
    #         # Check if subcategory exists
    #         if subcategory not in self.progress_data['pattern_data'][category]:
    #             return None
                
    #         # Look for pattern in subcategory
    #         subcategory_patterns = self.progress_data['pattern_data'][category][subcategory]
            
    #         # Search for pattern in all pattern entries
    #         for pattern_key, data in subcategory_patterns.items():
    #             if data.get('pattern') == pattern:
    #                 return data
                    
    #         return None
            
    #     except Exception as e:
    #         self.log_message(f"Error getting pattern status: {str(e)}")
    #         return None
    # def update_pattern_progress(self, category: str, subcategory: str, pattern_key: str, url: str, success: bool):
    #     """Update progress for a specific pattern"""
    #     try:
    #         if not self.progress_data['pattern_data'].get(category, {}).get(subcategory, {}).get(pattern_key):
    #             self.log_message(f"Pattern key {pattern_key} not found for {category}/{subcategory}")
    #             return
                
    #         pattern_data = self.progress_data['pattern_data'][category][subcategory][pattern_key]
            
    #         if success:
    #             # Move URL from pending to downloaded
    #             if url in pattern_data['urls']['pending']:
    #                 pattern_data['urls']['pending'].remove(url)
    #                 pattern_data['urls']['downloaded'].append(url)
    #                 self.progress_data['statistics']['downloaded_urls'] += 1
                    
    #                 # Remove from failed if it was there
    #                 if url in pattern_data['urls']['failed']:
    #                     pattern_data['urls']['failed'].remove(url)
                        
    #                 # Check if pattern is complete
    #                 if not pattern_data['urls']['pending']:
    #                     pattern_data['status'] = 'completed'
    #                     self.progress_data['statistics']['completed_patterns'] += 1
    #                     self.log_message(f"Pattern {pattern_key} completed for {category}/{subcategory}")
    #         else:
    #             # Add to failed if not already there
    #             if url not in pattern_data['urls']['failed']:
    #                 pattern_data['urls']['failed'].append(url)
    #                 self.progress_data['statistics']['failed_urls'] += 1
            
    #         self.save_progress()
            
    #     except Exception as e:
    #         self.log_message(f"Error updating pattern progress: {str(e)}")
    
    def update_pattern_progress(self, category: str, subcategory: str, pattern_key: str, url: str, success: bool):
        """Update progress for a specific pattern"""
        try:
            # Validate input parameters
            if not all([category, subcategory, pattern_key, url]):
                self.log_message("Missing required parameters for progress update")
                return False

            # Validate pattern exists
            if not self.progress_data['pattern_data'].get(category, {}).get(subcategory, {}).get(pattern_key):
                self.log_message(f"Pattern key {pattern_key} not found for {category}/{subcategory}")
                return False
                
            pattern_data = self.progress_data['pattern_data'][category][subcategory][pattern_key]
            
            # Log current state before update
            self.log_message(f"""
    Pattern Progress Update:
    - Category: {category}
    - Subcategory: {subcategory}
    - Pattern Key: {pattern_key}
    - URL: {url}
    - Success: {success}
    - Current Status: {pattern_data['status']}
    - Pending URLs: {len(pattern_data['urls']['pending'])}
    - Downloaded URLs: {len(pattern_data['urls']['downloaded'])}
    - Failed URLs: {len(pattern_data['urls']['failed'])}
            """)
            
            if success:
                # Move URL from pending to downloaded
                if url in pattern_data['urls']['pending']:
                    pattern_data['urls']['pending'].remove(url)
                    pattern_data['urls']['downloaded'].append(url)
                    self.progress_data['statistics']['downloaded_urls'] += 1
                    
                    # Remove from failed if it was there
                    if url in pattern_data['urls']['failed']:
                        pattern_data['urls']['failed'].remove(url)
                        
                    # Check if pattern is complete
                    if not pattern_data['urls']['pending']:
                        pattern_data['status'] = 'completed'
                        self.progress_data['statistics']['completed_patterns'] += 1
                        self.log_message(f"Pattern {pattern_key} completed for {category}/{subcategory}")
            else:
                # Add to failed if not already there
                if url not in pattern_data['urls']['failed']:
                    pattern_data['urls']['failed'].append(url)
                    self.progress_data['statistics']['failed_urls'] += 1
            
            self.save_progress()
            return True
                
        except Exception as e:
            self.log_message(f"Error updating pattern progress: {str(e)}")
            return False

    def get_pattern_status(self, category: str, subcategory: str, pattern: str) -> dict:
        """Get status of a specific pattern"""
        try:
            # Validate input parameters
            if not all([category, subcategory, pattern]):
                self.log_message("Missing required parameters for getting pattern status")
                return None
                
            # Check if category exists
            if category not in self.progress_data['pattern_data']:
                self.log_message(f"Category {category} not found in progress data")
                return None
                
            # Check if subcategory exists
            if subcategory not in self.progress_data['pattern_data'][category]:
                self.log_message(f"Subcategory {subcategory} not found in category {category}")
                return None
                
            # Look for pattern in subcategory
            subcategory_patterns = self.progress_data['pattern_data'][category][subcategory]
            
            # Search for pattern in all pattern entries
            for pattern_key, data in subcategory_patterns.items():
                if data.get('pattern') == pattern:
                    status_data = {
                        'pattern_key': pattern_key,
                        'status': data['status'],
                        'downloaded_urls': data['urls']['downloaded'],
                        'pending_urls': data['urls']['pending'],
                        'failed_urls': data['urls']['failed'],
                        'total_urls': len(data['urls']['downloaded']) + 
                                    len(data['urls']['pending']) + 
                                    len(data['urls']['failed'])
                    }
                    return status_data
                        
            self.log_message(f"Pattern {pattern} not found in {category}/{subcategory}")
            return None
                
        except Exception as e:
            self.log_message(f"Error getting pattern status: {str(e)}")
            return None

    def is_pattern_completed(self, category: str, subcategory: str, pattern: str) -> bool:
        """Check if a pattern's downloads are completed"""
        try:
            pattern_status = self.get_pattern_status(category, subcategory, pattern)
            return pattern_status and pattern_status['status']['state'] in ['completed', 'completed_with_failures']
        except Exception as e:
            self.log_message(f"Error checking pattern completion: {str(e)}")
            return False

    def get_next_pending_pattern(self, category: str, subcategory: str) -> dict:
        """Get next pattern that needs processing"""
        try:
            patterns = self.progress_data['pattern_progress'].get(category, {}).get(subcategory, {})
            for pattern_key, data in patterns.items():
                if data['status']['state'] == 'in_progress':
                    return {
                        'pattern_key': pattern_key,
                        'pattern_data': data
                    }
            return None
        except Exception as e:
            self.log_message(f"Error getting next pending pattern: {str(e)}")
            return None
        
        