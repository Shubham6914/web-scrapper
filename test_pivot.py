import pandas as pd
from ProgressTracker import ProgressTracker
from pivot_table_manager import PivotTableManager
from google_sheet import GoogleSheetsSync

def test_google_sheets_connection():
    """Test Google Sheets connection"""
    try:
        print("Testing Google Sheets connection...")
        sync = GoogleSheetsSync('1xs7PMfsoJidcOaJuibbT3qq18aPsxzJj20tVz0kACN4')
        print("✓ Google Sheets connection successful")
        return sync
    except Exception as e:
        print(f"✗ Google Sheets connection failed: {str(e)}")
        return None

def test_progress_tracker():
    """Test Progress Tracker"""
    try:
        print("Testing Progress Tracker...")
        tracker = ProgressTracker('logs')
        print("✓ Progress Tracker initialized")
        return tracker
    except Exception as e:
        print(f"✗ Progress Tracker failed: {str(e)}")
        return None

def test_pivot_manager():
    """Test Pivot Table Manager"""
    try:
        print("Testing Pivot Table Manager...")
        tracker = ProgressTracker('logs')
        pivot = PivotTableManager(
            progress_tracker=tracker,
            spreadsheet_id='1xs7PMfsoJidcOaJuibbT3qq18aPsxzJj20tVz0kACN4'
        )
        print("✓ Pivot Table Manager initialized")
        return pivot
    except Exception as e:
        print(f"✗ Pivot Table Manager failed: {str(e)}")
        return None

def test_sheet_creation():
    """Test sheet creation"""
    try:
        print("Testing sheet creation...")
        sync = GoogleSheetsSync('1xs7PMfsoJidcOaJuibbT3qq18aPsxzJj20tVz0kACN4')
        
        # Test with sample data
        test_df = pd.DataFrame({
            'Category': ['Test Category'],
            'Status': ['Test Status']
        })
        
        # Try creating and updating each sheet
        sheets = ['Active Progress', 'Daily Progress', 'Summary View']
        for sheet in sheets:
            print(f"Testing {sheet}...")
            sync.update_sheet(test_df, sheet)
            print(f"✓ {sheet} created/updated successfully")
            
    except Exception as e:
        print(f"✗ Sheet creation failed: {str(e)}")

def test_full_pivot_generation():
    """Test full pivot table generation"""
    try:
        print("Testing full pivot generation...")
        pivot = test_pivot_manager()
        if pivot:
            print("Generating reports...")
            pivot.generate_reports()
            print("✓ Reports generated successfully")
    except Exception as e:
        print(f"✗ Pivot generation failed: {str(e)}")

if __name__ == "__main__":
    print("Starting pivot table tests...")
    print("-" * 50)
    
    # Run tests
    test_google_sheets_connection()
    print("-" * 50)
    test_progress_tracker()
    print("-" * 50)
    test_sheet_creation()
    print("-" * 50)
    test_full_pivot_generation()