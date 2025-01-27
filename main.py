# main.py
"""
    Single ScribdScraper class that manages all components
Clear initialization sequence
Organized execution flow
Proper error handling and logging
Resource cleanup

    Returns:
        _type_: _description_
"""
from selenium.webdriver.remote.webdriver import WebDriver
import time

# Import our managers
from config_manager import ConfigManager
from auth_manager import AuthManager
from download_manager import DownloadManager
from search_pattern_generator import SearchPatternGenerator
from SearchExecutionManager import SearchExecutionManager
from ValidationManager import ValidationManager
from ProgressTracker import ProgressTracker

# Import data and existing utilities
from insurance_data import INSURANCE_CATEGORIES
from file_count_tracker import DownloadTracker
from file_naming_convention import DocumentNameHandler
from report import DownloadReportManager
from category_processor import CategoryProcessor

class ScribdScraper:
    def __init__(self):
        """Initialize the scraper with all necessary managers"""
        try:
            # Initialize config manager first
            self.config_manager = ConfigManager()
            
            # Initialize tracking and reporting
            self.download_tracker = DownloadTracker(log_file=self.config_manager.log_file)
            self.name_handler = DocumentNameHandler(self.config_manager.log_file)
            self.report_manager = DownloadReportManager()
            
            # Initialize progress tracker early
            self.progress_tracker = ProgressTracker()  # Moved up
            
            # Setup WebDriver
            self.driver = self.setup_driver()
            
            # Initialize all managers
            self.auth_manager = AuthManager(self.driver, self.config_manager)
            self.download_manager = DownloadManager(
                self.driver,
                self.config_manager,
                self.download_tracker,
                self.name_handler,
                self.report_manager,
                self.progress_tracker  # Now progress_tracker exists
            )
            
            # Initialize search and validation components
            self.pattern_generator = SearchPatternGenerator(INSURANCE_CATEGORIES)
            self.validator = ValidationManager()
            
            # Initialize category processor
            self.category_processor = CategoryProcessor(
                self.config_manager,
                self.download_manager,
                self.progress_tracker  # Now progress_tracker exists
            )
            
            # Initialize search executor
            self.search_executor = SearchExecutionManager(
                self.pattern_generator.generate_all_patterns(),
                self.driver,
                self.progress_tracker,
                self.validator
            )

        except Exception as e:
            print(f"Error initializing ScribdScraper: {str(e)}")
            raise

    def setup_driver(self):
        """Setup and return WebDriver"""
        try:
            selenium_grid_url = "http://localhost:4444"
            driver = WebDriver(
                command_executor=selenium_grid_url,
                options=self.config_manager.get_chrome_options()
            )
            return driver
        except Exception as e:
            self.config_manager.log_message(f"Error setting up WebDriver: {str(e)}")
            raise

    def run(self):
        """Main execution method"""
        try:
            # Start browser session
            self.driver.get('https://www.scribd.com')
            self.config_manager.log_message("Started browser session")

            # Perform login
            if not self.auth_manager.ensure_login():
                self.config_manager.log_message("Failed to login, stopping execution")
                return

            # Continuous processing loop
            while True:
                try:
                    # Check for in-progress patterns first
                    resume_point = self.progress_tracker.get_resume_point()

                    if resume_point.get('status') == 'resume' and resume_point.get('pending_urls'):
                        # Resume downloading pending URLs
                        self.config_manager.log_message("\n=== Resuming previous pattern... ===")
                        self.config_manager.log_message(f"Category: {resume_point['category']}")
                        self.config_manager.log_message(f"Subcategory: {resume_point['subcategory']}")
                        self.config_manager.log_message(f"Pending URLs: {len(resume_point['pending_urls'])}")

                        downloaded_count = 0
                        for idx, url in enumerate(resume_point['pending_urls']):
                            try:
                                self.config_manager.log_message(f"Processing pending URL {idx + 1}/{len(resume_point['pending_urls'])}")
                                success = self.download_manager.download_document(
                                    url,
                                    category=resume_point['category'],
                                    subcategory=resume_point['subcategory'],
                                    pattern=resume_point['pattern'],
                                    pattern_key=resume_point['pattern_key']
                                )

                                if success:
                                    downloaded_count += 1
                                    self.config_manager.log_message(f"Successfully downloaded {downloaded_count}/5 documents for this pattern")

                                self.progress_tracker.update_pattern_progress(
                                    category=resume_point['category'],
                                    subcategory=resume_point['subcategory'],
                                    pattern_key=resume_point['pattern_key'],
                                    url=url,
                                    success=success
                                )

                                if downloaded_count >= 5:
                                    self.config_manager.log_message("Reached 5 downloads limit, moving to next pattern")
                                    break

                                time.sleep(2)

                            except Exception as e:
                                self.config_manager.log_message(f"Error processing pending URL: {str(e)}")
                                continue

                        continue

                    # Execute search patterns if no pending downloads
                    self.config_manager.log_message("\n=== Starting search execution... ===")
                    search_results = self.search_executor.execute_search_sequence()

                    if not search_results:
                        self.config_manager.log_message("All patterns processed")
                        break

                    # Extract pattern information
                    category = search_results['category']
                    subcategory = search_results['subcategory']
                    pattern = search_results['pattern']
                    pattern_index = search_results['pattern_index']
                    urls = search_results['urls']

                    self.config_manager.log_message(f"\nProcessing Pattern:")
                    self.config_manager.log_message(f"Category: {category}")
                    self.config_manager.log_message(f"Subcategory: {subcategory}")
                    self.config_manager.log_message(f"Pattern: {pattern}")
                    self.config_manager.log_message(f"URLs found: {len(urls)}")

                    if urls:
                        # Initialize pattern tracking
                        pattern_key = self.progress_tracker.initialize_pattern_tracking(
                            category, subcategory, pattern, urls
                        )

                        # Process URLs for this pattern
                        self.config_manager.log_message("\nStarting downloads for pattern...")
                        downloaded_count = 0

                        for idx, url in enumerate(urls):
                            try:
                                self.config_manager.log_message(f"Processing URL {idx + 1}/{len(urls)}")
                                success = self.download_manager.download_document(
                                    url,
                                    category=category,
                                    subcategory=subcategory,
                                    pattern=pattern,
                                    pattern_key=pattern_key
                                )

                                if success:
                                    downloaded_count += 1
                                    self.config_manager.log_message(f"Successfully downloaded {downloaded_count}/5 documents for this pattern")

                                self.progress_tracker.update_pattern_progress(
                                    category=category,
                                    subcategory=subcategory,
                                    pattern_key=pattern_key,
                                    url=url,
                                    success=success
                                )

                                if downloaded_count >= 5:
                                    self.config_manager.log_message("Reached 5 downloads limit, moving to next pattern")
                                    # Mark current pattern as completed
                                    self.progress_tracker.update_pattern_progress(
                                        category=category,
                                        subcategory=subcategory,
                                        pattern_key=pattern_key,
                                        url=url,
                                        success=True
                                    )
                                    break

                                time.sleep(2)

                            except Exception as e:
                                self.config_manager.log_message(f"Error downloading URL: {str(e)}")
                                continue

                        # Add delay before next pattern
                        self.config_manager.log_message("\nWaiting before next pattern...")
                        time.sleep(5)

                except Exception as e:
                    self.config_manager.log_message(f"Error processing pattern: {str(e)}")
                    self.config_manager.log_message("Attempting to continue with next pattern...")
                    continue

            # Print final statistics
            self.config_manager.log_message("\n=== Processing Completed ===")
            self.print_final_stats()

        except Exception as e:
            self.config_manager.log_message(f"Critical error in main execution: {str(e)}")
            import traceback
            self.config_manager.log_message(f"Error traceback: {traceback.format_exc()}")
        finally:
            self.config_manager.log_message("Starting cleanup...")
            self.cleanup()
            self.config_manager.log_message("Cleanup completed")
            
    def process_search_results(self, search_results):
        """Process the search results and download documents"""
        try:
            self.config_manager.log_message("Starting to process search results")
            
            if not search_results or not isinstance(search_results, dict):
                self.config_manager.log_message("Invalid search results format")
                return
            
            category = search_results.get('category')
            urls = search_results.get('urls', [])
            
            if not category or not urls:
                self.config_manager.log_message("Missing category or URLs in search results")
                return
            
            self.config_manager.log_message(f"Processing category: {category}")
            self.config_manager.log_message(f"Total URLs to process: {len(urls)}")
            
            # Process category using CategoryProcessor
            try:
                category_report = self.category_processor.process_category_urls(category, urls)
                
                # Log category processing results
                self.config_manager.log_message("\n=== Category Processing Report ===")
                self.config_manager.log_message(f"Category: {category}")
                self.config_manager.log_message(f"Total URLs: {category_report['total_urls']}")
                self.config_manager.log_message(f"Successful Downloads: {category_report['successful_downloads']}")
                self.config_manager.log_message(f"Failed Downloads: {category_report['failed_downloads']}")
                self.config_manager.log_message(f"Final Failures: {category_report['final_failures']}")
                
                # Handle any remaining failed downloads
                if category_report['final_failures'] > 0:
                    self.config_manager.log_message(
                        f"Warning: {category_report['final_failures']} URLs failed all download attempts"
                    )
                
                return category_report
                
            except Exception as e:
                self.config_manager.log_message(f"Error processing category {category}: {str(e)}")
                return None

        except Exception as e:
            self.config_manager.log_message(f"Critical error in process_search_results: {str(e)}")
            import traceback
            self.config_manager.log_message(f"Error traceback: {traceback.format_exc()}")
            return None

    def load_processed_urls(self):
        """Load previously processed URLs"""
        try:
            with open('processed_urls.txt', 'r') as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            return []
        except Exception as e:
            self.config_manager.log_message(f"Error loading processed URLs: {str(e)}")
            return []

    def print_final_stats(self):
        """Print final processing statistics"""
        try:
            stats = self.progress_tracker.get_progress_summary()
            final_stats = f"""
            === Final Processing Statistics ===
            Total Searches: {stats['statistics']['total_searches']}
            Successful Searches: {stats['statistics']['successful_searches']}
            Failed Searches: {stats['statistics']['failed_searches']}
            Documents Found: {stats['statistics']['documents_found']}
            Completed Categories: {stats['completed_categories']}/{stats['total_categories']}
            ================================
            """
            self.config_manager.log_message(final_stats)
        except Exception as e:
            self.config_manager.log_message(f"Error printing final stats: {str(e)}")

    
    def print_interim_stats(self, category, subcategory):
        """Print interim statistics for current subcategory"""
        try:
            download_status = self.progress_tracker.get_download_status(category, subcategory)
            if download_status:
                stats = f"""
            === Interim Statistics: {category} - {subcategory} ===
            Total URLs: {download_status['total_urls']}
            Downloaded: {len(download_status['downloaded_urls'])}
            Pending: {len(download_status['pending_urls'])}
            Failed: {len(download_status['failed_urls'])}
            Status: {download_status['status']}
            ================================================
            """
                self.config_manager.log_message(stats)
        except Exception as e:
            self.config_manager.log_message(f"Error printing interim stats: {str(e)}")
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.driver.quit()
            self.config_manager.log_message("Browser session ended, log file closed.")
        except Exception as e:
            self.config_manager.log_message(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    scraper = ScribdScraper()
    scraper.run()