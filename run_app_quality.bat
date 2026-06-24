@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Starting InknowVa - Quality Mode
echo ============================================

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

set DATA_PATH=data
set CHROMA_PATH=chroma_db
set CACHE_DIR=cache

set EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
set EMBEDDING_DEVICE=cpu
set EMBEDDING_NORMALIZE=1

set OLLAMA_MODEL=qwen2.5:7b
set OLLAMA_TEMPERATURE=0.1
set OLLAMA_NUM_CTX=4096
set OLLAMA_NUM_PREDICT=512

set SEMANTIC_K=9
set BM25_K=9
set HYBRID_FINAL_K=11
set RERANK_TOP_N=3
set MIN_QUALITY_SCORE=0.45
set MAX_CONTEXT_CHARS=6000

set FORCE_REINGEST=0
set FORCE_CACHE_REBUILD=0

if exist "app.py" (
    streamlit run app.py
) else if exist "main.py" (
    streamlit run main.py
) else (
    echo ERROR: app.py or main.py was not found in this folder.
    echo Put this .bat file in your project root folder.
    pause
)

endlocal
