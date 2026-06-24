InknowVa BAT files

Put these .bat files in your project root folder.

Recommended use:
1. run_app.bat
   - Normal app start.
   - Uses qwen2.5:3b, e5-small, balanced retrieval.

2. run_app_quality.bat
   - Higher quality app start.
   - Uses qwen2.5:7b and higher retrieval K values.
   - Slower on CPU.

3. run_ingest.bat
   - Normal ingestion.
   - Uses cache/vector metadata when available.

4. run_reingest_force.bat
   - Force rebuild chunks, BM25, and Chroma vectors.
   - Use after changing data files, embedding model, chunker, or cleaner.

5. clean_vectors_and_cache.bat
   - Deletes chroma_db and cache.
   - Use this when you get embedding dimension mismatch.
   - After this, run run_reingest_force.bat.

6. run_tests.bat
   - Runs document loader, retrieval, and RAG tests if available.

7. run_retrieval_test.bat
   - Runs retrieval test only.

8. run_rag_test.bat
   - Runs RAG test only.

Important:
- Do not change EMBEDDING_MODEL_NAME without rebuilding chroma_db.
- If you switch e5-base <-> e5-small, run clean_vectors_and_cache.bat then run_reingest_force.bat.
- Make sure Ollama is installed and the selected model is pulled.
