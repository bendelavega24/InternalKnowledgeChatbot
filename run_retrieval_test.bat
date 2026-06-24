@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Running Retrieval Test
echo ============================================

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

set DATA_PATH=data
set CHROMA_PATH=chroma_db
set CACHE_DIR=cache
set EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small

if exist "tests\test_retrieval.py" (
    python tests\test_retrieval.py
) else if exist "For Testing Purposes\test_retrieval.py" (
    python "For Testing Purposes\test_retrieval.py"
) else (
    echo ERROR: test_retrieval.py not found.
    pause
)

endlocal
