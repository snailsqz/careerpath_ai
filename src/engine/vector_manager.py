import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import hashlib
import shutil
from typing import List, Dict, Any

from src.config import (
    DATA_DIR, VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def load_all_data_sources() -> List[Dict[str, Any]]:
    all_items = []
    
    # Map source name to filename
    sources = {
        "Coursera": "coursera_dataset.csv",
        "FutureSkill": "futureskill_dataset.csv",
        "DataCamp": "datacamp_dataset.csv",
        "Khan Academy": "khan_dataset.csv"
    }

    for source_name, filename in sources.items():
        file_path = DATA_DIR / filename
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                # Handle NaNs in image_url
                if 'image_url' in df.columns:
                    df['image_url'] = df['image_url'].fillna('')
                else:
                    df['image_url'] = ''
                    
                records = df.to_dict('records')
                # Inject source if missing? Original code didn't seem to explicitly force it if CSV has it.
                # Assuming CSV has 'source' column or logic handles it.
                
                all_items.extend(records)
                logger.info(f"Loaded {len(records)} items from {source_name}")
            except Exception as e:
                logger.error(f"Error loading {source_name}: {e}")
        else:
             logger.debug(f"Data file for {source_name} not found at {file_path}")

    return all_items

def update_database_incremental():
    logger.info("="*50)
    logger.info("STARTING INCREMENTAL UPDATE")
    logger.info("="*50)

    db_path = str(VECTOR_STORE_DIR)
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    # Chroma checks if dir exists
    db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
    
    incoming_data = load_all_data_sources()
    if not incoming_data:
        logger.warning("No data found in CSV files. Aborting.")
        return

    logger.info("Reading existing database...")
    existing_data = db.get() 
    existing_ids = set(existing_data['ids'])
    
    existing_hashes = {}
    if existing_data['ids'] and existing_data['metadatas']:
        for id_, meta in zip(existing_data['ids'], existing_data['metadatas']):
            if meta:
                existing_hashes[id_] = meta.get('content_hash', '')
        
    docs_to_add = []      
    ids_to_add = []       
    ids_seen_in_source = set() 

    logger.info("Analyzing differences (Delta Check)...")

    for item in incoming_data:
        doc_id = str(item.get('id', 'unknown'))
        
        # Simple dedupe in source
        if doc_id in ids_seen_in_source:
            continue
        ids_seen_in_source.add(doc_id)
        
        content = f"""
        Title: {item.get('title', '')}
        Description: {item.get('description', '')}
        Level: {item.get('level', '')}
        Category: {item.get('category', '')}
        """
        clean_content = content.strip()
        current_hash = generate_hash(clean_content)
        
        metadata = {
            "id": doc_id,
            "title": str(item.get('title', '')),
            "url": str(item.get('url', '')),
            "level": str(item.get('level', '')),
            "category": str(item.get('category', '')),
            "image_url": str(item.get('image_url', '')),
            "duration": str(item.get('duration', '')),
            "source": str(item.get('source', 'Unknown')),
            "content_hash": current_hash 
        }

        should_update = False
        
        if doc_id not in existing_ids:
            should_update = True
        elif existing_hashes.get(doc_id) != current_hash:
            logger.debug(f"Draft update found for: {item.get('title')}")
            should_update = True

        if should_update:
            doc = Document(page_content=clean_content, metadata=metadata)
            docs_to_add.append(doc)
            ids_to_add.append(doc_id)

    ids_to_delete = list(existing_ids - ids_seen_in_source)
    
    if ids_to_delete:
        logger.info(f"Deleting {len(ids_to_delete)} old items...")
        db.delete(ids=ids_to_delete)
    else:
        logger.info("No items to delete.")

    if docs_to_add:
        logger.info(f"Found {len(docs_to_add)} items to upsert. Processing in batches...")
        
        batch_size = 4000 
        total_docs = len(docs_to_add)
        
        for i in range(0, total_docs, batch_size):
            batch_docs = docs_to_add[i : i + batch_size]
            batch_ids = ids_to_add[i : i + batch_size]
            
            logger.info(f"   Upserting batch {i//batch_size + 1} ({len(batch_docs)} items)...")
            db.add_documents(batch_docs, ids=batch_ids)
            
        logger.info(f"Upsert complete ({total_docs} items).")
    else:
        logger.info("No new or updated items found.")

    logger.info("="*50)
    logger.info("INCREMENTAL UPDATE FINISHED")
    logger.info("="*50)

def build_database():
    update_database_incremental()

if __name__ == "__main__":
    build_database()