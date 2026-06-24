@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Running InknowVa Tests
echo ============================================

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

set DATA_PATH=data
set CHROMA_PATH=chroma_db
set CACHE_DIR=cache
set EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
set OLLAMA_MODEL=qwen2.5:3b

if exist "tests\test_document_loader.py" (
    python tests\test_document_loader.py
) else if exist "For Testing Purposes\test_document_loader.py" (
    python "For Testing Purposes\test_document_loader.py"
)

echo.
if exist "tests\test_retrieval.py" (
    python tests\test_retrieval.py
) else if exist "For Testing Purposes\test_retrieval.py" (
    python "For Testing Purposes\test_retrieval.py"
)

echo.
if exist "tests\test_rag.py" (
    python tests\test_rag.py
) else if exist "For Testing Purposes\test_rag.py" (
    python "For Testing Purposes\test_rag.py"
)

echo.
pause
endlocal
