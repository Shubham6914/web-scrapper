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
        self.batch_size = 10  # Process URLs in batches

    def process_subcategory(self, category: str, subcategory: str, urls: List[str], current_page: int) -> Dict:
        """
        Process URLs for a subcategory with pagination support
        Args:
            category: Current category
            subcategory: Current subcategory
            urls: List of URLs to process
            current_page: Current pagination page
        Returns:
            dict: Processing results
        """
        try:
            self.config_manager.log_message(f"\n=== Processing {category} - {subcategory} (Page {current_page}) ===")
            self.config_manager.log_message(f"URLs to process: {len(urls)}")
            
            results = {
                'total_urls': len(urls),
                'successful_downloads': 0,
                'failed_downloads': 0,
                'page': current_page
            }
            
            # Process URLs in batches
            for i in range(0, len(urls), self.batch_size):
                batch_urls = urls[i:i + self.batch_size]
                batch_results = self.process_url_batch(batch_urls, category, subcategory)
                
                results['successful_downloads'] += batch_results['successful']
                results['failed_downloads'] += batch_results['failed']
            
            # Update progress for current page
            self.config_manager.update_pagination_progress(
                category=category,
                subcategory=subcategory,
                current_page=current_page,
                urls_processed=len(urls)
            )
            
            self.log_results(category, subcategory, results)
            return results
            
        except Exception as e:
            self.config_manager.log_message(f"Error in process_subcategory: {str(e)}")
            return None
        
    def process_url_batch(self, urls: List[str], category: str, subcategory: str) -> Dict:
        """
        Process a batch of URLs
        Args:
            urls: List of URLs to process
            category: Current category
            subcategory: Current subcategory
        Returns:
            dict: Batch processing results
        """
        batch_results = {'successful': 0, 'failed': 0}
        
        for url in urls:
            try:
                self.config_manager.log_message(f"\nProcessing URL: {url}")
                success = self.download_manager.download_document(url, category, subcategory)
                
                if success:
                    batch_results['successful'] += 1
                    self.config_manager.log_message("Download successful")
                else:
                    # Retry failed download
                    retry_success = self.retry_download(url, category, subcategory)
                    if retry_success:
                        batch_results['successful'] += 1
                    else:
                        batch_results['failed'] += 1
                
                time.sleep(2)  # Delay between downloads
                
            except Exception as e:
                self.config_manager.log_message(f"Error processing URL: {str(e)}")
                batch_results['failed'] += 1
        
        return batch_results


    def retry_download(self, url: str, category: str, subcategory: str) -> bool:
        """
        Retry failed download with improved error handling
        """
        for attempt in range(self.retry_limit):
            try:
                self.config_manager.log_message(f"Retry attempt {attempt + 1} for URL: {url}")
                success = self.download_manager.download_document(url, category, subcategory)
                
                if success:
                    return True
                
                time.sleep(5 * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                self.config_manager.log_message(f"Error in retry attempt {attempt + 1}: {str(e)}")
                time.sleep(5 * (attempt + 1))
        
        return False

    def log_results(self, category: str, subcategory: str, results: Dict):
        """
        Log processing results with pagination information
        """
        summary = f"""
        === Processing Summary: {category} - {subcategory} (Page {results['page']}) ===
        Total URLs: {results['total_urls']}
        Successful Downloads: {results['successful_downloads']}
        Failed Downloads: {results['failed_downloads']}
        Success Rate: {(results['successful_downloads'] / results['total_urls']) * 100:.2f}%
        ===============================================
        """
        self.config_manager.log_message(summary)
        
        
    def check_completion_status(self, category: str, subcategory: str, total_pages_processed: int) -> bool:
        """
        Check if subcategory processing is complete
        Args:
            category: Current category
            subcategory: Current subcategory
            total_pages_processed: Number of pages processed
        Returns:
            bool: Completion status
        """
        try:
            max_pages = self.config_manager.pagination_config['max_pages']
            is_complete = total_pages_processed >= max_pages
            
            if is_complete:
                self.progress_tracker.mark_subcategory_complete(category, subcategory)
                self.config_manager.log_message(f"Completed processing {category}/{subcategory} after {total_pages_processed} pages")
            
            return is_complete
            
        except Exception as e:
            self.config_manager.log_message(f"Error checking completion status: {str(e)}")
            return False