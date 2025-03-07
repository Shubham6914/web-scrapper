from google_sheets_sync import PivotSheetSync
import pandas as pd

def verify_sheets():
    SPREADSHEET_ID = '1xs7PMfsoJidcOaJuibbT3qq18aPsxzJj20tVz0kACN4'
    
    print(f"\nVerifying sheets in spreadsheet: {SPREADSHEET_ID}")
    
    try:
        # Initialize sync
        sync = PivotSheetSync(SPREADSHEET_ID)
        
        # Get spreadsheet info
        spreadsheet = sync.service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        # Print all sheets
        print("\nExisting sheets:")
        for sheet in spreadsheet['sheets']:
            title = sheet['properties']['title']
            sheet_id = sheet['properties']['sheetId']
            print(f"- {title} (ID: {sheet_id})")
            
        # Try to write test data
        test_data = pd.DataFrame({
            'Test Column': ['Test Data']
        })
        
        print("\nTrying to write to each sheet:")
        for sheet_name in ['Active Progress', 'Daily Progress', 'Summary View']:
            try:
                sync.update_sheet(test_data, sheet_name)
                print(f"✓ Successfully wrote to {sheet_name}")
            except Exception as e:
                print(f"✗ Failed to write to {sheet_name}: {str(e)}")
                
    except Exception as e:
        print(f"Verification failed: {str(e)}")

if __name__ == "__main__":
    verify_sheets()