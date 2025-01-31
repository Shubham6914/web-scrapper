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
        
    def initialize_search(self):
        """Initialize or reset search position"""
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
        
        return {
            'category': current_category,
            'subcategory': current_subcategory,
            'search_term': f"{current_subcategory} {current_category}",
            'is_last_subcategory': self.is_last_subcategory(),
            'is_last_category': self.is_last_category()
        }
    
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
        
        return {
            'current_position': self.get_current_search_item(),
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