import os
import pandas as pd
import sys

# Import Module
try:
    from modules.coursera_fetch import fetch_courses
    from modules.futureskills_fetch import fetch_futureskill
    from modules.datacamp_fetch import fetch_datacamp_courses
    from modules.vector_manager import build_database
except ImportError as e:
    print(f"Import Error: {e}")
    print("Check if __init__.py exists in modules folder.")
    sys.exit(1)

def save_to_data_folder(data_list, filename):
    if not data_list:
        print(f"Warning: No data to save for {filename}")
        return

    project_root = os.path.dirname(os.path.abspath(__file__))
    
    data_dir = os.path.join(project_root, 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data folder at: {data_dir}")

    full_path = os.path.join(data_dir, filename)

    df = pd.DataFrame(data_list)
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} records to: {full_path}")

def run_pipeline():
    print("="*50)
    print("STARTING UPDATE PIPELINEs")
    print("="*50)

    # print("\n[1/5] Fetching Coursera Data...")
    # try:
    #     coursera_data = fetch_courses(max_pages=100, start_page_num=1)
    #     save_to_data_folder(coursera_data, "coursera_dataset.csv")
        
    # except Exception as e:
    #     print(f"Error fetching Coursera: {e}")

    print("\n[2/5] Fetching FutureSkill Data...")
    try:
        futureskill_data = fetch_futureskill(limit_pages=100)
        save_to_data_folder(futureskill_data, "futureskill_dataset.csv")
        
    except Exception as e:
        print(f"Error fetching FutureSkill: {e}")
        
    print("\n[3/5] Fetching DataCamp Data...")
    try:
        datacamp_data = fetch_datacamp_courses(max_limit=1000)
        save_to_data_folder(datacamp_data, "datacamp_dataset.csv")
    except Exception as e:
        print(f"Error fetching DataCamp: {e}")
        
    print("\n[5/5] Rebuilding Vector Database...")
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