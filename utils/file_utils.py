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
        
        # Read the content as text
        content = uploaded_file.read().decode('utf-8')
        
        # Remove BOM character if present
        if content.startswith('\ufeff'):
            content = content.replace('\ufeff', '')
            
        # Simple parsing for robustness - split by newlines
        lines = content.split('\n')
        items = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Handle CSV with or without quotes
            if ',' in line:
                # If it's a comma-separated line, take the first item
                parts = line.split(',')
                item = parts[0].strip()
                
                # Remove quotes if present
                if item.startswith('"') and item.endswith('"'):
                    item = item[1:-1]
                elif item.startswith("'") and item.endswith("'"):
                    item = item[1:-1]
                    
                if item:
                    items.append(item)
            else:
                # Simple line with just one item
                item = line.strip()
                if item:
                    items.append(item)
        
        # Remove duplicates while preserving order
        unique_items = []
        seen = set()
        
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        
        return unique_items
        
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
