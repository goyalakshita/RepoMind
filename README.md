# RepoMind – AI-Powered Code Repository Assistant

RepoMind is an AI-powered repository assistant that helps developers understand unfamiliar codebases through natural-language questions. It uses Retrieval-Augmented Generation (RAG) to retrieve relevant code snippets and generate context-aware explanations with source references.

## Features

- **Multiple Repository Inputs:** Load repositories through GitHub URLs, ZIP files, or local folders.
- **Code Parsing:** Extract Python functions, classes, and methods using Abstract Syntax Trees (AST).
- **Semantic Search:** Find relevant code based on the meaning of a question rather than exact keyword matching.
- **RAG-Based Question Answering:** Retrieve relevant code and use an LLM to generate grounded explanations.
- **Vector Storage:** Store and search code embeddings using ChromaDB.
- **Source References:** Display relevant file paths and code locations.
- **Multiple LLM Providers:** Gemini as the primary provider and Groq as a fallback.
- **Repository History:** Maintain repository metadata and persistent chat history.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| Code Parsing | Python AST |
| Embedding Model | Sentence Transformers – all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Primary LLM | Gemini – gemini-3.5-flash-lite |
| Fallback LLM | Groq – openai/gpt-oss-120b |
| Repository Management | GitPython |
| Testing | Pytest |

## System Architecture

1. **Repository Input:** The user provides a GitHub URL, ZIP file, or local repository.
2. **File Discovery:** Supported source files are identified and loaded.
3. **Code Parsing:** Python files are structurally parsed to extract meaningful code components.
4. **Chunking and Embeddings:** Code is divided into smaller units and converted into numerical embeddings.
5. **Vector Storage:** Embeddings, code snippets, and metadata are stored in ChromaDB.
6. **Semantic Retrieval:** The user's question is converted into an embedding to retrieve relevant code.
7. **Answer Generation:** Retrieved context is passed to the LLM to generate an explanation with source references.

## Project Structure

```text
RepoMind/
├── agents/
├── core/
│   ├── code_parser.py
│   ├── embeddings.py
│   ├── llm_handler.py
│   ├── rag_pipeline.py
│   ├── repository_history.py
│   ├── repository_loader.py
│   ├── retriever.py
│   └── vector_store.py
├── data/
├── tests/
├── utils/
├── app.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/goyalakshita/RepoMind.git
cd RepoMind
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create a `.env` file in the project root and configure your Gemini and Groq API keys using the environment variable names expected by `core/llm_handler.py`.

Never upload your actual API keys to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## Testing

Run the test suite using:

```bash
python -m pytest tests -v
```

## Limitations

- Structural AST-based parsing is currently implemented for Python.
- Other supported file types can be loaded as text, but do not yet have equivalent language-specific structural parsing.
- The application currently runs locally and requires API credentials for LLM-based responses.

## Future Scope

- Multi-language structural parsing using Tree-sitter.
- Improved retrieval and ranking techniques.
- Agent-based workflows for automated code analysis and documentation.
- Incremental repository indexing.
- Cloud deployment and wider accessibility.

## Author

**Akshita Goyal**

B.Tech – Computer Science and Engineering (Data Science)

GitHub: [goyalakshita](https://github.com/goyalakshita)

---

*RepoMind – Making unfamiliar codebases easier to understand.*
