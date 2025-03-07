import pandas as pd
from datetime import datetime
from typing import Dict, Any
from google_sheets_sync import PivotSheetSync  # Import the new class

class PivotTableManager:
    def __init__(self, progress_tracker, spreadsheet_id=None):
        self.progress_tracker = progress_tracker
        self.target_downloads = 100
        self.google_sync = None
        
        if spreadsheet_id:
            self.google_sync = PivotSheetSync(spreadsheet_id)
            # Generate initial reports
            self.generate_reports()

    def create_active_progress_df(self) -> pd.DataFrame:
        """Create active progress DataFrame"""
        progress_data = []
        downloads = self.progress_tracker.progress_data['completed']['downloads']
        current = self.progress_tracker.progress_data['current_position']
        last_processed = self.progress_tracker.progress_data['last_processed']
        
        for category in downloads:
            for subcategory, count in downloads[category].items():
                status = "Completed" if count >= self.target_downloads else \
                        "In Progress" if count > 0 else "Not Started"
                
                # Get last updated timestamp
                last_updated = "-"
                if status != "Not Started":
                    if (category == last_processed['category'] and 
                        subcategory == last_processed['subcategory']):
                        # Convert timestamp format
                        timestamp = last_processed['timestamp']
                        try:
                            # Convert from "20250306_164229" to readable format
                            dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                            last_updated = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            last_updated = timestamp
                
                # Mark current task
                is_current = (category == current['category'] and 
                            subcategory == current['subcategory'])
                
                progress_data.append({
                    'Category': category,
                    'Subcategory': subcategory,
                    'Downloaded': count,
                    'Target': self.target_downloads,
                    'Progress': f"{count}/{self.target_downloads}",
                    'Status': status,
                    'Last Updated': last_updated,
                    'Current Task': "→" if is_current else ""
                })
        
        df = pd.DataFrame(progress_data)
        # Reorder columns to put Last Updated before Current Task
        columns = ['Category', 'Subcategory', 'Downloaded', 'Target', 
                'Progress', 'Status', 'Last Updated', 'Current Task']
        df = df[columns]
        print(f"Active Progress Data Sample:\n{df.head()}")
        return df   


    def create_daily_progress_df(self) -> pd.DataFrame:
        """Create daily progress DataFrame"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = []
        downloads = self.progress_tracker.progress_data['completed']['downloads']
        
        for category in downloads:
            # Calculate actual downloads for this category
            category_downloads = sum(count for count in downloads[category].values())
            
            # Calculate total target (100 per subcategory)
            total_subcats = len(downloads[category])
            target_total = total_subcats * self.target_downloads
            
            # Calculate progress percentage
            progress_pct = (category_downloads / target_total * 100) if target_total > 0 else 0
            
            daily_data.append({
                'Date': today,
                'Category': category,
                'Files Downloaded Today': category_downloads,
                'Total Target': target_total,
                'Progress': f"{category_downloads}/{target_total}",
                'Status': 'Completed' if progress_pct >= 100 else 
                        'In Progress' if category_downloads > 0 else 'Not Started'
            })
        
        df = pd.DataFrame(daily_data)
        # Sort by Files Downloaded Today in descending order
        df = df.sort_values('Files Downloaded Today', ascending=False)
        print(f"Daily Progress Data Sample:\n{df.head()}")
        return df

    def create_summary_df(self) -> pd.DataFrame:
        """Create summary DataFrame"""
        summary_data = []
        downloads = self.progress_tracker.progress_data['completed']['downloads']
        
        for category in downloads:
            completed = sum(1 for count in downloads[category].values() 
                          if count >= self.target_downloads)
            in_progress = sum(1 for count in downloads[category].values() 
                            if 0 < count < self.target_downloads)
            not_started = sum(1 for count in downloads[category].values() 
                            if count == 0)
            
            summary_data.append({
                'Category': category,
                'Total Subcategories': len(downloads[category]),
                'Completed': completed,
                'In Progress': in_progress,
                'Not Started': not_started,
                'Completion Rate': f"{(completed/len(downloads[category])*100):.1f}%"
            })
        
        df = pd.DataFrame(summary_data)
        print(f"Summary Data Sample:\n{df.head()}")  # Debug print
        return df

    def _get_category_status(self, category: str, subcategories: dict) -> str:
        """Determine category status"""
        if all(count >= self.target_downloads for count in subcategories.values()):
            return "Completed"
        elif any(count > 0 for count in subcategories.values()):
            return "In Progress"
        return "Not Started"

    def generate_reports(self):
        """Generate all reports"""
        try:
            if self.google_sync:
                print("Generating progress reports...")
                
                # Create DataFrames
                active_df = self.create_active_progress_df()
                daily_df = self.create_daily_progress_df()
                summary_df = self.create_summary_df()

                try:
                    # Update sheets one by one with error handling
                    print("Updating Active Progress sheet...")
                    self.google_sync.update_sheet(data_frame=active_df, sheet_name='Active Progress')
                except Exception as e:
                    print(f"Error updating Active Progress: {str(e)}")

                try:
                    print("Updating Daily Progress sheet...")
                    self.google_sync.update_sheet(data_frame=daily_df, sheet_name='Daily Progress')
                except Exception as e:
                    print(f"Error updating Daily Progress: {str(e)}")

                try:
                    print("Updating Summary View sheet...")
                    self.google_sync.update_sheet(data_frame=summary_df, sheet_name='Summary View')
                except Exception as e:
                    print(f"Error updating Summary View: {str(e)}")

                print("All reports generated successfully")

        except Exception as e:
            print(f"Error generating reports: {str(e)}")
            
            
   