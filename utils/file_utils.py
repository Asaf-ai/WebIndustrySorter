import csv
import pandas as pd
import io

def parse_csv(uploaded_file):
    """
    Parse a CSV file uploaded by the user.
    
    Args:
        uploaded_file: The uploaded file object
        
    Returns:
        list: List of items from the CSV
    """
    try:
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Try pandas first
        try:
            df = pd.read_csv(uploaded_file)
            if len(df.columns) == 1:
                # Single column CSV
                items = df.iloc[:, 0].dropna().astype(str).tolist()
            else:
                # Multiple columns - use first column
                items = df.iloc[:, 0].dropna().astype(str).tolist()
                
        except Exception:
            # Fallback to csv module
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(content))
            items = []
            for row in csv_reader:
                if row and row[0].strip():
                    items.append(row[0].strip())
        
        # Remove duplicates and empty strings
        items = [item for item in items if item.strip()]
        items = list(dict.fromkeys(items))  # Remove duplicates while preserving order
        
        return items
    except Exception as e:
        raise Exception(f"Error parsing CSV: {str(e)}")

def export_to_csv(results):
    """
    Export classification results to CSV.
    
    Args:
        results (list): List of classification results
        
    Returns:
        str: CSV content as string
    """
    try:
        df = pd.DataFrame(results)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    except Exception as e:
        raise Exception(f"Error exporting to CSV: {str(e)}")
