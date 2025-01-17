from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import time
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
        Main method to execute the search sequence for all patterns
        Returns: Dictionary of search results and statistics
        """
        # Get resume point if any
        resume_point = self.progress_tracker.get_resume_point()
        
        try:
            # Iterate through each insurance category
            for category, subcategories in self.search_patterns.items():
                # Skip categories until resume point if exists
                if resume_point['category'] and category != resume_point['category']:
                    continue
                    
                self.current_progress['category'] = category
                print(f"\nProcessing category: {category}")
                
                # Process each subcategory
                for subcategory, patterns in subcategories.items():
                    # Skip subcategories until resume point if exists
                    if resume_point['subcategory'] and subcategory != resume_point['subcategory']:
                        continue
                        
                    self.current_progress['subcategory'] = subcategory
                    print(f"\nProcessing subcategory: {subcategory}")
                    
                    # Execute patterns in priority order
                    for pattern_index, pattern in enumerate(patterns):
                        # Skip patterns until resume point if exists
                        if resume_point['pattern_index'] and pattern_index < resume_point['pattern_index']:
                            continue
                            
                        self.current_progress['pattern_index'] = pattern_index
                        
                        # Execute search with current pattern
                        search_success, results = self.search_with_pattern(pattern)
                        
                        # Update progress tracker
                        self.progress_tracker.update_search_progress(
                            category=category,
                            subcategory=subcategory,
                            pattern=pattern,
                            success=search_success,
                            documents=len(results) if results else 0
                        )
                        
                        # If search was successful, store pattern
                        if search_success:
                            self.current_progress['successful_patterns'].add(pattern)
                            
                        # Track progress
                        self.track_progress()
                        
                        # If we have enough successful results, mark subcategory complete and move to next
                        if len(self.current_progress['successful_patterns']) >= self.search_config['min_results']:
                            self.progress_tracker.mark_subcategory_complete(category, subcategory)
                            break
                    
                    # Clear successful patterns for next subcategory
                    self.current_progress['successful_patterns'].clear()
                    
                # Print progress report after each category
                self.progress_tracker.print_progress_report()
                
            return self.search_results
                    
        except Exception as e:
            print(f"Error in search execution: {str(e)}")
            # Save progress before returning None
            self.progress_tracker.save_progress()
            return None

    
    def search_with_pattern(self, pattern):
        """
        Execute search with a single pattern
        
        Parameters:
        - pattern: Search pattern to execute
        
        Returns:
        - Tuple: (success_status: bool, results: list)
        """
        try:
            print(f"Attempting search with pattern: {pattern}")
            # Navigate to search page
            self.driver.get('https://www.scribd.com/search')
            
            # Find and clear search input with better wait handling
            try:
                search_input = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
                )
                print("Found search input")

                search_input.clear()
                
                # Input search pattern
                search_input.send_keys(pattern)
                search_input.send_keys(Keys.RETURN)
                print(f"Entered search pattern: {pattern}")
                
                # Wait for search results to load
                WebDriverWait(self.driver, self.search_config['wait_time']).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="search-results"]'))
                )
                
                print("Search results container found")
                # Add small delay to ensure results are fully loaded
                time.sleep(2)
                
                # Validate results
                validation_result = self.validate_search_results()
                print(f"Validation result: {validation_result}")
                # Validate results and get them if successful
                if validation_result:
                    results = self.driver.find_elements(By.CSS_SELECTOR, 'a[class^="FluidCell-module_linkOverlay"]')
                    print(f"Found {len(results)} results")
                    # Additional validation of results
                    if results and len(results) >= self.search_config['min_results']:
                        print(f"Found {len(results)} results for pattern: {pattern}")
                        return True, results
                    else:
                        print(f"Insufficient results found for pattern: {pattern}")
                        return False, []
                
                print(f"Search validation failed for pattern: {pattern}")
                return False, []
                
            except Exception as e:
                print(f"Error during search execution: {str(e)}")
                return False, []
                
        except Exception as e:
            print(f"Critical error executing search pattern '{pattern}': {str(e)}")
            # Attempt to refresh page on critical error
            try:
                self.driver.refresh()
            except:
                pass
            return False, []

    def validate_search_results(self):
        """
        Validate the search results
        
        Returns:
        - Boolean indicating if results are valid
        """
        try:
            # Wait for results container
            results_container = WebDriverWait(self.driver, self.search_config['wait_time']).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="search-results"]'))
            )
            
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