from pivot_table_manager import PivotTableManager
from ProgressTracker import ProgressTracker

def test_pivot_data():
    print("Testing pivot table data generation...")
    
    # Initialize components
    tracker = ProgressTracker('logs')
    pivot_manager = PivotTableManager(
        progress_tracker=tracker,
        spreadsheet_id='1xs7PMfsoJidcOaJuibbT3qq18aPsxzJj20tVz0kACN4'
    )
    
    # Generate and show sample data
    print("\nGenerating reports...")
    pivot_manager.generate_reports()

if __name__ == "__main__":
    test_pivot_data()