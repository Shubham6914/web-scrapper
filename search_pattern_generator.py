# search_pattern_generator.py

class SearchPatternGenerator:
    def __init__(self, insurance_data):
        """Initialize with insurance data dictionary"""
        self.insurance_data = insurance_data
        self.patterns = {}
        self.common_terms = ['insurance', 'coverage', 'policy']
    
    def clean_term(self, term):
        """Clean and format search terms"""
        if isinstance(term, str):
            # Remove special characters, convert to lowercase
            cleaned = term.lower()
            cleaned = cleaned.replace('_', ' ').replace('-', ' ')
            return cleaned.strip()
        return term

    def generate_basic_pattern(self, main_category, subcategory_data):
        """Generate basic search patterns"""
        patterns = set()
        
        # Clean category and subcategory terms
        main_cat = self.clean_term(main_category)
        search_term = self.clean_term(subcategory_data['search_term'])
        
        # Generate basic combinations
        patterns.add(f"{main_cat} {search_term}")
        patterns.add(f"{search_term} insurance")
        patterns.add(f"{main_cat} {search_term} insurance")
        
        return list(patterns)

    def generate_description_pattern(self, subcategory_name, subcategory_data):
        """Generate description-based patterns"""
        patterns = set()
        search_term = self.clean_term(subcategory_data['search_term'])
        
        # Generate patterns from description keywords
        for keyword in subcategory_data['description_keywords']:
            keyword = self.clean_term(keyword)
            patterns.add(f"{search_term} {keyword}")
            patterns.add(f"{search_term} insurance {keyword}")
            
            # Combine multiple keywords
            for second_keyword in subcategory_data['description_keywords']:
                if keyword != second_keyword:
                    second_keyword = self.clean_term(second_keyword)
                    patterns.add(f"{search_term} {keyword} {second_keyword}")
        
        return list(patterns)

    def generate_combined_pattern(self, main_category, subcategory_name, subcategory_data):
        """Generate combined patterns using multiple elements"""
        patterns = set()
        main_cat = self.clean_term(main_category)
        search_term = self.clean_term(subcategory_data['search_term'])
        
        # Combine with description keywords
        for keyword in subcategory_data['description_keywords']:
            keyword = self.clean_term(keyword)
            patterns.add(f"{main_cat} {search_term} {keyword}")
            patterns.add(f"{search_term} insurance {keyword}")
            
            # Add variations with common terms
            for common_term in self.common_terms:
                patterns.add(f"{search_term} {common_term} {keyword}")
                patterns.add(f"{main_cat} {search_term} {common_term} {keyword}")
        
        return list(patterns)

    def generate_action_pattern(self, subcategory_data):
        """Generate patterns using action words"""
        patterns = set()
        search_term = self.clean_term(subcategory_data['search_term'])
        action_word = self.clean_term(subcategory_data['action_words'])
        
        # Generate action-based patterns
        for keyword in subcategory_data['description_keywords']:
            keyword = self.clean_term(keyword)
            patterns.add(f"{action_word} {search_term} {keyword}")
            patterns.add(f"{search_term} {action_word} {keyword}")
            patterns.add(f"{search_term} insurance {action_word} {keyword}")
        
        return list(patterns)

    def clean_and_validate_patterns(self, patterns):
        """Clean and validate generated patterns"""
        cleaned_patterns = set()
        
        for pattern in patterns:
            # Remove multiple spaces
            cleaned = ' '.join(pattern.split())
            # Remove very short or very long patterns
            if 3 <= len(cleaned.split()) <= 6:
                cleaned_patterns.add(cleaned)
        
        return list(cleaned_patterns)

    def generate_all_patterns(self):
        """Main method to generate all search patterns"""
        for main_category, subcategories in self.insurance_data.items():
            self.patterns[main_category] = {}
            
            for subcategory_name, subcategory_data in subcategories.items():
                current_patterns = []
                
                # Generate all pattern types
                basic_patterns = self.generate_basic_pattern(
                    main_category, subcategory_data
                )
                description_patterns = self.generate_description_pattern(
                    subcategory_name, subcategory_data
                )
                combined_patterns = self.generate_combined_pattern(
                    main_category, subcategory_name, subcategory_data
                )
                action_patterns = self.generate_action_pattern(
                    subcategory_data
                )
                
                # Combine all patterns
                current_patterns.extend(basic_patterns)
                current_patterns.extend(description_patterns)
                current_patterns.extend(combined_patterns)
                current_patterns.extend(action_patterns)
                
                # Clean and validate
                final_patterns = self.clean_and_validate_patterns(current_patterns)
                
                # Store patterns
                self.patterns[main_category][subcategory_name] = final_patterns
        
        return self.patterns