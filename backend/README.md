# Antigravity Backend (FastAPI)

The core intelligence engine.

## 🛠️ Tech Stack
*   **Python 3.12**
*   **FastAPI**: High-performance Async Web Framework.
*   **Sentence-Transformers**: Local embeddings (`all-MiniLM-L6-v2`).
*   **PyTorch (MPS)**: Hardware acceleration on Mac Silicon.
*   **Rank_BM25**: Keyword search algorithms.
*   **Pydantic**: Data validation.

## 🏃‍♂️ Running Locally

1.  **Environment**:
    ```bash
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Start Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## 🧪 Testing

Run production-grade checks:

```bash
# Run all agent logic tests
pytest tests/test_refactored_agents.py
```

## 📂 Key Directories
*   `app/agents/`: Individual agent logic definitions.
*   `app/services/`: Shared utilities (EmbeddingService, DocumentParser).
*   `data/`: Persistent storage (gitignored). Embeddings live here.
