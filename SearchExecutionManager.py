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
            'wait_time': 12,
            'min_results': 2,
            'max_results': 5,
            'search_delay': 5,
            'max_page_limit': 20 # New: Maximum pages to process
        }

    def execute_search_with_retries(self, category, subcategory, search_term, max_attempts=3):
        """
        Execute search with retries fordef wait_for_element(self, by, selector, timeout=10, visible=True): each page using direct URL pagination
        Returns success status and collected URLs
        """
        self.config_manager.log_message(f"\n=== Starting search for {category}/{subcategory} ===")
        
        all_urls = []  # Master list for all collected URLs
        max_page_limit = 15 # Maximum pages to process
        
        # Process each page up to limit
        for page in range(1, max_page_limit + 1):
            self.config_manager.log_message(f"\n=== Processing page {page} ===")
            page_urls = []  # URLs collected from current page
            
            # Try each page multiple times
            for attempt in range(max_attempts):
                try:
                    self.config_manager.log_message(f"Attempt {attempt + 1} of {max_attempts} for page {page}")
                    
                    # Construct and navigate to search URL
                    search_url = f'https://www.scribd.com/search?query={search_term}&page={page}'
                    self.config_manager.log_message(f"Search term: {search_term}")  # Log search term for each attempt
        
                    self.config_manager.log_message(f"Navigating to: {search_url}")
                    
                    self.driver.get(search_url)
                    time.sleep(self.search_config['search_delay'])
                    
                    # Check for explicit no results message
                    try:
                        no_results = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'No results for')]")
                        if no_results:
                            self.config_manager.log_message(f"Explicit 'No results' found on page {page}")
                            return True if all_urls else False, all_urls
                    except Exception as e:
                        self.config_manager.log_message(f"Error checking no results: {str(e)}")
                    
                    # Collect URLs from current page attempt
                    current_attempt_urls = self.collect_document_urls(category, subcategory)
                    
                    if current_attempt_urls:
                        page_urls = current_attempt_urls  # Store successful URLs
                        self.config_manager.log_message(f"Found {len(current_attempt_urls)} URLs on page {page}, attempt {attempt + 1}")
                        break  # Successfully got URLs, move to next page
                    else:
                        self.config_manager.log_message(f"No URLs found on page {page}, attempt {attempt + 1}")
                        
                    if attempt < max_attempts - 1:
                        self.config_manager.log_message("Waiting before next attempt...")
                        time.sleep(5)
                        
                except Exception as e:
                    self.config_manager.log_message(f"Error in page {page}, attempt {attempt + 1}: {str(e)}")
                    if attempt < max_attempts - 1:
                        time.sleep(5)
            
            # Add any URLs found from this page to master list
            if page_urls:
                all_urls.extend(page_urls)
                self.config_manager.log_message(f"Added {len(page_urls)} URLs from page {page} to collection")
            
            # Log running total
            self.config_manager.log_message(f"Running total of URLs collected: {len(all_urls)}")
            
            # Add delay before next page unless it's the last page
            if page < max_page_limit:
                self.config_manager.log_message(f"Waiting before processing page {page + 1}")
                time.sleep(self.search_config['search_delay'])
        
        # Final results
        self.config_manager.log_message(f"\n=== Search completed ===")
        self.config_manager.log_message(f"Total pages processed: {max_page_limit}")
        self.config_manager.log_message(f"Total URLs collected: {len(all_urls)}")
        
        # Return True if any URLs were found, False otherwise
        return len(all_urls) > 0, all_urls

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
        """
        Collect and filter document URLs using multiple selector strategies
        Args:
            category: Current category
            subcategory: Current subcategory
        Returns:
            list: Collected valid URLs
        """
        try:
            self.config_manager.log_message("Starting URL collection with enhanced selectors...")
            
            # List of selector strategies to try (in order of preference)
            selector_strategies = [
                {
                    'type': 'css',
                    'selector': 'a[class^="FluidCell-module_linkOverlay"]',
                    'description': 'Original fluid cell selector'
                },
                {
                    'type': 'css',
                    'selector': 'div.doc-cell a',
                    'description': 'Document cell links'
                },
                {
                    'type': 'xpath',
                    'selector': '//div[contains(@class, "search-results")]//a[contains(@href, "/document/")]',
                    'description': 'Direct document links'
                },
                {
                    'type': 'css',
                    'selector': 'a[href*="/document/"]',
                    'description': 'Generic document links'
                }
            ]

            # Wait for page load with better timing
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                # Wait for search results container
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="search-results"]'))
                )
            except Exception as e:
                self.config_manager.log_message(f"Warning: Page load wait condition failed: {str(e)}")

            # Try each selector strategy
            new_urls = set()  # Using set to avoid duplicates
            for strategy in selector_strategies:
                try:
                    self.config_manager.log_message(f"\nTrying {strategy['description']}...")
                    
                    # Select elements based on selector type
                    if strategy['type'] == 'css':
                        elements = self.driver.find_elements(By.CSS_SELECTOR, strategy['selector'])
                    else:  # xpath
                        elements = self.driver.find_elements(By.XPATH, strategy['selector'])
                    
                    self.config_manager.log_message(f"Found {len(elements)} elements with {strategy['type']} selector: {strategy['selector']}")
                    
                    # Process elements found with current strategy
                    for element in elements:
                        try:
                            url = element.get_attribute('href')
                            if self._is_valid_document_url(url):
                                new_urls.add(url)
                        except Exception as e:
                            self.config_manager.log_message(f"Error extracting URL from element: {str(e)}")
                            continue
                    
                    # If we found URLs with this strategy, we can stop trying others
                    if new_urls:
                        self.config_manager.log_message(f"Successfully found {len(new_urls)} URLs using {strategy['description']}")
                        break
                        
                except Exception as e:
                    self.config_manager.log_message(f"Error with {strategy['description']}: {str(e)}")
                    continue
            
            # Convert set back to list and return
            final_urls = list(new_urls)
            self.config_manager.log_message(f"Final total unique URLs collected: {len(final_urls)}")
            return final_urls
                
        except Exception as e:
            self.config_manager.log_message(f"Error in collect_document_urls: {str(e)}")
            import traceback
            self.config_manager.log_message(f"Full traceback: {traceback.format_exc()}")
            return []

    def _is_valid_document_url(self, url):
        """
        Validate if URL is a valid Scribd document URL
        Args:
            url: URL to validate
        Returns:
            bool: True if valid, False otherwise
        """
        if not url:
            return False
            
        # Basic validation criteria
        valid_conditions = [
            'scribd.com/document/' in url,
            not url.endswith('#'),
            not url.endswith('/')
        ]
        
        # Check if URL was already processed
        if self.url_manager.is_processed(url):
            return False
            
        return all(valid_conditions)

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