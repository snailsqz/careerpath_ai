import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import hashlib
import shutil

# ใช้ Model เดิม
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

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
        "skilllane": os.path.join(project_root, 'data', 'skilllane_dataset.csv'),
        "db": os.path.join(project_root, 'vector_store')
    }

def load_all_data_sources(paths):
    """โหลด CSV ทั้งหมดมารวมกันเป็น list เดียว"""
    all_items = []
    
    # 1. Load Coursera
    if os.path.exists(paths['coursera']):
        try:
            df = pd.read_csv(paths['coursera'])
            # แปลงเป็น dict เพื่อให้จัดการง่าย
            all_items.extend(df.to_dict('records'))
            print(f"Loaded {len(df)} items from Coursera")
        except Exception as e:
            print(f"Error loading Coursera CSV: {e}")

    # 2. Load SkillLane
    if os.path.exists(paths['skilllane']):
        try:
            df = pd.read_csv(paths['skilllane'])
            all_items.extend(df.to_dict('records'))
            print(f"Loaded {len(df)} items from SkillLane")
        except Exception as e:
            print(f"Error loading SkillLane CSV: {e}")
            
    return all_items

def update_database_incremental():
    print("="*50)
    print("STARTING INCREMENTAL UPDATE")
    print("="*50)

    paths = get_project_paths()
    db_path = paths['db']

    # 1. เตรียม Model และ DB
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    # เชื่อมต่อกับ DB เดิม (ถ้าไม่มี มันจะสร้างใหม่เอง)
    db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
    
    # 2. ดึงข้อมูล "ของใหม่" (Incoming Data) จาก CSV
    incoming_data = load_all_data_sources(paths)
    if not incoming_data:
        print("No data found in CSV files. Aborting.")
        return

    # 3. ดึงข้อมูล "ของเดิม" (Existing Data) จาก DB
    # ใช้ .get() เพื่อดึง ID และ Metadata ทั้งหมดออกมาเช็ค
    print("Reading existing database...")
    existing_data = db.get() 
    existing_ids = set(existing_data['ids'])
    
    # สร้าง Map: ID -> Hash เดิม (เอาไว้เช็คว่าเนื้อหาเปลี่ยนไหม)
    existing_hashes = {}
    for id_, meta in zip(existing_data['ids'], existing_data['metadatas']):
        if meta:
            existing_hashes[id_] = meta.get('content_hash', '')

    # --- เตรียมตัวแปรสำหรับ Batch Operation ---
    docs_to_add = []      # เก็บ Document ที่จะ Insert/Update
    ids_to_add = []       # เก็บ ID
    ids_seen_in_source = set() # เก็บ ID ที่เจอใน CSV รอบนี้ (เอาไว้หาตัวลบ)

    print("Analyzing differences (Delta Check)...")

    # 4. วนลูปเทียบข้อมูล (The Core Logic)
    for item in incoming_data:
        doc_id = str(item.get('id', 'unknown'))
        ids_seen_in_source.add(doc_id)
        
        # เตรียม Content
        content = f"""
        Title: {item.get('title', '')}
        Description: {item.get('description', '')}
        Level: {item.get('level', '')}
        Category: {item.get('category', '')}
        """
        clean_content = content.strip()
        
        # คำนวณ Hash ของเนื้อหาใหม่
        current_hash = generate_hash(clean_content)
        
        # เตรียม Metadata (เพิ่ม content_hash เข้าไป)
        metadata = {
            "id": doc_id,
            "title": item.get('title', ''),
            "url": item.get('url', ''),
            "level": str(item.get('level', '')),
            "duration": str(item.get('duration', '')),
            "source": str(item.get('source', 'Unknown')),
            "content_hash": current_hash 
        }

        # --- LOGIC การตัดสินใจ ---
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

    # 5. หา "ของที่ต้องลบ" (Deleted Items)
    # คือ ID ที่มีใน DB แต่ไม่มีใน CSV รอบนี้
    ids_to_delete = list(existing_ids - ids_seen_in_source)

    
    # Action 1: DELETE
    if ids_to_delete:
        print(f"Deleting {len(ids_to_delete)} old items...")
        db.delete(ids=ids_to_delete)
    else:
        print("No items to delete.")

    # Action 2: ADD / UPDATE (Chroma ใช้ .add_documents จะ Upsert ให้เอง)
    if docs_to_add:
        print(f"Upserting {len(docs_to_add)} new/updated items...")
        db.add_documents(docs_to_add, ids=ids_to_add)
        print(f"Upsert complete.")
    else:
        print("No new or updated items found.")

    print("="*50)
    print("INCREMENTAL UPDATE FINISHED")
    print("="*50)

# เปลี่ยนชื่อให้เรียกใช้ได้เหมือนเดิม
def build_database():
    update_database_incremental()

if __name__ == "__main__":
    build_database()