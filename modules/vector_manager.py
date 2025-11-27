import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import hashlib
import shutil

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def generate_hash(text):
    """สร้างรหัส MD5 จากข้อความ เพื่อใช้ตรวจสอบว่าเนื้อหาเปลี่ยนหรือไม่"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_project_paths():
    """ฟังก์ชันช่วยหา Path แบบอัตโนมัติ"""
    try:
        current_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        current_path = os.getcwd()
        
    project_root = current_path
    while True:
        if os.path.exists(os.path.join(project_root, 'data')):
            break
        parent = os.path.dirname(project_root)
        if parent == project_root:
            project_root = os.getcwd() # Fallback
            break
        project_root = parent
        
    return {
        "coursera": os.path.join(project_root, 'data', 'coursera_dataset.csv'),
        #"skilllane": os.path.join(project_root, 'data', 'skilllane_dataset.csv'),
        "futureskill": os.path.join(project_root, 'data', 'futureskill_dataset.csv'),
        "datacamp": os.path.join(project_root, 'data', 'datacamp_dataset.csv'),
        "db": os.path.join(project_root, 'vector_store')
    }

def load_all_data_sources(paths):
    """โหลด CSV ทั้งหมดมารวมกันเป็น list เดียว"""
    all_items = []
    
    # 1. Coursera
    # if os.path.exists(paths['coursera']):
    #     try:
    #         df = pd.read_csv(paths['coursera'])
    #         df['image_url'] = df['image_url'].fillna('') 
    #         all_items.extend(df.to_dict('records'))
    #         print(f"Loaded {len(df)} items from Coursera")
    #     except Exception as e:
    #         print(f"Error loading Coursera: {e}")

    #2. FutureSkill
    if os.path.exists(paths['futureskill']):
        try:
            df = pd.read_csv(paths['futureskill'])
            df['image_url'] = df['image_url'].fillna('')
            all_items.extend(df.to_dict('records'))
            print(f"Loaded {len(df)} items from FutureSkill")
        except Exception as e:
            print(f"Error loading FutureSkill: {e}")

    # 3. [เพิ่ม] DataCamp
    if os.path.exists(paths['datacamp']):
        try:
            df = pd.read_csv(paths['datacamp'])
            df['image_url'] = df['image_url'].fillna('')
            all_items.extend(df.to_dict('records'))
            print(f"Loaded {len(df)} items from DataCamp")
        except Exception as e:
            print(f"Error loading DataCamp: {e}")

    # 4. Internal Data
    # if os.path.exists(paths['internal']):
    #     try:
    #         df = pd.read_csv(paths['internal'])
    #         df['image_url'] = df['image_url'].fillna('')
    #         all_items.extend(df.to_dict('records'))
    #         print(f"Loaded {len(df)} internal items")
    #     except Exception as e:
    #         print(f"Error loading Internal: {e}")
            
    return all_items

def update_database_incremental():
    print("="*50)
    print("STARTING INCREMENTAL UPDATE")
    print("="*50)

    paths = get_project_paths()
    db_path = paths['db']

    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
    
    incoming_data = load_all_data_sources(paths)
    if not incoming_data:
        print("No data found in CSV files. Aborting.")
        return

    print("Reading existing database...")
    existing_data = db.get() 
    existing_ids = set(existing_data['ids'])
    
    existing_hashes = {}
    for id_, meta in zip(existing_data['ids'], existing_data['metadatas']):
        if meta:
            existing_hashes[id_] = meta.get('content_hash', '')
        
    docs_to_add = []      # เก็บ Document ที่จะ Insert/Update
    ids_to_add = []       # เก็บ ID
    ids_seen_in_source = set() # เก็บ ID ที่เจอใน CSV รอบนี้ (เอาไว้หาตัวลบ)

    print("Analyzing differences (Delta Check)...")

    for item in incoming_data:
        doc_id = str(item.get('id', 'unknown'))
        
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
            "title": item.get('title', ''),
            "url": item.get('url', ''),
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
            print(f"   Draft update found for: {item.get('title')}")
            should_update = True
        else:
            pass

        if should_update:
            doc = Document(page_content=clean_content, metadata=metadata)
            docs_to_add.append(doc)
            ids_to_add.append(doc_id)

    ids_to_delete = list(existing_ids - ids_seen_in_source)
    
    if ids_to_delete:
        print(f"Deleting {len(ids_to_delete)} old items...")
        db.delete(ids=ids_to_delete)
    else:
        print("No items to delete.")

    if docs_to_add:
        print(f"Found {len(docs_to_add)} items to upsert. Processing in batches...")
        
        batch_size = 4000 
        total_docs = len(docs_to_add)
        
        for i in range(0, total_docs, batch_size):
           
            batch_docs = docs_to_add[i : i + batch_size]
            batch_ids = ids_to_add[i : i + batch_size]
            
            print(f"   ↳ Upserting batch {i//batch_size + 1} ({len(batch_docs)} items)...")
            
            db.add_documents(batch_docs, ids=batch_ids)
            
        print(f"Upsert complete ({total_docs} items).")
    else:
        print("No new or updated items found.")

    print("="*50)
    print("INCREMENTAL UPDATE FINISHED")
    print("="*50)

def build_database():
    update_database_incremental()

if __name__ == "__main__":
    build_database()