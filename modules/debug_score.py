from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

# ใช้โมเดลตัวเดียวกับที่คุณเพิ่งแก้
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def get_db_path():
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
            project_root = os.getcwd()
            break
        project_root = parent
        
    return os.path.join(project_root, 'vector_store')

def debug_search():
    db_path = get_db_path()
    print(f"📂 Loading DB from: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Database not found! Run update_pipeline.py first.")
        return

    # โหลด DB
    try:
        embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
    except Exception as e:
        print(f"❌ Error loading DB: {e}")
        return

    # รายการคำค้นหาที่จะเทส (ลองเปลี่ยนได้ตามใจชอบ)
    test_queries = [
        "การตลาดออนไลน์",       # ไทยจ๋าๆ
        "Python Programming",   # อังกฤษจ๋าๆ
        "Data Analysis พื้นฐาน", # ไทยปนอังกฤษ
        "อยากเป็นผู้บริหาร",      # Soft Skill
    ]
    
    print("\n" + "="*60)
    print(f"🔍 DEBUGGING SEARCH SCORE (Model: {EMBEDDING_MODEL_NAME})")
    print("💡 Note: Score คือ Distance (ระยะห่าง). ยิ่งน้อย = ยิ่งเหมือน")
    print("="*60)
    
    for query in test_queries:
        print(f"\n❓ Query: '{query}'")
        print("-" * 60)
        
        try:
            # ใช้ similarity_search_with_score (คืนค่า Distance)
            results = db.similarity_search_with_score(query, k=5)
            
            if not results:
                print("   ❌ No results found.")
                continue

            min_score = 999
            max_score = -1

            for i, (doc, score) in enumerate(results, 1):
                title = doc.metadata.get('title', 'No Title')
                source = doc.metadata.get('source', 'Unknown')
                
                # เก็บสถิติ
                if score < min_score: min_score = score
                if score > max_score: max_score = score
                
                # จัดสี/สัญลักษณ์ให้น่าอ่าน
                prefix = "   "
                if source in ['FutureSkill', 'SkillLane']:
                    prefix = "TH"
                elif source == 'Coursera':
                    prefix = "EN"
                
                print(f"{prefix}{i}. [{score:.4f}] {title} ({source})")

            print("-" * 60)
            print(f"📊 Stats: Best Match = {min_score:.4f} | Worst Match = {max_score:.4f}")
            
            # คำแนะนำ Threshold
            suggested_threshold = max_score + 1.0
            print(f"💡 Suggested Threshold: < {suggested_threshold:.1f}")

        except Exception as e:
            print(f"❌ Error searching: {e}")

if __name__ == "__main__":
    debug_search()