class SearchMechanism:
    def __init__(self, insurance_categories):
        """
        Initialize search mechanism with insurance categories
        Args:
            insurance_categories (dict): Dictionary of categories and their subcategories
        """
        self.categories = insurance_categories
        self.category_list = list(insurance_categories.keys())
        self.current_category_index = 0
        self.current_subcategory_index = 0
        self.search_completed = False
        
    def initialize_search(self, resume_point=None):
        """
        Initialize or reset search position with resume capability
        Args:
            resume_point: Dictionary containing resume information
        """
        if resume_point:
            self.current_category_index = resume_point['category_index']
            self.current_subcategory_index = resume_point['subcategory_index']
            self.search_completed = False
        else:
            self.current_category_index = 0
            self.current_subcategory_index = 0
            self.search_completed = False
            
        return self.get_current_search_item()
    
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
        
        # Format search term explicitly
        search_term = self._format_search_term(current_subcategory)
        
        # Debug logging
        print(f"DEBUG: Category: {current_category}")
        print(f"DEBUG: Subcategory: {current_subcategory}")
        print(f"DEBUG: Formatted search term: {search_term}")
        
        return {
            'category': current_category,
            'subcategory': current_subcategory,
            'search_term': search_term,  # This should now be properly formatted
            'is_last_subcategory': self.is_last_subcategory(),
            'is_last_category': self.is_last_category(),
            'category_index': self.current_category_index,
            'subcategory_index': self.current_subcategory_index
        }
    
    
    def _format_search_term(self, term):
        """
        Format subcategory for search
        Args:
            term: Subcategory name
        Returns:
            str: Formatted search term
        """
        if not term:
            return ""
        
        # Remove underscores and clean up
        term = term.replace('_', ' ')
        term = ' '.join(term.split())
        
        # For Commercial Auto Insurance, we want to keep it as is
        if 'insurance' not in term.lower():
            term += ' insurance'
        
        # Clean up any double spaces
        formatted_term = ' '.join(term.split())
        
        print(f"DEBUG: Original term: {term}")
        print(f"DEBUG: Formatted search term: {formatted_term}")
    
        return formatted_term
    
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
        Get current search progress information
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
            'processed_categories': processed_categories,
            'total_categories': total_categories,
            'processed_subcategories': processed_subcategories,
            'total_subcategories': total_subcategories,
            'completion_percentage': (processed_subcategories / total_subcategories) * 100
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
    