from config.settings import MMR_FETCH_K, MMR_LAMBDA, SEMANTIC_K, USE_E5_PREFIX


def format_semantic_query(query, use_e5_prefix=USE_E5_PREFIX):
    # Optional E5 format: query: <question>.
    query = str(query or "").strip()
    if not query:
        return ""

    if use_e5_prefix and not query.lower().startswith("query:"):
        return f"query: {query}"

    return query


def get_semantic_retriever(vectorstore, k=SEMANTIC_K, search_type="similarity", score_threshold=None):
    # Gumawa ng LangChain retriever wrapper.
    search_kwargs = {"k": k}

    if score_threshold is not None:
        search_kwargs["score_threshold"] = score_threshold

    return vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )


def semantic_search(vectorstore, query, k=SEMANTIC_K, use_e5_prefix=USE_E5_PREFIX):
    # Vector similarity search.
    formatted_query = format_semantic_query(query, use_e5_prefix=use_e5_prefix)
    if not formatted_query:
        return []

    return vectorstore.similarity_search(formatted_query, k=k)


def semantic_search_with_scores(vectorstore, query, k=SEMANTIC_K, use_e5_prefix=USE_E5_PREFIX):
    # Vector search with score metadata.
    formatted_query = format_semantic_query(query, use_e5_prefix=use_e5_prefix)
    if not formatted_query:
        return []

    results = vectorstore.similarity_search_with_score(formatted_query, k=k)
    docs = []

    for doc, score in results:
        doc.metadata = dict(doc.metadata or {})
        doc.metadata["semantic_score"] = float(score)
        docs.append(doc)

    return docs


def mmr_search(
    vectorstore,
    query,
    k=SEMANTIC_K,
    fetch_k=MMR_FETCH_K,
    lambda_mult=MMR_LAMBDA,
    use_e5_prefix=USE_E5_PREFIX,
):
    # MMR search para bawas duplicate/near-duplicate results.
    formatted_query = format_semantic_query(query, use_e5_prefix=use_e5_prefix)
    if not formatted_query:
        return []

    return vectorstore.max_marginal_relevance_search(
        formatted_query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
    )
