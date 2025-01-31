import json
import os
import time
from typing import Dict, List, Any
class CategoryProcessor:
    def __init__(self, config_manager, download_manager, progress_tracker):
        """
        Initialize Category Processor
        Args:
            config_manager: ConfigManager instance
            download_manager: DownloadManager instance
            progress_tracker: ProgressTracker instance
        """
        self.config_manager = config_manager
        self.download_manager = download_manager
        self.progress_tracker = progress_tracker
        self.retry_limit = 2

    def process_subcategory(self, category: str, subcategory: str, urls: List[str]) -> Dict:
        """
        Process URLs for a subcategory
        Args:
            category: Current category
            subcategory: Current subcategory
            urls: List of URLs to process
        Returns:
            dict: Processing results
        """
        try:
            self.config_manager.log_message(f"\n=== Processing {category} - {subcategory} ===")
            self.config_manager.log_message(f"URLs to process: {len(urls)}")
            
            results = {
                'total_urls': len(urls),
                'successful_downloads': 0,
                'failed_downloads': 0
            }
            
            for url in urls:
                try:
                    self.config_manager.log_message(f"\nProcessing URL: {url}")
                    success = self.download_manager.download_document(url, category, subcategory)
                    
                    if success:
                        results['successful_downloads'] += 1
                        self.config_manager.log_message("Download successful")
                    else:
                        # Retry failed download
                        retry_success = self.retry_download(url, category, subcategory)
                        if retry_success:
                            results['successful_downloads'] += 1
                        else:
                            results['failed_downloads'] += 1
                    
                    time.sleep(2)  # Delay between downloads
                    
                except Exception as e:
                    self.config_manager.log_message(f"Error processing URL: {str(e)}")
                    results['failed_downloads'] += 1
            
            # Update progress
            if results['successful_downloads'] > 0:
                self.progress_tracker.mark_subcategory_complete(category, subcategory)
            
            self.log_results(category, subcategory, results)
            return results
            
        except Exception as e:
            self.config_manager.log_message(f"Error in process_subcategory: {str(e)}")
            return None

    def retry_download(self, url: str, category: str, subcategory: str) -> bool:
        """
        Retry failed download
        Args:
            url: URL to retry
            category: Current category
            subcategory: Current subcategory
        Returns:
            bool: Success status
        """
        for attempt in range(self.retry_limit):
            self.config_manager.log_message(f"Retry attempt {attempt + 1} for URL: {url}")
            success = self.download_manager.download_document(url, category, subcategory)
            
            if success:
                return True
                
            time.sleep(5)
        
        return False

    def log_results(self, category: str, subcategory: str, results: Dict):
        """
        Log processing results
        Args:
            category: Current category
            subcategory: Current subcategory
            results: Processing results
        """
        summary = f"""
        === Processing Summary: {category} - {subcategory} ===
        Total URLs: {results['total_urls']}
        Successful Downloads: {results['successful_downloads']}
        Failed Downloads: {results['failed_downloads']}
        Success Rate: {(results['successful_downloads'] / results['total_urls']) * 100:.2f}%
        ===============================================
        """
        self.config_manager.log_message(summary)