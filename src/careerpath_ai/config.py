import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
# src/careerpath_ai/config.py -> src/careerpath_ai -> src -> project_root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
# VECTOR_STORE_DIR is managed by ChromaDB, but good to know location

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
URL_COURSERA_API = os.getenv("URL_COURSERA_API")

# Model Config
MODEL_NAME = "gemini-2.5-flash"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

if not GOOGLE_API_KEY:
    # We might not want to raise immediately on import in case we are just running utilities,
    # but for the main app it is critical.
    pass 
