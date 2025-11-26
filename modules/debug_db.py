from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

# --- 1. ฟังก์ชันหา Path อัจฉริยะ (ที่คุณให้มา) ---
def get_project_paths():
    """ฟังก์ชันช่วยหา Path แบบอัตโนมัติ"""
    try:
        current_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        current_path = os.getcwd()
        
    project_root = current_path
    while True:
        # เดินหาโฟลเดอร์ data เพื่อยืนยันว่าเป็น Root Project
        if os.path.exists(os.path.join(project_root, 'data')):
            break
        parent = os.path.dirname(project_root)
        if parent == project_root:
            project_root = os.getcwd() # Fallback
            break
        project_root = parent
        
    return {
        "db": os.path.join(project_root, 'vector_store')
    }

# --- 2. ฟังก์ชันตรวจสอบข้อมูล ---
def check_db_content():
    # เรียกใช้ฟังก์ชันหา Path
    paths = get_project_paths()
    db_path = paths['db']
    
    print(f"Checking Database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Error: Database folder not found.")
        print("Suggestion: Run 'python update_pipeline.py' first.")
        return

    # โหลด Database
    try:
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
        
        # ลองค้นหา (Test Query)
        query = "Python"
        print(f"\nTest Searching for: '{query}'...")
        results = db.similarity_search(query, k=1)
        
        if results:
            doc = results[0]
            print("-" * 40)
            print("✅ Found Data!")
            print(f"Title:     {doc.metadata.get('title')}")
            print(f"Source:    {doc.metadata.get('source')}")
            print(f"Category:  {doc.metadata.get('category')}")
            
            # เช็คจุดสำคัญ: รูปภาพ
            img_url = doc.metadata.get('image_url')
            print(f"Image URL: {img_url}")
            
            if img_url and str(img_url).lower() != 'nan':
                print("status:    OK (Has Image)")
            else:
                print("status:    WARNING (No Image / nan)")
            print("-" * 40)
        else:
            print("⚠️ Database loaded, but search returned no results.")
            
    except Exception as e:
        print(f"❌ Error loading database: {e}")

if __name__ == "__main__":
    check_db_content()