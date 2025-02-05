from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

from ProgressTracker import ProgressTracker
from ProcessedURLManager import ProcessedURLManager  # New import

class SearchExecutionManager:
    def __init__(self, driver,config_manager, progress_tracker=None, url_manager=None,):
        """
        Initialize Search Execution Manager
        Args:
            driver: Selenium WebDriver instance
            progress_tracker: ProgressTracker instance
            url_manager: ProcessedURLManager instance
        """
        self.driver = driver
        self.config_manager = config_manager
        self.progress_tracker = progress_tracker if progress_tracker else ProgressTracker()
        self.url_manager = url_manager if url_manager else ProcessedURLManager()
        
        self.search_config = {
            'wait_time': 10,
            'min_results': 2,
            'max_results': 5,
            'search_delay': 3
        }

    def execute_search_with_retries(self, category, subcategory, search_term, max_attempts=3):
        """
        Execute search with retries
        Args:
            category: Current category
            subcategory: Current subcategory
            search_term: Term to search
            max_attempts: Maximum number of retry attempts
        Returns:
            tuple: (success_status, urls_list)
        """
        self.config_manager.log_message(f"\n=== Starting search for {category}/{subcategory} ===")
        
        for attempt in range(max_attempts):
            try:
                self.config_manager.log_message(f"Attempt {attempt + 1} of {max_attempts}")
                
                success, urls = self.execute_single_search(category, subcategory, search_term)
                
                if success and urls:
                    self.config_manager.log_message(f"Successfully found URLs on attempt {attempt + 1}")
                    return True, urls
                
                # If not successful and not last attempt, wait before retry
                if attempt < max_attempts - 1:
                    self.config_manager.log_message(f"No URLs found, waiting before retry...")
                    time.sleep(5)  # Wait between attempts
                
            except Exception as e:
                self.config_manager.log_message(f"Error in search attempt {attempt + 1}: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(5)  # Wait before retry
        
        self.config_manager.log_message(f"No URLs found after {max_attempts} attempts")
        return False, []

    def execute_single_search(self, category, subcategory, search_term):
        """
        Execute single search attempt
        Args:
            category: Current category
            subcategory: Current subcategory
            search_term: Term to search
        Returns:
            tuple: (success_status, urls_list)
        """
        try:
            self.config_manager.log_message(f"Executing search with term: {search_term}")
            print(f"\nSearching for: {search_term}")
            print(f"Category: {category}, Subcategory: {subcategory}")
            
            # Navigate to search page
            self.driver.get('https://www.scribd.com/search')
            
            # Find and clear search input
            search_input = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
            )
            search_input.clear()
            
            # Input search term
            search_input.send_keys(search_term)
            search_input.send_keys(Keys.RETURN)
            
            # Wait for results
            time.sleep(self.search_config['search_delay'])
            
            # Get and filter URLs
            urls = self.collect_document_urls(category, subcategory)
            
            if urls:
                self.config_manager.log_message(f"Found {len(urls)} URLs: {urls}")
                print(f"Found {len(urls)} new documents")
                self.progress_tracker.update_search_progress(
                    category=category,
                    subcategory=subcategory,
                    success=True
                )
                return True, urls
            
            self.config_manager.log_message("No URLs found in search results")
            print("No new results found")
            self.progress_tracker.update_search_progress(
                category=category,
                subcategory=subcategory,
                success=False
            )
            return False, []
            
        except Exception as e:
            self.config_manager.log_message(f"Error executing search: {str(e)}")
            return False, []
            
    def collect_document_urls(self, category, subcategory):
        """Collect and filter document URLs"""
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]'
            )
            
            new_urls = []
            for element in elements:
                try:
                    url = element.get_attribute('href')
                    if (url and 
                        'www.scribd.com/document/' in url and 
                        not self.url_manager.is_processed(url)):
                        new_urls.append(url)
                        
                        if len(new_urls) >= self.search_config['max_results']:
                            break
                            
                except Exception as e:
                    print(f"Error getting URL: {str(e)}")
                    continue
                    
            return new_urls
            
        except Exception as e:
            print(f"Error collecting URLs: {str(e)}")
            return []

    def validate_results(self, category, subcategory):
        """
        Validate search results
        Args:
            category: Current category
            subcategory: Current subcategory
        Returns:
            bool: Validation status
        """
        try:
            results_container = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="search-results"]'))
            )
            
            # Check for no results
            try:
                no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results for')]")
                if no_results:
                    return False
            except:
                pass
            
            # Get all results
            results = results_container.find_elements(By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]')
            
            # Filter out processed URLs
            new_results = [
                result for result in results 
                if not self.url_manager.is_processed(result.get_attribute('href'))
            ]
            
            return len(new_results) >= self.search_config['min_results']
            
        except Exception as e:
            print(f"Error validating results: {str(e)}")
            return False

    def mark_url_processed(self, url, category, subcategory):
        """
        Mark URL as processed after successful download
        Args:
            url: Processed URL
            category: Current category
            subcategory: Current subcategory
        """
        try:
            self.url_manager.add_url(category, subcategory, url)
        except Exception as e:
            print(f"Error marking URL as processed: {str(e)}")

    def get_processed_stats(self):
        """
        Get statistics about processed URLs
        Returns:
            dict: URL processing statistics
        """
        return self.url_manager.get_stats()