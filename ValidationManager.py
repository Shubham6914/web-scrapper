class ValidationManager:
    def __init__(self):
        """
        Initialize validation manager with configuration settings
        """
        self.validation_config = {
            'min_results': 3,                    # Minimum number of results required
            'relevance_threshold': 0.6,          # Minimum relevance score (60%)
            'max_title_length': 150,             # Maximum title length to process
            'min_title_length': 10,              # Minimum title length to be valid
            'required_keywords': ['insurance', 'coverage', 'policy']  # Must contain at least one
        }
        
        # Track validation statistics
        self.validation_stats = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'invalid_results': []
        }

    def validate_search_results(self, results, category, subcategory):
        """
        Validate search results based on multiple criteria
        
        Parameters:
        - results: List of WebElements (search results)
        - category: Current insurance category
        - subcategory: Current insurance subcategory
        
        Returns:
        - tuple: (is_valid, validation_details)
        """
        try:
            self.validation_stats['total_checks'] += 1
            validation_details = {
                'total_results': len(results),
                'valid_results': 0,
                'relevance_score': 0,
                'failed_checks': [],
                'passed_checks': []
            }

            # 1. Check minimum results
            if not self._check_minimum_results(results, validation_details):
                return False, validation_details

            # 2. Validate each result
            valid_results = []
            for result in results:
                if self._validate_single_result(result, category, subcategory, validation_details):
                    valid_results.append(result)

            # 3. Calculate overall relevance score
            validation_details['valid_results'] = len(valid_results)
            validation_details['relevance_score'] = len(valid_results) / len(results)

            # 4. Final validation check
            is_valid = self._check_final_validation(validation_details)

            if is_valid:
                self.validation_stats['passed_checks'] += 1
            else:
                self.validation_stats['failed_checks'] += 1

            return is_valid, validation_details

        except Exception as e:
            print(f"Error in validation: {str(e)}")
            return False, validation_details

    def _check_minimum_results(self, results, validation_details):
        """Check if minimum number of results are present"""
        if len(results) < self.validation_config['min_results']:
            validation_details['failed_checks'].append('insufficient_results')
            return False
        validation_details['passed_checks'].append('minimum_results')
        return True

    def _validate_single_result(self, result, category, subcategory, validation_details):
        """
        Validate a single search result
        Returns: Boolean indicating if result is valid
        """
        try:
            # Get result title and description
            title = result.get_attribute('title').lower()
            description = result.get_attribute('text').lower() if result.get_attribute('text') else ''

            # 1. Title length check
            if not self._check_title_length(title):
                validation_details['failed_checks'].append('invalid_title_length')
                return False

            # 2. Keyword presence check
            if not self._check_required_keywords(title, description):
                validation_details['failed_checks'].append('missing_keywords')
                return False

            # 3. Category relevance check
            if not self._check_category_relevance(title, description, category, subcategory):
                validation_details['failed_checks'].append('low_relevance')
                return False

            validation_details['passed_checks'].append('result_validation')
            return True

        except Exception as e:
            print(f"Error validating result: {str(e)}")
            return False

    def _check_title_length(self, title):
        """Check if title length is within acceptable range"""
        return self.validation_config['min_title_length'] <= len(title) <= self.validation_config['max_title_length']

    def _check_required_keywords(self, title, description):
        """Check if required keywords are present"""
        text = f"{title} {description}"
        return any(keyword in text for keyword in self.validation_config['required_keywords'])

    def _check_category_relevance(self, title, description, category, subcategory):
        """Check if result is relevant to current category/subcategory"""
        text = f"{title} {description}".lower()
        category_terms = category.lower().replace('_', ' ').split()
        subcategory_terms = subcategory.lower().replace('_', ' ').split()
        
        # Check for category terms
        category_match = any(term in text for term in category_terms)
        # Check for subcategory terms
        subcategory_match = any(term in text for term in subcategory_terms)
        
        return category_match or subcategory_match

    def _check_final_validation(self, validation_details):
        """Perform final validation check"""
        # Check if enough valid results
        if validation_details['valid_results'] < self.validation_config['min_results']:
            return False
            
        # Check relevance score
        if validation_details['relevance_score'] < self.validation_config['relevance_threshold']:
            return False
            
        return True

    def get_validation_stats(self):
        """Get current validation statistics"""
        return {
            'total_checks': self.validation_stats['total_checks'],
            'passed_checks': self.validation_stats['passed_checks'],
            'failed_checks': self.validation_stats['failed_checks'],
            'success_rate': (self.validation_stats['passed_checks'] / 
                           self.validation_stats['total_checks'] if 
                           self.validation_stats['total_checks'] > 0 else 0)
        }

    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'invalid_results': []
        }