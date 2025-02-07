import os
from typing import List, Dict, Set
from datetime import datetime



class ProcessedURLManager:
    def __init__(self, log_file: str = None):
        """
        Initialize ProcessedURLManager
        Args:
            log_file: Optional log file path
        """
        self.processed_urls_file = 'processed_urls.txt'
        self.log_file = log_file
        self.processed_urls: Set[str] = set()
        self.category_urls: Dict[str, Dict[str, Set[str]]] = {}
        self.url_processing_history: Dict[str, Dict] = {}  # New: Track URL processing history
        self.load_processed_urls()
        
    
    def load_processed_urls(self) -> None:
        """Load existing processed URLs from file with enhanced error handling"""
        try:
            if os.path.exists(self.processed_urls_file):
                with open(self.processed_urls_file, 'r') as f:
                    invalid_lines = []
                    for line_number, line in enumerate(f, 1):
                        try:
                            if '|' not in line:
                                invalid_lines.append(f"Line {line_number}: Missing separator")
                                continue
                                
                            parts = line.strip().split('|')
                            if len(parts) != 3:
                                invalid_lines.append(f"Line {line_number}: Invalid format")
                                continue
                                
                            category, subcategory, url = parts
                            
                            # Validate URL format
                            if not url.startswith('https://www.scribd.com/document/'):
                                invalid_lines.append(f"Line {line_number}: Invalid URL format")
                                continue
                                
                            self.processed_urls.add(url)
                            
                            # Initialize category/subcategory if needed
                            if category not in self.category_urls:
                                self.category_urls[category] = {}
                            if subcategory not in self.category_urls[category]:
                                self.category_urls[category][subcategory] = set()
                                
                            self.category_urls[category][subcategory].add(url)
                            
                        except Exception as e:
                            invalid_lines.append(f"Line {line_number}: {str(e)}")
                            continue
                    
                    # Log validation results
                    self.log_message(f"Loaded {len(self.processed_urls)} processed URLs")
                    if invalid_lines:
                        self.log_message("Validation issues found:")
                        for issue in invalid_lines:
                            self.log_message(f"- {issue}")
                            
        except Exception as e:
            self.log_message(f"Critical error loading processed URLs: {str(e)}")
            raise

    def add_url(self, category: str, subcategory: str, url: str) -> bool:
        """
        Add new URL to processed list with enhanced validation and tracking
        Args:
            category: Insurance category
            subcategory: Insurance subcategory
            url: Document URL
        Returns:
            bool: Success status
        """
        try:
            # Validate inputs
            if not all([category, subcategory, url]):
                self.log_message("Invalid input: All parameters are required")
                return False
                
            # Validate URL format
            if not url.startswith('https://www.scribd.com/document/'):
                self.log_message(f"Invalid URL format: {url}")
                return False
                
            # Check if URL is already processed
            if url in self.processed_urls:
                self.log_message(f"URL already processed: {url}")
                return False
                
            # Atomic write operation
            temp_file = f"{self.processed_urls_file}.temp"
            try:
                # Write to temporary file first
                with open(temp_file, 'w') as temp:
                    # Write existing content
                    if os.path.exists(self.processed_urls_file):
                        with open(self.processed_urls_file, 'r') as original:
                            temp.write(original.read())
                    # Append new URL
                    temp.write(f"{category}|{subcategory}|{url}\n")
                    
                # Rename temporary file to actual file
                os.replace(temp_file, self.processed_urls_file)
                
                # Update memory structures
                self.processed_urls.add(url)
                if category not in self.category_urls:
                    self.category_urls[category] = {}
                if subcategory not in self.category_urls[category]:
                    self.category_urls[category][subcategory] = set()
                self.category_urls[category][subcategory].add(url)
                
                # Track processing history
                timestamp = datetime.now().isoformat()
                self.url_processing_history[url] = {
                    'timestamp': timestamp,
                    'category': category,
                    'subcategory': subcategory
                }
                
                self.log_message(f"Successfully added URL: {url}")
                self.log_message(f"Category: {category}, Subcategory: {subcategory}")
                return True
                
            except Exception as e:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise
                
        except Exception as e:
            self.log_message(f"Error adding URL: {str(e)}")
            return False

    def is_processed(self, url: str) -> bool:
        """
        Check if URL has been processed
        Args:
            url: URL to check
        Returns:
            bool: True if already processed
        """
        return url in self.processed_urls

    def get_category_urls(self, category: str, subcategory: str = None) -> Set[str]:
        """
        Get processed URLs for category/subcategory
        Args:
            category: Insurance category
            subcategory: Optional subcategory
        Returns:
            set: Set of processed URLs
        """
        if category not in self.category_urls:
            return set()
            
        if subcategory:
            return self.category_urls[category].get(subcategory, set())
            
        # Return all URLs for category
        urls = set()
        for sub_urls in self.category_urls[category].values():
            urls.update(sub_urls)
        return urls

    def get_stats(self) -> Dict:
        """
        Get URL processing statistics
        Returns:
            dict: Statistics about processed URLs
        """
        stats = {
            'total_urls': len(self.processed_urls),
            'categories': {}
        }
        
        for category, subcats in self.category_urls.items():
            stats['categories'][category] = {
                'total': sum(len(urls) for urls in subcats.values()),
                'subcategories': {
                    subcat: len(urls) 
                    for subcat, urls in subcats.items()
                }
            }
            
        return stats

    def log_message(self, message: str) -> None:
        """Log a message with timestamp"""
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                with open(self.log_file, 'a') as f:
                    f.write(f'[{timestamp}] {message}\n')
            except Exception as e:
                print(f"Error writing to log: {str(e)}")
        print(message)



    def get_unprocessed_urls(self, urls: List[str]) -> List[str]:
        """
        Get list of URLs that haven't been processed yet
        Args:
            urls: List of URLs to check
        Returns:
            List[str]: Unprocessed URLs
        """
        return [url for url in urls if not self.is_processed(url)]

    def get_category_stats(self, category: str) -> Dict:
        """
        Get detailed statistics for a category
        Args:
            category: Category to get stats for
        Returns:
            Dict: Detailed category statistics
        """
        if category not in self.category_urls:
            return {'total': 0, 'subcategories': {}}
            
        stats = {
            'total': 0,
            'subcategories': {}
        }
        
        for subcategory, urls in self.category_urls[category].items():
            count = len(urls)
            stats['subcategories'][subcategory] = count
            stats['total'] += count
            
        return stats

    def cleanup(self) -> None:
        """Enhanced cleanup with detailed reporting"""
        try:
            stats = self.get_stats()
            self.log_message("\n=== Processed URLs Statistics ===")
            self.log_message(f"Total URLs Processed: {stats['total_urls']}")
            
            for category, cat_stats in stats['categories'].items():
                self.log_message(f"\nCategory: {category}")
                self.log_message(f"Total URLs: {cat_stats['total']}")
                self.log_message("Subcategory Breakdown:")
                for subcat, count in cat_stats['subcategories'].items():
                    self.log_message(f"  - {subcat}: {count} URLs")
                    
            # Backup processed URLs file
            self._backup_processed_urls()
            
        except Exception as e:
            self.log_message(f"Error during cleanup: {str(e)}")
            
            
    def _backup_processed_urls(self) -> None:
        """Create backup of processed URLs file"""
        try:
            if os.path.exists(self.processed_urls_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"{self.processed_urls_file}.{timestamp}.backup"
                with open(self.processed_urls_file, 'r') as source:
                    with open(backup_file, 'w') as backup:
                        backup.write(source.read())
                self.log_message(f"Created backup: {backup_file}")
        except Exception as e:
            self.log_message(f"Error creating backup: {str(e)}")