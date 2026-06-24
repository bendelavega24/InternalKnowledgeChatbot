@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Clean ChromaDB and Cache
echo ============================================
echo This will delete:
echo - chroma_db
echo - cache
echo.
echo Use this when you changed embedding model and got dimension mismatch.
echo Example error: expecting embedding dimension 768, got 384.
echo.
pause

if exist "chroma_db" (
    rmdir /s /q "chroma_db"
    echo Deleted chroma_db
) else (
    echo chroma_db not found
)

if exist "cache" (
    rmdir /s /q "cache"
    echo Deleted cache
) else (
    echo cache not found
)

echo.
echo Done. Run run_reingest_force.bat next.
pause
endlocal
