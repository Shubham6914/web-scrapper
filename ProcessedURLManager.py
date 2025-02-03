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
        self.load_processed_urls()
        
    
    def load_processed_urls(self) -> None:
        """Load existing processed URLs from file"""
        try:
            if os.path.exists(self.processed_urls_file):
                with open(self.processed_urls_file, 'r') as f:
                    for line in f:
                        try:
                            category, subcategory, url = line.strip().split('|')
                            self.processed_urls.add(url)
                            
                            # Organize by category and subcategory
                            if category not in self.category_urls:
                                self.category_urls[category] = {}
                            if subcategory not in self.category_urls[category]:
                                self.category_urls[category][subcategory] = set()
                            self.category_urls[category][subcategory].add(url)
                            
                        except ValueError:
                            self.log_message(f"Invalid line format: {line}")
                            continue
                
                self.log_message(f"Loaded {len(self.processed_urls)} processed URLs")
        except Exception as e:
            self.log_message(f"Error loading processed URLs: {str(e)}")

    def add_url(self, category: str, subcategory: str, url: str) -> bool:
        """
        Add new URL to processed list
        Args:
            category: Insurance category
            subcategory: Insurance subcategory
            url: Document URL
        Returns:
            bool: Success status
        """
        try:
            if url not in self.processed_urls:
                # Add to memory
                self.processed_urls.add(url)
                
                # Add to category tracking
                if category not in self.category_urls:
                    self.category_urls[category] = {}
                if subcategory not in self.category_urls[category]:
                    self.category_urls[category][subcategory] = set()
                self.category_urls[category][subcategory].add(url)
                
                # Write to file
                with open(self.processed_urls_file, 'a') as f:
                    f.write(f"{category}|{subcategory}|{url}\n")
                
                self.log_message(f"Added new URL: {url}")
                self.log_message(f"Category: {category}, Subcategory: {subcategory}")
                return True
                
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

    def cleanup(self) -> None:
        """Perform any necessary cleanup"""
        # Currently just logs stats
        stats = self.get_stats()
        self.log_message("\nProcessed URLs Statistics:")
        self.log_message(f"Total URLs: {stats['total_urls']}")
        for category, cat_stats in stats['categories'].items():
            self.log_message(f"\n{category}:")
            self.log_message(f"Total URLs: {cat_stats['total']}")
            for subcat, count in cat_stats['subcategories'].items():
                self.log_message(f"  {subcat}: {count} URLs")