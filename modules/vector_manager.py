import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import shutil 

def build_database(csv_path="./data/coursera_dataset.csv", db_path="./vector_store"):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    # ลบ DB เก่าทิ้งก่อนสร้างใหม่ เพื่อป้องกันข้อมูลซ้ำ
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        print(f"Deleted old database at {db_path}")

    df = pd.read_csv(csv_path)
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    documents = []
    print(f"Processing {len(df)} courses...")

    for _, row in df.iterrows():
        content = f"""
        Title: {row['title']}
        Category: {row['category']}
        Level: {row['level']}
        Description: {row['description']}
        """
        
        metadata = {
            "id": str(row['id']),
            "title": row['title'],
            "url": row['url'],
            "duration": str(row['duration']),
            "certificate": str(row['certificate_type']),
            "level": str(row['level'])
        }

        doc = Document(page_content=content.strip(), metadata=metadata)
        documents.append(doc)

    print("Creating Vector Database...")
    
    Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=db_path
    )
    
    print(f"Database saved to {db_path}")

def test_search(query, db_path="./vector_store"):
    print(f"\nTesting Search: '{query}'")
    
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory=db_path, embedding_function=embedding_model)
    
    results = db.similarity_search(query, k=3)
    
    for i, doc in enumerate(results):
        print(f"{i+1}. {doc.metadata['title']} ({doc.metadata['level']})")
        print(f"   Link: {doc.metadata['url']}")
        print("-" * 20)

if __name__ == "__main__":
    build_database()
    test_search("I want to learn about Python for Backend")