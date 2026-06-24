@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Running InknowVa Ingestion
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

set FORCE_REINGEST=0
set FORCE_CACHE_REBUILD=0

python ingest.py

echo.
pause
endlocal
