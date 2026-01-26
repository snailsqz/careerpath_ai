from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
import pandas as pd

# ใช้ Model เดียวกับที่คุณสร้าง DB (สำคัญมาก! ต้องตรงกัน)
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def get_db_path():
    try:
        current_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        current_path = os.getcwd()
    
    # เดินหา folder vector_store
    project_root = current_path
    while True:
        if os.path.exists(os.path.join(project_root, 'data')):
            break
        parent = os.path.dirname(project_root)
        if parent == project_root:
            project_root = os.getcwd()
            break
        project_root = parent
        
    return os.path.join(project_root, 'vector_store')

def inspect():
    db_path = get_db_path()
    print(f"📂 Database Path: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Error: ไม่พบโฟลเดอร์ Database")
        return

    try:
        # 1. เชื่อมต่อ DB
        embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
        
        # 2. เช็คจำนวนข้อมูล (Count)
        # Chroma เก็บข้อมูลใน collection (default ชื่อ 'langchain')
        collection = db._collection 
        count = collection.count()
        
        print(f"\n📊 Total Documents: {count:,} items")
        print("-" * 50)

        if count == 0:
            print("⚠️ Database ว่างเปล่า")
            return

        # 3. ขอดูเนื้อหา 5 ตัวแรก (Peek)
        print("👀 Peeking at first 5 items:\n")
        
        # ดึงข้อมูลออกมา (limit 5)
        data = collection.get(limit=5)
        
        # data จะเป็น dictionary ที่มี keys: ['ids', 'embeddings', 'documents', 'metadatas']
        ids = data['ids']
        metadatas = data['metadatas']
        documents = data['documents']

        for i in range(len(ids)):
            print(f"[{i+1}] ID: {ids[i]}")
            print(f"    Title: {metadatas[i].get('title', 'N/A')}")
            print(f"    Source: {metadatas[i].get('source', 'N/A')}")
            print(f"    Category: {metadatas[i].get('category', 'N/A')}")
            print(f"    Content Preview: {documents[i][:100]}...") # โชว์เนื้อหา 100 ตัวอักษรแรก
            print("-" * 30)

        # 4. (แถม) สรุปแยกตาม Source
        # ดึง Metadata ทั้งหมดมา Group by (ระวังช้าถ้าข้อมูลเยอะมาก)
        if count < 10000: # ถ้าไม่เยอะมากค่อยทำ
            print("\n📈 Statistics by Source:")
            all_data = collection.get()
            df = pd.DataFrame(all_data['metadatas'])
            if 'source' in df.columns:
                print(df['source'].value_counts().to_markdown())
            else:
                print("No 'source' field found in metadata.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect()