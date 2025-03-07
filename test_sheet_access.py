from google_sheets_sync import PivotSheetSync
import pandas as pd

def test_sheet_access():
    print("Starting sheet access test...")
    
    # Your spreadsheet ID
    SPREADSHEET_ID = '1xs7PMfsoJidcOaJuibbT3qq18aPsxzJj20tVz0kACN4'
    
    try:
        # Initialize PivotSheetSync instead of GoogleSheetsSync
        print("Initializing Google Sheets connection...")
        sync = PivotSheetSync(SPREADSHEET_ID)
        
        # Create a simple test DataFrame
        test_data = {
            'Category': ['BUSINESS INSURANCE'],
            'Subcategory': ['General Liability Insurance'],
            'Progress': ['140/100'],
            'Status': ['Completed'],
            'Last Updated': ['2025-03-06']
        }
        df = pd.DataFrame(test_data)
        
        # Try to update each sheet
        sheets = ['Active Progress', 'Daily Progress', 'Summary View']
        
        for sheet_name in sheets:
            print(f"\nTrying to update {sheet_name}...")
            try:
                # Call update_sheet with named parameters
                sync.update_sheet(data_frame=df, sheet_name=sheet_name)
                print(f"Successfully updated {sheet_name}")
            except Exception as e:
                print(f"Error updating {sheet_name}: {str(e)}")
        
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_sheet_access()