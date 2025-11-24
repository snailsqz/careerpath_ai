import os
import pandas as pd
import sys

try:
    from modules.fetch_courses import fetch_courses
    from modules.vector_manager import build_database
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def save_dataframe(data_list, filename):
    if not data_list:
        print(f"Warning: No data to save for {filename}")
        return

    current_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_path, 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    filepath = os.path.join(data_dir, filename)
    
    df = pd.DataFrame(data_list)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} records to: {filename}")

def run_pipeline():
    print("STARTING UPDATE PIPELINE (COURSERA ONLY)")

    print("[1/2] Fetching Coursera Data...")
    try:
        coursera_data = fetch_courses(max_pages=50)
        save_dataframe(coursera_data, "coursera_dataset.csv")
    except Exception as e:
        print(f"Error fetching Coursera: {e}")

    print("\n[2/2] Rebuilding Vector Database...")
    try:
        build_database()
    except Exception as e:
        print(f"Error building database: {e}")

    print("\nPIPELINE COMPLETED")

if __name__ == "__main__":
    run_pipeline()