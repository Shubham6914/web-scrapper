from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

from progress_tracker import ProgressTracker
from processed_url_manager import ProcessedURLManager  # New import

class SearchExecutionManager:
    def __init__(self, driver, progress_tracker=None, url_manager=None):
        """
        Initialize Search Execution Manager
        Args:
            driver: Selenium WebDriver instance
            progress_tracker: ProgressTracker instance
            url_manager: ProcessedURLManager instance
        """
        self.driver = driver
        self.progress_tracker = progress_tracker if progress_tracker else ProgressTracker()
        self.url_manager = url_manager if url_manager else ProcessedURLManager()
        
        self.search_config = {
            'wait_time': 10,
            'min_results': 2,
            'max_results': 5
        }

    def execute_search(self, category, subcategory):
        """
        Execute search for given category and subcategory
        Args:
            category: Current category
            subcategory: Current subcategory
        Returns:
            tuple: (success_status, urls_list)
        """
        try:
            print(f"\nSearching for: {category} - {subcategory}")
            search_term = f"{subcategory} {category}"
            
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
            time.sleep(3)
            
            # Get and filter URLs
            urls = self.collect_document_urls(category, subcategory)
            
            if urls:
                print(f"Found {len(urls)} new documents for {subcategory}")
                self.progress_tracker.update_search_progress(
                    category=category,
                    subcategory=subcategory,
                    success=True,
                    documents=len(urls)
                )
                return True, urls
            
            print(f"No new results found for {subcategory}")
            return False, []
            
        except Exception as e:
            print(f"Error executing search: {str(e)}")
            return False, []

    def collect_document_urls(self, category, subcategory):
        """
        Collect and filter document URLs
        Args:
            category: Current category
            subcategory: Current subcategory
        Returns:
            list: List of new document URLs
        """
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
                        not self.url_manager.is_processed(url)):  # Check if URL is new
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