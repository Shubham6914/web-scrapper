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

class ScribdScraper:
    def __init__(self):
        """Initialize the scraper with all necessary managers"""
        # Initialize config manager first
        self.config_manager = ConfigManager()
        
        # Initialize tracking and reporting
        self.download_tracker = DownloadTracker(log_file=self.config_manager.log_file)
        self.name_handler = DocumentNameHandler(self.config_manager.log_file)
        self.report_manager = DownloadReportManager()
        
        # Setup WebDriver
        self.driver = self.setup_driver()
        
        # Initialize all managers
        self.auth_manager = AuthManager(self.driver, self.config_manager)
        self.download_manager = DownloadManager(
            self.driver,
            self.config_manager,
            self.download_tracker,
            self.name_handler,
            self.report_manager
        )
        
        # Initialize search and validation components
        self.pattern_generator = SearchPatternGenerator(INSURANCE_CATEGORIES)
        self.validator = ValidationManager()
        self.progress_tracker = ProgressTracker()
        self.search_executor = SearchExecutionManager(
            self.pattern_generator.generate_all_patterns(),
            self.driver,
            self.progress_tracker,
            self.validator
        )

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

            # Execute search patterns
            search_results = self.search_executor.execute_search_sequence()
            
            if not search_results:
                self.config_manager.log_message("No search results found")
                return

            # Process search results
            self.process_search_results(search_results)

            # Print final statistics
            self.print_final_stats()

        except Exception as e:
            self.config_manager.log_message(f"Critical error in main execution: {str(e)}")
        finally:
            self.cleanup()

    def process_search_results(self, search_results):
        """Process the search results and download documents"""
        try:
            if not search_results or 'urls' not in search_results:
                self.config_manager.log_message("No search results to process")
                return
                
            urls = search_results['urls']
            self.config_manager.log_message(f"Found {len(urls)} documents to process")
            
            for url in urls:
                if self.should_process_url(url):
                    self.config_manager.log_message(f"Processing URL: {url}")
                    success = self.download_manager.download_document(url)
                    
                    if success:
                        self.mark_url_processed(url)
                        self.config_manager.log_message(f"Successfully downloaded: {url}")
                    
                    # Add delay between downloads
                    time.sleep(5)

        except Exception as e:
            self.config_manager.log_message(f"Error processing search results: {str(e)}")
            
    def should_process_url(self, url):
        """Check if URL should be processed"""
        if 'www.scribd.com/document/' not in url:
            return False
            
        # Check if URL was already processed
        processed_urls = self.load_processed_urls()
        return url not in processed_urls

    def mark_url_processed(self, url):
        """Mark URL as processed"""
        try:
            with open('processed_urls.txt', 'a') as f:
                f.write(f"{url}\n")
        except Exception as e:
            self.config_manager.log_message(f"Error marking URL as processed: {str(e)}")

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
        """Print final statistics"""
        self.download_tracker.print_stats()
        self.progress_tracker.print_progress_report()

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