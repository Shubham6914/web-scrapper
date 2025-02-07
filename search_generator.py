import traceback


# In search_generator.py
class SearchMechanism:
    def __init__(self, insurance_categories, config_manager=None):
        """
        Initialize search mechanism with insurance categories
        Args:
            insurance_categories (dict): Dictionary of categories and their subcategories
            config_manager: ConfigManager instance for logging
        """
        self.categories = insurance_categories
        self.category_list = list(insurance_categories.keys())
        self.current_category_index = 0
        self.current_subcategory_index = 0
        self.search_completed = False
        self.current_page = 1
        self.max_pages = 2  # Add this line
        self.config_manager = config_manager
        
    def log_message(self, message):
        """Safe logging method"""
        if self.config_manager:
            self.config_manager.log_message(message)
        else:
            print(message)

    def initialize_search(self, resume_point=None):
        """Initialize or reset search position with resume capability"""
        try:
            self.log_message("=== Initializing Search ===")
            
            if resume_point:
                self.log_message(f"Resuming from previous point: {resume_point}")
                self.current_category_index = resume_point['category_index']
                self.current_subcategory_index = resume_point['subcategory_index']
                self.current_page = resume_point.get('current_page', 1)
                self.search_completed = False
            else:
                self.log_message("Starting fresh search")
                self.current_category_index = 0
                self.current_subcategory_index = 0
                self.current_page = 1
                self.search_completed = False

            # Get current search item
            current_item = self.get_current_search_item()
            if current_item:
                self.log_message(f"Search initialized with: {current_item}")
            else:
                self.log_message("No search items available")
                
            return current_item
            
        except Exception as e:
            self.log_message(f"Error initializing search: {str(e)}")
            return None
    
    def get_current_search_item(self):
        """
        Get current category and subcategory for searching
        Returns:
            dict: Current search information
        """
        if self.search_completed:
            return None
            
        current_category = self.category_list[self.current_category_index]
        current_subcategory = self.categories[current_category][self.current_subcategory_index]
        
        return {
            'category': current_category,
            'subcategory': current_subcategory,
            'search_term': self._format_search_term(current_subcategory),
            'is_last_subcategory': self.is_last_subcategory(),
            'is_last_category': self.is_last_category(),
            'category_index': self.current_category_index,
            'subcategory_index': self.current_subcategory_index,
            'current_page': self.current_page,  # Add this line
            'max_pages': self.max_pages  # Add this line
        }
    
    
    def _format_search_term(self, term):
        """
        Format subcategory for search
        Args:
            term: Subcategory name
        Returns:
            str: Formatted search term
        """
        # Remove underscores and clean up
        term = term.replace('_', ' ')
        term = ' '.join(term.split())
        
        # Add 'insurance' if not present
        if 'insurance' not in term.lower():
            term += ' insurance'
            
        # Remove category prefix if present
        for category in self.category_list:
            category_name = category.replace('_', ' ').lower()
            if term.lower().startswith(category_name):
                term = term[len(category_name):].strip()
        
        return term.strip()
    
    def move_to_next(self):
        """
        Move to next search item
        Returns:
            dict: Next search information or None if completed
        """
        if self.search_completed:
            return None
            
        if not self.is_last_subcategory():
            self.current_subcategory_index += 1
        else:
            if not self.is_last_category():
                self.current_category_index += 1
                self.current_subcategory_index = 0
            else:
                self.search_completed = True
                return None
                
        return self.get_current_search_item()
    
    def is_last_subcategory(self):
        """Check if current subcategory is last in current category"""
        current_category = self.category_list[self.current_category_index]
        return self.current_subcategory_index >= len(self.categories[current_category]) - 1
    
    def is_last_category(self):
        """Check if current category is last"""
        return self.current_category_index >= len(self.category_list) - 1
    
    def get_search_progress(self):
        """
        Get current search progress information with pagination
        Returns:
            dict: Progress information
        """
        total_categories = len(self.category_list)
        total_subcategories = sum(len(subcategories) for subcategories in self.categories.values())
        
        processed_categories = self.current_category_index
        processed_subcategories = sum(len(self.categories[cat]) for cat in self.category_list[:self.current_category_index])
        processed_subcategories += self.current_subcategory_index
        
        current_item = self.get_current_search_item()
        
        return {
            'current_position': current_item,
            'current_search_term': current_item['search_term'] if current_item else None,
            'current_page': self.current_page,
            'max_pages': getattr(self, 'max_pages', 5),  # Safe access to max_pages
            'processed_categories': processed_categories,
            'total_categories': total_categories,
            'processed_subcategories': processed_subcategories,
            'total_subcategories': total_subcategories,
            'completion_percentage': (processed_subcategories / total_subcategories) * 100 if total_subcategories > 0 else 0
        }
    def reset_pagination(self):
        """
        Reset pagination for new search
        """
        self.current_page = 1

    def next_page(self):
        """
        Move to next page if available
        Returns:
            bool: True if moved to next page, False if at max pages
        """
        if self.current_page < getattr(self, 'max_pages', 5):  # Safe access to max_pages
            self.current_page += 1
            self.log_message(f"Moving to page {self.current_page}")
            return True
        self.log_message("Reached maximum page limit")
        return False
    def get_page_status(self):
        """
        Get current page status
        Returns:
            dict: Current page information
        """
        return {
            'current_page': self.current_page,
            'max_pages': getattr(self, 'max_pages', 5),
            'has_next_page': self.current_page < getattr(self, 'max_pages', 5)
        }
    def set_position(self, category_index, subcategory_index):
        """
        Set search position to specific indices
        Args:
            category_index (int): Category index
            subcategory_index (int): Subcategory index
        Returns:
            dict: Current search information after setting position
        """
        if (0 <= category_index < len(self.category_list)):
            self.current_category_index = category_index
            category = self.category_list[category_index]
            
            if (0 <= subcategory_index < len(self.categories[category])):
                self.current_subcategory_index = subcategory_index
                self.search_completed = False
                return self.get_current_search_item()
        
        return None

    # def get_current_terms(self):
    #     """
    #     Get current search terms and variations
    #     Returns:
    #         list: List of search term variations
    #     """
    #     current_item = self.get_current_search_item()
    #     if not current_item:
    #         return []
            
    #     base_term = current_item['search_term']
    #     return f"{base_term} insurance"
    