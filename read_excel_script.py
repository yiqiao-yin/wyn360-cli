#!/usr/bin/env python3
"""
Script to read and analyze Excel spreadsheet data
"""
import pandas as pd
import openpyxl
from pathlib import Path

def analyze_excel_file(file_path):
    """Analyze an Excel file and return detailed information about its contents"""
    
    file_path = Path(file_path)
    if not file_path.exists():
        return f"❌ File not found: {file_path}"
    
    try:
        # Load workbook to get sheet names
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet_names = workbook.sheetnames
        
        print(f"📊 **Excel File Analysis: {file_path.name}**\n")
        print(f"**Number of sheets:** {len(sheet_names)}")
        print(f"**Sheet names:** {', '.join(sheet_names)}\n")
        
        # Analyze each sheet
        for sheet_name in sheet_names:
            print(f"## 📋 Sheet: '{sheet_name}'\n")
            
            # Read with pandas for better analysis
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                
                print(f"**Dimensions:** {df.shape[0]} rows × {df.shape[1]} columns")
                print(f"**Column names:** {list(df.columns)}")
                
                # Show data types
                print(f"\n**Data types:**")
                for col, dtype in df.dtypes.items():
                    print(f"  - {col}: {dtype}")
                
                # Show first few rows
                print(f"\n**First 5 rows:**")
                print(df.head().to_string(index=True))
                
                # Show basic statistics for numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    print(f"\n**Summary statistics for numeric columns:**")
                    print(df[numeric_cols].describe().to_string())
                
                # Check for missing values
                missing_data = df.isnull().sum()
                if missing_data.any():
                    print(f"\n**Missing values:**")
                    for col, missing_count in missing_data[missing_data > 0].items():
                        print(f"  - {col}: {missing_count} missing values")
                else:
                    print(f"\n**✅ No missing values found**")
                
                # Show unique values for categorical columns (if reasonable number)
                categorical_cols = df.select_dtypes(include=['object']).columns
                for col in categorical_cols:
                    unique_count = df[col].nunique()
                    if unique_count <= 20:  # Only show if reasonable number
                        print(f"\n**Unique values in '{col}' ({unique_count} unique):**")
                        print(f"  {df[col].unique().tolist()}")
                    else:
                        print(f"\n**'{col}' has {unique_count} unique values (too many to display)**")
                
                print("\n" + "="*80 + "\n")
                
            except Exception as e:
                print(f"❌ Error reading sheet '{sheet_name}': {str(e)}\n")
        
        workbook.close()
        
    except Exception as e:
        print(f"❌ Error analyzing Excel file: {str(e)}")

if __name__ == "__main__":
    file_path = "/home/workbench/wyn360-cli/wyn360-cli/tests/test_files/sales_invoice.xlsx"
    analyze_excel_file(file_path)