#!/usr/bin/env python3
"""
Debug script to examine the DCWF Excel file structure.
"""

import pandas as pd
from pathlib import Path

def examine_dcwf_excel():
    """Examine the structure of the DCWF Excel file."""
    
    excel_path = "Documents/(U) 2025-01-24 DCWF Work Role Tool_v5.0.xlsx"
    
    try:
        # Read the Excel file
        excel_file = pd.ExcelFile(excel_path)
        print(f"Available sheets: {len(excel_file.sheet_names)} sheets")
        
        # Look at specific role sheets
        role_sheets = ["Software Developer", "Systems Developer", "Database Administrator", "IT Project Manager"]
        
        for role_name in role_sheets:
            if role_name in excel_file.sheet_names:
                print(f"\n=== {role_name} Sheet ===")
                role_df = pd.read_excel(excel_path, sheet_name=role_name)
                print(f"Shape: {role_df.shape}")
                print(f"Columns: {list(role_df.columns)}")
                
                # Look for task-related data
                print(f"\n=== First 5 rows of {role_name} ===")
                for i in range(min(5, len(role_df))):
                    row = role_df.iloc[i]
                    print(f"Row {i}: {dict(row)}")
                
                # Look for task columns
                task_cols = [col for col in role_df.columns if any(keyword in col.lower() 
                           for keyword in ['task', 'ksa', 'knowledge', 'skill', 'ability'])]
                if task_cols:
                    print(f"\nTask-related columns: {task_cols}")
                    
                    # Show some task examples
                    for col in task_cols[:2]:  # First 2 task columns
                        non_null = role_df[col].dropna()
                        if len(non_null) > 0:
                            print(f"\n{col} examples:")
                            for i, task in enumerate(non_null.head(3)):
                                print(f"  {i+1}. {str(task)[:150]}...")
        
        # Also examine DCWF Roles sheet more carefully
        print(f"\n=== DCWF Roles Detailed ===")
        roles_df = pd.read_excel(excel_path, sheet_name='DCWF Roles', header=1)  # Skip first row
        print(f"Shape: {roles_df.shape}")
        print(f"Columns: {list(roles_df.columns)}")
        
        # Look for software development related roles
        print(f"\n=== Software/Development Related Roles ===")
        for i, row in roles_df.iterrows():
            work_role = str(row.get('Work Role', ''))
            if any(keyword in work_role.lower() for keyword in ['software', 'developer', 'dev', 'program']):
                dcwf_code = row.get('DCWF Code', '')
                ncwf_id = row.get('NCWF ID', '')
                definition = str(row.get('Work Role Definition', ''))[:200]
                print(f"  {work_role} | Code: {dcwf_code} | ID: {ncwf_id}")
                print(f"    Definition: {definition}...")
                print()
            
    except Exception as e:
        print(f"Error examining DCWF Excel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_dcwf_excel() 