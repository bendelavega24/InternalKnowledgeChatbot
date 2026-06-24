from config.settings import (
    BM25_K,
    BM25_WEIGHT,
    HYBRID_FINAL_K,
    RRF_K,
    SEMANTIC_K,
    SEMANTIC_WEIGHT,
    USE_E5_PREFIX,
)
from retrieval.semantic_retriever import semantic_search


def get_document_key(doc):
    # Stable key para matanggal ang duplicate chunks.
    metadata = doc.metadata or {}
    source = metadata.get("source", "")
    page = metadata.get("page", "")
    chunk_id = metadata.get("chunk_id") or metadata.get("chunk_index", "")

    if chunk_id != "":
        return (source, page, chunk_id)

    preview = (doc.page_content or "")[:250]
    return (source, page, preview)


def remove_duplicates(docs):
    # I-keep ang unang version ng bawat unique chunk.
    unique_docs = []
    seen = set()

    for doc in docs:
        key = get_document_key(doc)
        if key in seen:
            continue

        seen.add(key)
        unique_docs.append(doc)

    return unique_docs


def reciprocal_rank_fusion(ranked_lists, weights=None, rrf_k=RRF_K, final_k=HYBRID_FINAL_K):
    # Pagsamahin ang semantic at BM25 ranking gamit ang RRF.
    if not ranked_lists:
        return []

    if weights is None:
        weights = [1.0] * len(ranked_lists)

    scores = {}
    docs_by_key = {}

    for list_index, docs in enumerate(ranked_lists):
        weight = weights[list_index] if list_index < len(weights) else 1.0

        for rank, doc in enumerate(docs or [], start=1):
            key = get_document_key(doc)

            if key not in docs_by_key:
                docs_by_key[key] = doc

            scores[key] = scores.get(key, 0.0) + weight / (rrf_k + rank)

            doc.metadata = dict(doc.metadata or {})
            doc.metadata[f"retrieval_rank_{list_index}"] = rank

    ranked_keys = sorted(scores, key=scores.get, reverse=True)
    fused_docs = []

    for key in ranked_keys[:final_k]:
        doc = docs_by_key[key]
        doc.metadata = dict(doc.metadata or {})
        doc.metadata["hybrid_score"] = float(scores[key])
        fused_docs.append(doc)

    return fused_docs


def hybrid_search(
    query,
    vectorstore,
    bm25_retriever,
    semantic_k=SEMANTIC_K,
    bm25_k=BM25_K,
    final_k=HYBRID_FINAL_K,
    use_rrf=True,
    use_e5_prefix=USE_E5_PREFIX,
    semantic_weight=SEMANTIC_WEIGHT,
    bm25_weight=BM25_WEIGHT,
):
    # Semantic + BM25 retrieval.
    query = str(query or "").strip()
    if not query:
        return []

    semantic_docs = semantic_search(
        vectorstore=vectorstore,
        query=query,
        k=semantic_k,
        use_e5_prefix=use_e5_prefix,
    )

    bm25_retriever.k = bm25_k
    bm25_docs = bm25_retriever.invoke(query)

    if use_rrf:
        return reciprocal_rank_fusion(
            ranked_lists=[semantic_docs, bm25_docs],
            weights=[semantic_weight, bm25_weight],
            final_k=final_k,
        )

    return remove_duplicates(semantic_docs + bm25_docs)[:final_k]
