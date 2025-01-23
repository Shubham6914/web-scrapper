import json
import os
import time
from typing import Dict, List, Any

class CategoryProcessor:
    def __init__(self, config_manager, download_manager, progress_tracker):
        """
        Initialize Category Processor
        
        Parameters:
        - config_manager: ConfigManager instance
        - download_manager: DownloadManager instance
        - progress_tracker: ProgressTracker instance
        """
        self.config_manager = config_manager
        self.download_manager = download_manager
        self.progress_tracker = progress_tracker
        self.retry_limit = 2
        self.category_progress = {}
        
        # Create category logs directory
        self.category_logs_dir = os.path.join('logs', 'categories')
        if not os.path.exists(self.category_logs_dir):
            os.makedirs(self.category_logs_dir)

    def initialize_category_progress(self, category: str) -> str:
        """
        Initialize progress tracking for a category
        
        Parameters:
        - category: Category name
        
        Returns:
        - Path to progress file
        """
        progress_file = os.path.join(self.category_logs_dir, f'{category}_progress.json')
        self.category_progress = {
            'category': category,
            'timestamp_started': self.progress_tracker.get_timestamp(),
            'urls_collected': [],
            'downloads_completed': [],
            'downloads_failed': [],
            'retry_attempts': {},
            'status': 'in_progress'
        }
        return progress_file

    def process_category_urls(self, category: str, subcategory: str, urls: List[str]) -> Dict:
        """Process URLs for a subcategory"""
        try:
            print(f"\n=== Processing {category} - {subcategory} ===")
            
            # Initialize or get download tracking
            download_status = self.progress_tracker.initialize_download_tracking(
                category, subcategory, urls
            )
            
            # Get pending URLs
            pending_urls = download_status['pending_urls']
            failed_urls = download_status['failed_urls']
            
            print(f"Total URLs: {len(urls)}")
            print(f"Already downloaded: {len(download_status['downloaded_urls'])}")
            print(f"Pending downloads: {len(pending_urls)}")
            print(f"Failed downloads: {len(failed_urls)}")
            
            # Process pending URLs
            for url in pending_urls[:]:  # Create copy to iterate
                try:
                    print(f"\nProcessing URL: {url}")
                    success = self.download_manager.download_document(url)
                    
                    # Update progress
                    self.progress_tracker.update_download_progress(
                        category, subcategory, url, success
                    )
                    
                    if success:
                        print("Download successful")
                    else:
                        print("Download failed")
                    
                    time.sleep(2)  # Delay between downloads
                    
                except Exception as e:
                    print(f"Error processing URL {url}: {str(e)}")
                    self.progress_tracker.update_download_progress(
                        category, subcategory, url, False
                    )
            
            # Retry failed downloads
            if failed_urls:
                print("\n=== Retrying Failed Downloads ===")
                retry_urls = self.retry_failed_downloads(
                    category, subcategory, failed_urls
                )
            
            # Get final status
            final_status = self.progress_tracker.get_download_status(
                category, subcategory
            )
            
            return final_status
            
        except Exception as e:
            print(f"Error in process_category_urls: {str(e)}")
            return None

    def retry_failed_downloads(self, category: str, subcategory: str, failed_urls: List[str]) -> List[str]:
        """Retry failed downloads"""
        still_failed = []
        
        for url in failed_urls:
            retry_count = 0
            while retry_count < self.retry_limit:
                print(f"Retry attempt {retry_count + 1} for URL: {url}")
                success = self.download_manager.download_document(url)
                
                if success:
                    self.progress_tracker.update_download_progress(
                        category, subcategory, url, True
                    )
                    break
                    
                retry_count += 1
                time.sleep(5)
            
            if retry_count == self.retry_limit:
                still_failed.append(url)
        
        return still_failed

    def save_category_progress(self, progress_file: str):
        """
        Save category progress to file
        
        Parameters:
        - progress_file: Path to progress file
        """
        try:
            with open(progress_file, 'w') as f:
                json.dump(self.category_progress, f, indent=4)
            self.config_manager.log_message(f"Category progress saved to {progress_file}")
        except Exception as e:
            self.config_manager.log_message(f"Error saving category progress: {str(e)}")

    def generate_category_report(self, category: str) -> Dict:
        """
        Generate report for category
        
        Parameters:
        - category: Category name
        
        Returns:
        - Dictionary containing category processing statistics
        """
        timestamp_completed = self.progress_tracker.get_timestamp()
        
        report = {
            'category': category,
            'timestamp_started': self.category_progress['timestamp_started'],
            'timestamp_completed': timestamp_completed,
            'total_urls': len(self.category_progress['urls_collected']),
            'successful_downloads': len(self.category_progress['downloads_completed']),
            'failed_downloads': len(self.category_progress['downloads_failed']),
            'final_failures': len(self.category_progress.get('retry_failures', [])),
            'retry_attempts': self.category_progress['retry_attempts'],
            'status': 'completed'
        }
        
        self.config_manager.log_message(f"Category Report for {category}:")
        self.config_manager.log_message(json.dumps(report, indent=2))
        
        return report