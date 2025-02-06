"""
ScribdScraper: Main class that manages sequential category-subcategory based scraping
with organized directory structure and simplified search mechanism.
"""
import traceback
from selenium.webdriver.remote.webdriver import WebDriver
import time

# Import managers
from config_manager import ConfigManager
from auth_manager import AuthManager
from download_manager import DownloadManager
from search_generator import SearchMechanism
from SearchExecutionManager import SearchExecutionManager
from ProgressTracker import ProgressTracker

# Import utilities
from insurance_data import INSURANCE_CATEGORIES
from file_naming_convention import DocumentNameHandler
from category_processor import CategoryProcessor
from ProcessedURLManager import ProcessedURLManager
from report import DownloadReportManager


class ScribdScraper:
    def __init__(self):
        """Initialize the scraper with all necessary components"""
        try:
            # Initialize config manager first
            self.config_manager = ConfigManager()
            
            # Initialize progress tracker first (since other components depend on it)
            self.progress_tracker = ProgressTracker(self.config_manager.log_dir)
            
            # Initialize category tracking
            self.progress_tracker.initialize_category_tracking(INSURANCE_CATEGORIES)
            
            # Get resume point
            resume_point = self.progress_tracker.get_resume_point()
            
            # Initialize tracking and management components
            self.name_handler = DocumentNameHandler(self.config_manager.log_file)
            self.url_manager = ProcessedURLManager(
                log_file=self.config_manager.log_file
            )
            self.report_manager = DownloadReportManager(
            excel_file='download_reports.xlsx',
            spreadsheet_id='1sbKp5Xa_NPd5Bp6MbaS_eaLlgLzsdX_t3jcms3zgXQ4'
            )
                    
            # Setup WebDriver
            self.driver = self.setup_driver()
            
            # Initialize core managers
            self.auth_manager = AuthManager(self.driver, self.config_manager)
            
            
            # Initialize search components
            self.search_mechanism = SearchMechanism(INSURANCE_CATEGORIES)
            current_search = self.search_mechanism.initialize_search(resume_point)
            self.search_executor = SearchExecutionManager(
                driver=self.driver,
                progress_tracker=self.progress_tracker,  # Explicitly name the parameter
                config_manager = self.config_manager,
                url_manager=self.url_manager
            )
            self.download_manager = DownloadManager(
                self.driver,
                self.config_manager,
                self.name_handler,
                self.progress_tracker,
                self.url_manager,
                self.report_manager,
                self.search_executor
            )

            # Log successful initialization
            self.config_manager.log_message("All components initialized successfully")

        except Exception as e:
            error_msg = f"Error initializing ScribdScraper: {str(e)}"
            if hasattr(self, 'config_manager'):
                self.config_manager.log_message(error_msg)
            print(error_msg)
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

            # Get resume point
            resume_point = self.progress_tracker.get_resume_point()
            current_search = self.search_mechanism.initialize_search(resume_point)
            
            while current_search:
                try:
                    category = current_search['category']
                    subcategory = current_search['subcategory']
                    search_term = current_search['search_term']
                    
                    # Update progress tracker position
                    self.progress_tracker.update_position(
                        category=category,
                        subcategory=subcategory,
                        category_index=current_search['category_index'],
                        subcategory_index=current_search['subcategory_index']
                    )
                    
                    # Check if subcategory is already complete
                    if self.progress_tracker.is_subcategory_complete(category, subcategory):
                        self.config_manager.log_message(f"Subcategory {subcategory} already completed, skipping...")
                        current_search = self.search_mechanism.move_to_next()
                        continue
                    
                    self.config_manager.log_message(f"\n=== Processing: {category} - {subcategory} ===")
                    self.config_manager.log_message(f"Search term: {search_term}")
                    
                    # Setup directories
                    self.config_manager.setup_category_directory(category)
                    current_dir = self.config_manager.setup_subcategory_directory(category, subcategory)
                    
                    # Execute search
                    search_success, found_urls = self.search_executor.execute_search_with_retries(
                        category,
                        subcategory,
                        search_term
                    )
                    
                    if search_success and found_urls:
                        self.config_manager.log_message(f"Found {len(found_urls)} URLs to process")
                        current_downloads = 0
                        required_downloads = 5
                        
                        for url in found_urls:
                            if self.url_manager.is_processed(url):
                                continue
                                
                            success = self.download_manager.download_document(
                                url,
                                category,
                                subcategory
                            )
                            
                            if success:
                                current_downloads += 1
                                # Don't record download here since it's already done in download_manager
                                
                                # Check if we've reached 2 downloads
                                if current_downloads >= required_downloads:
                                    self.progress_tracker.mark_subcategory_complete(category, subcategory)
                                    break
                            
                            time.sleep(2)
                    
                    # Move to next search item
                    current_search = self.search_mechanism.move_to_next()
                    time.sleep(3)
                    
                    # Check category completion
                    if current_search and current_search.get('is_last_subcategory'):
                        if self.progress_tracker.is_category_complete(category):
                            self.progress_tracker.check_category_completion(category)
                            self.config_manager.log_message(f"Completed category: {category}")
                    
                    time.sleep(3)
                    
                except Exception as e:
                    self.config_manager.log_message(f"Error processing search: {str(e)}")
                    current_search = self.search_mechanism.move_to_next()
                    continue

            # Print final statistics
            self.print_final_stats()

        except Exception as e:
            self.config_manager.log_message(f"Critical error in main execution: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
        finally:
            self.cleanup()

    def print_interim_stats(self, category, subcategory):
        """Print interim statistics"""
        try:
            progress = self.search_mechanism.get_search_progress()
            url_stats = self.url_manager.get_stats()
            download_stats = self.progress_tracker.get_daily_count()
            
            stats = f"""
            === Progress Report: {category} - {subcategory} ===
            Processed Categories: {progress['processed_categories']}/{progress['total_categories']}
            Processed Subcategories: {progress['processed_subcategories']}/{progress['total_subcategories']}
            URLs Processed: {url_stats['total_urls']}
            Today's Downloads: {download_stats}
            Completion: {progress['completion_percentage']:.2f}%
            ===============================================
            """
            self.config_manager.log_message(stats)
        except Exception as e:
            self.config_manager.log_message(f"Error printing interim stats: {str(e)}")

    def print_final_stats(self):
        """Print final processing statistics"""
        try:
            progress = self.search_mechanism.get_search_progress()
            url_stats = self.url_manager.get_stats()
            download_stats = self.progress_tracker.print_stats()
            
            final_stats = f"""
            === Final Processing Statistics ===
            Categories Processed: {progress['processed_categories']}/{progress['total_categories']}
            Subcategories Processed: {progress['processed_subcategories']}/{progress['total_subcategories']}
            Total URLs Processed: {url_stats['total_urls']}
            
            Download Statistics:
            {download_stats}
            
            URL Processing by Category:
            """
            
            for category, cat_stats in url_stats['categories'].items():
                final_stats += f"\n{category}: {cat_stats['total']} URLs"
                for subcat, count in cat_stats['subcategories'].items():
                    final_stats += f"\n  - {subcat}: {count} URLs"
            
            self.config_manager.log_message(final_stats)
        except Exception as e:
            self.config_manager.log_message(f"Error printing final stats: {str(e)}")

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.driver.quit()
            self.url_manager.cleanup()
            self.config_manager.log_message("Browser session ended, log file closed.")
        except Exception as e:
            self.config_manager.log_message(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    scraper = ScribdScraper()
    scraper.run()