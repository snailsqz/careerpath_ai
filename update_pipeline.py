import sys
import pandas as pd
from src.careerpath_ai.config import DATA_DIR
from src.careerpath_ai.ingestion.coursera_fetch import fetch_courses
from src.careerpath_ai.ingestion.futureskills_fetch import fetch_futureskill
from src.careerpath_ai.ingestion.datacamp_fetch import fetch_datacamp_courses
from src.careerpath_ai.engine.vector_manager import build_database
from src.careerpath_ai.utils.logger import get_logger

logger = get_logger(__name__)

def save_to_data_folder(data_list, filename):
    if not data_list:
        logger.warning(f"No data to save for {filename}")
        return

    full_path = DATA_DIR / filename
    
    # Ensure directory exists
    DATA_DIR.mkdir(exist_ok=True, parents=True)

    df = pd.DataFrame(data_list)
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    logger.info(f"Saved {len(df)} records to: {full_path}")

def run_pipeline():
    logger.info("="*50)
    logger.info("STARTING UPDATE PIPELINES")
    logger.info("="*50)

    logger.info("[1/5] Fetching Coursera Data...")
    try:
        coursera_data = fetch_courses(max_pages=170, start_page_num=1)
        save_to_data_folder(coursera_data, "coursera_dataset.csv")
    except Exception as e:
        logger.error(f"Error fetching Coursera: {e}")

    logger.info("[2/5] Fetching FutureSkill Data...")
    try:
        futureskill_data = fetch_futureskill(limit_pages=100)
        save_to_data_folder(futureskill_data, "futureskill_dataset.csv")
    except Exception as e:
        logger.error(f"Error fetching FutureSkill: {e}")
        
    logger.info("[3/5] Fetching DataCamp Data...")
    try:
        datacamp_data = fetch_datacamp_courses(max_limit=1000)
        save_to_data_folder(datacamp_data, "datacamp_dataset.csv")
    except Exception as e:
        logger.error(f"Error fetching DataCamp: {e}")
        
    logger.info("[4/5] Rebuilding Vector Database...")
    try:
        build_database()
    except Exception as e:
        logger.error(f"Error building database: {e}")

    logger.info("="*50)
    logger.info("PIPELINE COMPLETED")
    logger.info("="*50)

if __name__ == "__main__":
    run_pipeline()