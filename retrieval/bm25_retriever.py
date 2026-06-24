import re

from langchain_community.retrievers import BM25Retriever

from config.settings import BM25_K


def preprocess_text(text):
    # Gawing lowercase tokens para mas maayos ang keyword matching.
    if not text:
        return []

    return re.findall(r"\b[\w-]+\b", str(text).lower())


def create_bm25_retriever(chunks, k=BM25_K, use_preprocessing=True):
    # Gumawa ng BM25 index mula sa chunks.
    if not chunks:
        raise ValueError("No chunks received. Run loading, cleaning, and chunking first.")

    if use_preprocessing:
        retriever = BM25Retriever.from_documents(
            chunks,
            preprocess_func=preprocess_text,
        )
    else:
        retriever = BM25Retriever.from_documents(chunks)

    retriever.k = k
    return retriever


def bm25_search(bm25_retriever, query, k=None):
    # Keyword-based search.
    query = str(query or "").strip()
    if not query:
        return []

    if k is not None:
        bm25_retriever.k = k

    return bm25_retriever.invoke(query)
