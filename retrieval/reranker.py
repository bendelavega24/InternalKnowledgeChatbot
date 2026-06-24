from FlagEmbedding import FlagReranker

from config.settings import (
    RERANK_BATCH_SIZE,
    RERANK_MAX_CHARS,
    RERANK_MAX_LENGTH,
    RERANK_TOP_N,
    RERANK_USE_FP16,
    RERANKER_MODEL_NAME,
)


def load_reranker(model_name=RERANKER_MODEL_NAME, use_fp16=RERANK_USE_FP16):
    # I-load ang reranker model.
    return FlagReranker(model_name, use_fp16=use_fp16)


def normalize_scores(scores):
    # Gawing plain Python list ang scores.
    if isinstance(scores, (int, float)):
        return [float(scores)]

    if hasattr(scores, "tolist"):
        return scores.tolist()

    return list(scores)


def trim_document_text(text, max_chars=RERANK_MAX_CHARS):
    # Putulin ang text para bumilis ang reranking.
    clean_text = " ".join(str(text or "").split())

    if len(clean_text) <= max_chars:
        return clean_text

    return clean_text[:max_chars].rstrip()


def compute_rerank_scores(
    reranker,
    pairs,
    batch_size=RERANK_BATCH_SIZE,
    max_length=RERANK_MAX_LENGTH,
):
    # Compatible sa iba-ibang FlagEmbedding versions.
    try:
        return reranker.compute_score(
            pairs,
            batch_size=batch_size,
            max_length=max_length,
        )
    except TypeError:
        pass

    try:
        return reranker.compute_score(pairs, batch_size=batch_size)
    except TypeError:
        pass

    return reranker.compute_score(pairs)


def rerank_documents(
    query,
    documents,
    reranker,
    top_n=RERANK_TOP_N,
    min_score=None,
    show_scores=False,
    return_scores=False,
    max_chars=RERANK_MAX_CHARS,
    batch_size=RERANK_BATCH_SIZE,
    max_length=RERANK_MAX_LENGTH,
):
    # I-rerank ang candidate docs at kunin ang top_n.
    if not documents:
        return []

    query = str(query or "").strip()
    pairs = [
        [query, trim_document_text(doc.page_content, max_chars=max_chars)]
        for doc in documents
    ]

    scores = compute_rerank_scores(
        reranker=reranker,
        pairs=pairs,
        batch_size=batch_size,
        max_length=max_length,
    )
    scores = normalize_scores(scores)

    ranked_docs = sorted(
        zip(documents, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    results = []

    for rank, (doc, score) in enumerate(ranked_docs, start=1):
        if min_score is not None and score < min_score:
            continue

        doc.metadata = dict(doc.metadata or {})
        doc.metadata["rerank_score"] = float(score)
        doc.metadata["rerank_rank"] = rank

        if show_scores:
            source = doc.metadata.get("source", "Unknown source")
            page = doc.metadata.get("page", "N/A")
            print(f"Rerank rank {rank} | score={score:.4f} | source={source} | page={page}")

        results.append((doc, score))

        if len(results) >= top_n:
            break

    if return_scores:
        return results

    return [doc for doc, _ in results]
