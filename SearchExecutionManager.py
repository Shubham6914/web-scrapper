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
            'search_delay': 3,
            'max_page_limit': 25  # New: Maximum pages to process
        }

    def execute_search_with_retries(self, category, subcategory, search_term, max_attempts=3):
        """
        Execute search with retries using direct URL pagination
        """
        self.config_manager.log_message(f"\n=== Starting search for {category}/{subcategory} ===")
        
        for attempt in range(max_attempts):
            try:
                self.config_manager.log_message(f"Attempt {attempt + 1} of {max_attempts}")
                
                all_urls = []
                
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
                            break
                    except:
                        pass
                    
                    # Collect URLs from current page
                    page_urls = self.collect_document_urls(category, subcategory)
                    
                    if page_urls:
                        all_urls.extend(page_urls)
                        self.config_manager.log_message(f"Found {len(page_urls)} URLs on page {page}")
                    else:
                        self.config_manager.log_message(f"No URLs found on page {page}, ending search.")
                        break
                    
                    # Add delay between pages
                    if page < self.search_config['max_page_limit']:
                        time.sleep(self.search_config['search_delay'])
                
                if all_urls:
                    self.config_manager.log_message(f"Total URLs found: {len(all_urls)}")
                    return True, all_urls
                
                if attempt < max_attempts - 1:
                    self.config_manager.log_message("No URLs found, waiting before retry...")
                    time.sleep(5)
                
            except Exception as e:
                self.config_manager.log_message(f"Error in search attempt {attempt + 1}: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
        
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