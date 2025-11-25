import os
import pandas as pd
import sys

# Import Module
try:
    from modules.fetch_courses import fetch_courses
    from modules.vector_manager import build_database
except ImportError as e:
    print(f"Import Error: {e}")
    print("Check if __init__.py exists in modules folder.")
    sys.exit(1)

def save_to_data_folder(data_list, filename):
    """
    Saves list of data to the 'data' folder at the project root.
    """
    if not data_list:
        print(f"Warning: No data to save for {filename}")
        return

    # 1. Get root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Define data directory path
    data_dir = os.path.join(project_root, 'data')
    
    # 3. Create directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data folder at: {data_dir}")

    # 4. Construct full file path
    full_path = os.path.join(data_dir, filename)
    
    # 5. Save to CSV
    df = pd.DataFrame(data_list)
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} records to: {full_path}")

def run_pipeline():
    print("="*50)
    print("STARTING UPDATE PIPELINE (COURSERA ONLY)")
    print("="*50)

    # --- STEP 1: Fetch & Save ---
    print("\n[1/2] Fetching Coursera Data...")
    try:
        # Fetch 50 pages (~5,000 courses)
        coursera_data = fetch_courses(max_pages=100)
        
        # Save to data folder
        save_to_data_folder(coursera_data, "coursera_dataset.csv")
        
    except Exception as e:
        print(f"Error fetching Coursera: {e}")

    # --- STEP 2: Rebuild DB ---
    print("\n[2/2] Rebuilding Vector Database...")
    try:
        # Calls the build_database function from vector_manager
        build_database()
    except Exception as e:
        print(f"Error building database: {e}")

    print("\n" + "="*50)
    print("PIPELINE COMPLETED")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()