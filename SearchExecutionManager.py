from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

from ProgressTracker import ProgressTracker
from ProcessedURLManager import ProcessedURLManager  # New import

class SearchExecutionManager:
    from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class SearchExecutionManager:
    def __init__(self, driver, config_manager, progress_tracker=None, url_manager=None):
        """
        Initialize Search Execution Manager with pagination support
        """
        self.driver = driver
        self.config_manager = config_manager
        self.progress_tracker = progress_tracker
        self.url_manager = url_manager
        
        # Updated search configuration without result limits
        self.search_config = {
            'wait_time': 10,
            'search_delay': 3,
            'max_page_limit': 5  # New: Maximum pages to process
        }
        
        # New: Pagination tracking
        self.current_page = 1
        
        # New: Pagination selectors
        self.pagination_selectors = {
            'next_button': 'button[data-e2e="pagination_next"]',  # Update with correct selector
            'results_container': 'div[class*="search-results"]'
        }

    def execute_search_with_retries(self, category, subcategory, search_term, max_attempts=3):
        """
        Execute search with retries using direct URL pagination and page-wise downloading
        """
        self.config_manager.log_message(f"\n=== Starting search for {category}/{subcategory} ===")
        
        for attempt in range(max_attempts):
            try:
                self.config_manager.log_message(f"Attempt {attempt + 1} of {max_attempts}")
                
                # Process pages using direct URL pagination
                for page in range(1, self.search_config['max_page_limit'] + 1):
                    self.config_manager.log_message(f"\nProcessing page {page}")
                    
                    # Construct search URL with page number
                    search_url = f'https://www.scribd.com/search?query={search_term}&page={page}'
                    self.config_manager.log_message(f"Navigating to: {search_url}")
                    
                    # Navigate to search URL
                    self.driver.get(search_url)
                    time.sleep(self.search_config['search_delay'])
                    
                    # Check for no results
                    try:
                        no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results for')]")
                        if no_results:
                            self.config_manager.log_message(f"No results found on page {page}, ending search.")
                            return False, []
                    except:
                        pass
                    
                    # Collect URLs from current page
                    page_urls = self.collect_document_urls(category, subcategory)
                    
                    if page_urls:
                        self.config_manager.log_message(f"Found {len(page_urls)} URLs on page {page}")
                        
                        # Process all URLs from current page before moving to next page
                        self.config_manager.log_message(f"Processing downloads for page {page}")
                        for url in page_urls:
                            if self.url_manager.is_processed(url):
                                self.config_manager.log_message(f"URL already processed: {url}")
                                continue
                                
                            # Download current URL
                            success = self.download_manager.download_document(
                                url,
                                category,
                                subcategory
                            )
                            
                            if success:
                                self.config_manager.log_message(f"Successfully downloaded: {url}")
                            else:
                                self.config_manager.log_message(f"Failed to download: {url}")
                            
                            time.sleep(2)  # Delay between downloads
                        
                        self.config_manager.log_message(f"Completed processing all URLs from page {page}")
                    else:
                        self.config_manager.log_message(f"No URLs found on page {page}, ending search.")
                        break
                    
                    # Add delay before moving to next page
                    if page < self.search_config['max_page_limit']:
                        time.sleep(self.search_config['search_delay'])
                
                # Successfully completed all pages
                return True, []
                
            except Exception as e:
                self.config_manager.log_message(f"Error in search attempt {attempt + 1}: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
        
        return False, []
    def execute_single_search(self, category, subcategory, search_term, is_pagination=False):
        """
        Execute single search attempt with pagination support
        """
        try:
            if not is_pagination:
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
            
            # Get URLs from current page
            urls = self.collect_document_urls(category, subcategory)
            
            if urls:
                self.config_manager.log_message(f"Found {len(urls)} URLs on page {self.current_page}")
                print(f"Found {len(urls)} documents on page {self.current_page}")
                return True, urls
            
            self.config_manager.log_message(f"No URLs found on page {self.current_page}")
            return False, []
            
        except Exception as e:
            self.config_manager.log_message(f"Error executing search: {str(e)}")
            return False, []

    def collect_document_urls(self, category, subcategory):
        """Collect all document URLs from current page"""
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]'
            )
            
            page_urls = []
            for element in elements:
                try:
                    url = element.get_attribute('href')
                    if (url and 
                        'www.scribd.com/document/' in url and 
                        not self.url_manager.is_processed(url)):
                        page_urls.append(url)
                            
                except Exception as e:
                    print(f"Error getting URL: {str(e)}")
                    continue
                    
            return page_urls
            
        except Exception as e:
            print(f"Error collecting URLs: {str(e)}")
            return []

    def check_for_next_page(self):
        """Check if next page exists"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, self.pagination_selectors['next_button'])
            is_enabled = next_button.is_enabled()
            has_disabled_class = 'disabled' in next_button.get_attribute('class')
            
            self.config_manager.log_message(f"Next button found: Enabled={is_enabled}, Has disabled class={has_disabled_class}")
            
            return is_enabled and not has_disabled_class
        except Exception as e:
            self.config_manager.log_message(f"Error checking next page: {str(e)}")
            return False

    def navigate_to_next_page(self):
        """Navigate to next page"""
        try:
            self.config_manager.log_message(f"Attempting to navigate to page {self.current_page + 1}")
            
            next_button = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.pagination_selectors['next_button']))
            )
            
            # Scroll to button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            
            # Try regular click first
            try:
                next_button.click()
            except:
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", next_button)
            
            self.current_page += 1
            
            # Wait for new page to load
            WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.pagination_selectors['results_container']))
            )
            
            self.config_manager.log_message(f"Successfully navigated to page {self.current_page}")
            return True
            
        except Exception as e:
            self.config_manager.log_message(f"Error navigating to next page: {str(e)}")
            return False

    def get_current_page_number(self):
        """Get current page number"""
        try:
            page_element = self.driver.find_element(By.CSS_SELECTOR, self.pagination_selectors['page_number'])
            return int(page_element.text)
        except:
            return self.current_page
        
            
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
            # Wait for results container
            results_container = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="search-results"]'))
            )
            
            # Check for no results
            try:
                no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results for')]")
                if no_results:
                    self.config_manager.log_message("No results found for search")
                    return False
            except:
                pass
            
            # Get all results
            results = results_container.find_elements(By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]')
            
            # Check if any results exist
            if not results:
                self.config_manager.log_message("No valid results found")
                return False
                
            # Filter out processed URLs
            new_results = [
                result for result in results 
                if not self.url_manager.is_processed(result.get_attribute('href'))
            ]
            
            # Return True if there are any new results
            has_new_results = len(new_results) > 0
            self.config_manager.log_message(f"Found {len(new_results)} new results")
            return has_new_results
                
        except Exception as e:
            self.config_manager.log_message(f"Error validating results: {str(e)}")
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
    
    def calculate_completion_status(self, category, subcategory, search_term):
        """
        Calculate completion status for a subcategory
        """
        try:
            # Get all available URLs using the pagination-aware search
            success, fetched_urls = self.execute_search_with_retries(
                category, 
                subcategory, 
                search_term
            )
            
            total_urls = len(fetched_urls)
            print(f"Total available URLs for {subcategory}: {total_urls}")

            # Get current download count
            current_downloads = self.progress_tracker.get_subcategory_downloads(category, subcategory)
            print(f"Current downloads for {subcategory}: {current_downloads}")

            # Handle case when no URLs are found
            if total_urls == 0:
                if current_downloads > 0:
                    # If we already have downloads but no new URLs, consider it complete
                    required_downloads = current_downloads
                    return True, current_downloads, required_downloads, total_urls
                else:
                    # No URLs and no downloads
                    return False, 0, 0, 0

            # Calculate required downloads (minimum 1)
            required_downloads = max(total_urls // 2, 1)
            print(f"Required downloads for {subcategory}: {required_downloads} (half of {total_urls} total URLs)")

            # Check completion status
            is_complete = current_downloads >= required_downloads

            return is_complete, current_downloads, required_downloads, total_urls

        except Exception as e:
            self.config_manager.log_message(f"Error calculating completion status: {str(e)}")
            return False, 0, 0, 0