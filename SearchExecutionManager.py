from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
# import progress trackeer class to track progress 
from ProgressTracker import ProgressTracker
# import validation manager class to validate
from ValidationManager import ValidationManager

class SearchExecutionManager:
    def __init__(self, search_patterns, driver,progress_tracker=None, validator=None):
        """
        Initialize the Search Execution Manager
        
        Parameters:
        - search_patterns: Dictionary of generated search patterns from SearchPatternGenerator
        - driver: Selenium WebDriver instance
        """
        self.search_patterns = search_patterns
        self.driver = driver
        # Use provided instances or create new ones
        self.progress_tracker = progress_tracker if progress_tracker else ProgressTracker()
        self.validator = validator if validator else ValidationManager()
            
        # Track current search progress
        self.current_progress = {
            'category': None,
            'subcategory': None,
            'pattern_index': 0,
            'successful_patterns': set()
        }
        
        # Store search results and metrics
        self.search_results = {
            'successful_searches': {},
            'failed_searches': {},
            'documents_found': {}
        }
        
        # Configure search settings
        self.search_config = {
            'min_results': 3,          # Minimum results needed to consider search successful
            'max_retries': 2,          # Maximum retry attempts for failed searches
            'wait_time': 10            # Maximum wait time for results
    
        }
        # Initialize progress tracker
        self.progress_tracker = ProgressTracker()
        # initialize validator
        self.validator = ValidationManager()

    def execute_search_sequence(self):
        """
        Main method to execute the search sequence one pattern at a time
        Returns: Dictionary containing single pattern results and status
        """
        try:
            # Get resume point if any
            resume_point = self.progress_tracker.get_resume_point()
            
            # Handle in-progress pattern with pending URLs
            if resume_point.get('status') == 'resume' and resume_point.get('pending_urls'):
                return {
                    'category': resume_point['category'],
                    'subcategory': resume_point['subcategory'],
                    'pattern': resume_point['pattern'],
                    'pattern_key': resume_point['pattern_key'],
                    'urls': resume_point['pending_urls'],
                    'total_urls': resume_point['total_pending'],
                    'status': 'resume_downloads'
                }

            # Iterate through each insurance category
            for category, subcategories in self.search_patterns.items():
                # Skip categories until resume point if exists
                if resume_point.get('category') and category != resume_point['category']:
                    continue
                    
                self.current_progress['category'] = category
                print(f"\n=== Processing Category: {category} ===")
                
                # Process each subcategory
                for subcategory, patterns in subcategories.items():
                    # Skip subcategories until resume point if exists
                    if resume_point.get('subcategory') and subcategory != resume_point['subcategory']:
                        continue
                        
                    self.current_progress['subcategory'] = subcategory
                    print(f"\nProcessing subcategory: {subcategory}")
                    
                    # Get current pattern index
                    current_pattern_index = resume_point.get('pattern_index', 0)
                    
                    # Execute patterns one at a time
                    for pattern_index, pattern in enumerate(patterns):
                        # Skip patterns until resume point
                        if pattern_index < current_pattern_index:
                            continue
                            
                        self.current_progress['pattern_index'] = pattern_index
                        
                        # Check if pattern was already processed
                        if self.progress_tracker.is_pattern_completed(
                            category=category,
                            subcategory=subcategory,
                            pattern=pattern
                        ):
                            print(f"Pattern '{pattern}' already completed, moving to next...")
                            continue
                        
                        print(f"\nProcessing pattern: {pattern}")
                        
                        # Execute search with current pattern
                        search_success, results = self.search_with_pattern(pattern)
                        
                        if search_success and results:
                            print(f"Found {len(results)} URLs for pattern '{pattern}'")
                            
                            # Update progress tracker
                            self.progress_tracker.update_search_progress(
                                category=category,
                                subcategory=subcategory,
                                pattern=pattern,
                                success=search_success,
                                documents=len(results)
                            )
                            
                            # Return results for this pattern
                            return {
                                'category': category,
                                'subcategory': subcategory,
                                'pattern': pattern,
                                'pattern_index': pattern_index,
                                'urls': results,
                                'total_urls': len(results),
                                'status': 'pattern_ready_for_download'
                            }
                        else:
                            print(f"No results found for pattern '{pattern}'")
                            self.progress_tracker.update_search_progress(
                                category=category,
                                subcategory=subcategory,
                                pattern=pattern,
                                success=False,
                                documents=0
                            )
                    
                    # If all patterns for subcategory are processed
                    print(f"All patterns processed for {subcategory}")
                    self.progress_tracker.mark_subcategory_complete(category, subcategory)
                    self.current_progress['successful_patterns'].clear()
                
                # Print progress report after each category
                self.progress_tracker.print_progress_report()
            
            # If we reach here, all categories are processed
            print("\nAll categories and patterns processed")
            return None
                    
        except Exception as e:
            print(f"Error in search execution: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            self.progress_tracker.save_progress()
            return None

    def is_pattern_completed(self, category, subcategory, pattern):
        """Check if pattern has been processed and downloads completed"""
        try:
            download_status = self.progress_tracker.get_pattern_status(category, subcategory, pattern)
            return download_status and download_status.get('status') == 'completed'
        except Exception:
            return False

    

    def is_subcategory_completed(self, category, subcategory):
        """Check if subcategory is already completed"""
        try:
            category_data = self.progress_tracker.progress_data['categories'].get(category, {})
            subcategory_data = category_data.get('subcategories', {}).get(subcategory, {})
            return subcategory_data.get('completed', False)
        except Exception:
            return False

    def is_pattern_tried(self, category, subcategory, pattern):
        """Check if pattern has already been tried for this subcategory"""
        try:
            category_data = self.progress_tracker.progress_data['categories'].get(category, {})
            subcategory_data = category_data.get('subcategories', {}).get(subcategory, {})
            patterns_tried = subcategory_data.get('patterns_tried', [])
            return pattern in patterns_tried
        except Exception:
            return False
    
    def search_with_pattern(self, pattern):
        try:
            print(f"Attempting search with pattern: {pattern}")
            self.driver.get('https://www.scribd.com/search')
            
            # Find and clear search input
            search_input = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
            )
            search_input.clear()
            
            # Input search pattern
            search_input.send_keys(pattern)
            search_input.send_keys(Keys.RETURN)
            
            # Wait for results to load
            time.sleep(3)  # Add small delay
            
            # Get all document links
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]'
            )
            urls = []
            
            for element in elements:
                try:
                    url = element.get_attribute('href')
                    if url and 'www.scribd.com/document/' in url:
                        print(f"Found document URL: {url}")
                        urls.append(url)
                except Exception as e:
                    print(f"Error getting URL: {str(e)}")
                    continue
            
            if urls:
                print(f"Found {len(urls)} document URLs")
                return True, urls
                
            return False, []
            
        except Exception as e:
            print(f"Error in search: {str(e)}")
            return False, []

    def validate_search_results(self):
        """
        Validate the search results
        
        Returns:
        - Boolean indicating if results are valid
        """
        try:
            print("Starting result validation")
            # Wait for results container
            results_container = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="search-results"]'))
            )
            print("Found results container")
            # Check for "no results" message
            try:
                no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results for')]")
                if no_results:
                    print("No results found message detected")
                    return False
            except:
                pass  # No "no results" message found, continue validation
            
            # Find all result elements
            results = results_container.find_elements(By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]')
            
            # Check if we have minimum required results
            if len(results) >= self.search_config['min_results']:
                # Verify result relevance
                relevant_count = 0
                for result in results[:5]:  # Check first 5 results
                    try:
                        title = result.get_attribute('title').lower()
                        # Check if result matches current category/subcategory
                        if (self.current_progress['category'].lower() in title or 
                            self.current_progress['subcategory'].lower() in title):
                            relevant_count += 1
                    except:
                        continue
                
                # Return True if we have enough relevant results
                return relevant_count >= 2  # At least 2 relevant results
            
            return False
            
        except Exception as e:
            print(f"Error validating results: {str(e)}")
            return False
    

    def track_progress(self):
        """
        Track and log search progress
        """
        try:
            # Calculate progress metrics
            category = self.current_progress['category']
            subcategory = self.current_progress['subcategory']
            successful_patterns = len(self.current_progress['successful_patterns'])
            
            # Log progress
            progress_msg = (
                f"Progress - Category: {category}, "
                f"Subcategory: {subcategory}, "
                f"Successful Patterns: {successful_patterns}"
            )
            print(progress_msg)
            
            # Store progress in results
            if category not in self.search_results:
                self.search_results[category] = {}
            
            self.search_results[category][subcategory] = {
                'successful_patterns': list(self.current_progress['successful_patterns']),
                'pattern_index': self.current_progress['pattern_index']
            }
            
        except Exception as e:
            print(f"Error tracking progress: {str(e)}")

    def _store_successful_search(self, pattern):
        """
        Store successful search pattern and results
        """
        category = self.current_progress['category']
        subcategory = self.current_progress['subcategory']
        
        if category not in self.search_results['successful_searches']:
            self.search_results['successful_searches'][category] = {}
        
        if subcategory not in self.search_results['successful_searches'][category]:
            self.search_results['successful_searches'][category][subcategory] = []
        
        self.search_results['successful_searches'][category][subcategory].append(pattern)

    def _store_failed_search(self, pattern):
        """
        Store failed search pattern
        """
        category = self.current_progress['category']
        subcategory = self.current_progress['subcategory']
        
        if category not in self.search_results['failed_searches']:
            self.search_results['failed_searches'][category] = {}
        
        if subcategory not in self.search_results['failed_searches'][category]:
            self.search_results['failed_searches'][category][subcategory] = []
        
        self.search_results['failed_searches'][category][subcategory].append(pattern)