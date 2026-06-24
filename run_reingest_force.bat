@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Force Rebuild InknowVa Vectors and Cache
echo ============================================
echo This will rebuild chunks, BM25 cache, and Chroma vectors.
echo Use this after changing data files, cleaning/chunking, or embedding model.
echo.
pause

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

set DATA_PATH=data
set CHROMA_PATH=chroma_db
set CACHE_DIR=cache

set EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
set EMBEDDING_DEVICE=cpu
set EMBEDDING_NORMALIZE=1

set FORCE_REINGEST=1
set FORCE_CACHE_REBUILD=1

python ingest.py

echo.
pause
endlocal
