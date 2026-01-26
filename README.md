# CareerPath AI (CPAI)

CareerPath AI is an intelligent career advisory engine designed to analyze user career goals, identify skill gaps, and recommend personalized learning paths. By leveraging Large Language Models (LLMs) and Vector Search, the system provides context-aware guidance and curates relevant courses from major educational platforms.

## System Architecture & Technical Stack

### 1. Data Ingestion (ETL Pipeline)

The system employs a robust ETL (Extract, Transform, Load) pipeline to aggregate course data from multiple sources.

- **Extraction**: Automated scrapers and API connectors collect metadata (titles, descriptions, syllabi) from platforms such as Coursera, Udemy, and localized providers.
- **Transformation**: Data cleaning and normalization processes standardize course formats, filter low-quality entries, and detect language (TH/EN).
- **Loading**: Processed data is embedded and stored in a vector database for efficient semantic retrieval.

### 2. Core AI Engine (RAG - Retrieval Augmented Generation)

The heart of the application is the `SkillEngine`, which utilizes a RAG architecture:

- **Intent Analysis**: Google Gemini 2.5 Flash analyzes user input to extract current roles, target career paths, and specific constraints (e.g., preference for free courses).
- **Semantic Search**: `sentence-transformers` generate high-dimensional embeddings for both user queries and course catalog data.
- **Vector Retrieval**: ChromaDB performs similarity searches to find courses that mathematically match the identified skill gaps.
- **Contextual Recommendation**: The LLM synthesizes the retrieved course data with the user's career context to generate a coherent, step-by-step learning roadmap.

### 3. Memory & Context Management

- **Short-term Memory**: Implements LangChain's `RunnableWithMessageHistory` to maintain conversational context within a session. This allows the system to handle follow-up questions and refine recommendations based on previous interactions.

## Installation & Setup

### Prerequisites

- Python 3.12+
- UV Package Manager (recommended) or Pip

### Configuration

1. Clone the repository.
2. Create a `.env` file in the root directory.
3. Add your Google API Key:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

### Dependency Installation

```bash
uv sync
```

## Usage

### 1. Data Pipeline Execution

Before running the main application, ensure the vector database is populated:

```bash
uv run src/engine/vector_manager.py
```

This command triggers the incremental update process, processing CSV datasets and updating the ChromaDB vector store.

### 2. Running the Advisor CLI

Start the interactive command-line interface:

```bash
uv run main.py
```

## Project Structure

```
careerpath_ai/
├── data/                   # Raw CSV datasets
├── src/
│   ├── engine/
│   │   ├── skill_engine.py    # Core logic (LLM + RAG)
│   │   └── vector_manager.py  # Vector DB management & ETL
│   ├── model/              # Data models and schemas
│   ├── utils/              # Helper functions (Logging, etc.)
│   └── config.py           # Configuration management
├── vector_store/           # Persisted ChromaDB data
├── main.py                 # CLI Entry point
└── pyproject.toml          # Dependency definitions
```

## License

MIT License
