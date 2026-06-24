from config.settings import (
    BM25_K,
    DATA_PATH,
    ENABLE_FALSE_PREMISE_RETRY,
    ENABLE_NEIGHBOR_EXPANSION,
    ENABLE_QUESTION_REWRITE,
    HYBRID_FINAL_K,
    MAX_CONTEXT_CHARS,
    MIN_QUALITY_SCORE,
    NEIGHBOR_WINDOW,
    NO_ANSWER_TEXT,
    RERANK_TOP_N,
    SEMANTIC_K,
    SOURCE_TOP_N,
)
from embeddings.embedding_model import get_embedding_model
from vectorstore.chroma_store import load_chroma_vectorstore

from utils.bm25_cache import load_or_create_bm25
from utils.chunk_cache import load_or_create_chunks

from retrieval.context_filter import (
    expand_neighbor_chunks,
    filter_low_quality_docs,
    limit_context_docs,
)
from retrieval.hybrid_retriever import hybrid_search
from retrieval.reranker import load_reranker, rerank_documents

from llm.ollama_llm import load_llm
from chains.rag_chain import (
    clean_generated_answer,
    generate_answer,
    get_sources,
    stream_answer,
)

from memory.question_rewriter import rewrite_question
from suggestions.suggestion_generator import generate_suggestions


ASSUMPTION_CHECK_STARTERS = (
    "why ",
    "how ",
    "why did ",
    "how did ",
    "why was ",
    "why is ",
    "bakit ",
    "paano ",
)


def build_response(answer, sources=None, documents=None, suggestions=None):
    # Standard response format para sa UI.
    return {
        "answer": answer,
        "sources": sources or [],
        "documents": documents or [],
        "suggestions": suggestions or [],
    }


def is_no_answer(answer):
    # Check kung fallback/no-answer ang sagot.
    if not answer:
        return False

    return NO_ANSWER_TEXT.lower() in str(answer).lower()


def needs_strict_assumption_check(question):
    # Mas strict sa why/how/bakit/paano dahil madalas may hidden false premise.
    normalized = " ".join(str(question or "").lower().split())
    return any(normalized.startswith(starter) for starter in ASSUMPTION_CHECK_STARTERS)


def safe_generate_suggestions(question, answer, llm):
    # Gumawa ng suggestions pero huwag sirain main flow kapag may error.
    try:
        return generate_suggestions(
            question=question,
            answer=answer,
            llm=llm,
        )
    except Exception:
        return []


def safe_rewrite_question(question, chat_history, llm):
    # Rewrite follow-up question kapag may chat history.
    if not ENABLE_QUESTION_REWRITE or not chat_history:
        return question

    try:
        rewritten_question = rewrite_question(
            question=question,
            chat_history=chat_history,
            llm=llm,
        )

        if rewritten_question and rewritten_question.strip():
            return rewritten_question.strip()

    except Exception:
        pass

    return question


def load_chatbot_components():
    # Load lahat ng reusable components ng chatbot.
    embedding_model = get_embedding_model()

    vectorstore = load_chroma_vectorstore(
        embedding_model=embedding_model,
    )

    chunks = load_or_create_chunks(DATA_PATH)

    bm25_retriever = load_or_create_bm25(
        chunks=chunks,
        k=BM25_K,
    )

    return {
        "vectorstore": vectorstore,
        "bm25_retriever": bm25_retriever,
        "reranker": load_reranker(),
        "llm": load_llm(),
        "chunks": chunks,
    }


def retrieve_documents(
    retrieval_query,
    vectorstore,
    bm25_retriever,
    reranker,
    all_chunks=None,
    debug=False,
):
    # Hybrid retrieval -> rerank -> filter -> optional expand -> limit context.
    hybrid_docs = hybrid_search(
        query=retrieval_query,
        vectorstore=vectorstore,
        bm25_retriever=bm25_retriever,
        semantic_k=SEMANTIC_K,
        bm25_k=BM25_K,
        final_k=HYBRID_FINAL_K,
        use_rrf=True,
    )

    if debug:
        print(f"Hybrid candidates: {len(hybrid_docs)}")

    reranked_docs = rerank_documents(
        query=retrieval_query,
        documents=hybrid_docs,
        reranker=reranker,
        top_n=RERANK_TOP_N,
        show_scores=debug,
    )

    clean_docs = filter_low_quality_docs(
        reranked_docs,
        min_score=MIN_QUALITY_SCORE,
    )

    if debug:
        print(f"Clean reranked docs: {len(clean_docs)}")

    if ENABLE_NEIGHBOR_EXPANSION and all_chunks:
        clean_docs = expand_neighbor_chunks(
            selected_docs=clean_docs,
            all_chunks=all_chunks,
            window=NEIGHBOR_WINDOW,
        )

    return limit_context_docs(
        clean_docs,
        max_chars=MAX_CONTEXT_CHARS,
    )


def maybe_retry_false_premise(question, answer, final_docs, llm, chat_history="", debug=False):
    # Second chance kapag why/how question pero nag-fallback kahit may docs.
    if not ENABLE_FALSE_PREMISE_RETRY:
        return answer

    if not final_docs or not is_no_answer(answer):
        return answer

    if not needs_strict_assumption_check(question):
        return answer

    retry_answer = generate_answer(
        question=question,
        docs=final_docs,
        llm=llm,
        chat_history=chat_history,
        debug=debug,
        strict_assumption_check=True,
        correction_retry=True,
    )

    if retry_answer and not is_no_answer(retry_answer):
        return retry_answer

    return answer


def ask_rag(
    question,
    vectorstore,
    bm25_retriever,
    reranker,
    llm,
    chat_history="",
    debug=False,
    all_chunks=None,
):
    # Non-streaming RAG answer.
    question = str(question or "").strip()

    if not question:
        return build_response(answer="No question entered.")

    retrieval_query = safe_rewrite_question(
        question=question,
        chat_history=chat_history,
        llm=llm,
    )

    final_docs = retrieve_documents(
        retrieval_query=retrieval_query,
        vectorstore=vectorstore,
        bm25_retriever=bm25_retriever,
        reranker=reranker,
        all_chunks=all_chunks,
        debug=debug,
    )

    if not final_docs:
        return build_response(answer=NO_ANSWER_TEXT)

    strict_check = needs_strict_assumption_check(question)

    answer = generate_answer(
        question=question,
        docs=final_docs,
        llm=llm,
        chat_history=chat_history,
        debug=debug,
        strict_assumption_check=strict_check,
    )

    answer = maybe_retry_false_premise(
        question=question,
        answer=answer,
        final_docs=final_docs,
        llm=llm,
        chat_history=chat_history,
        debug=debug,
    )

    sources = get_sources(final_docs[:SOURCE_TOP_N])

    if is_no_answer(answer):
        sources = []

    suggestions = safe_generate_suggestions(
        question=question,
        answer=answer,
        llm=llm,
    )

    return build_response(
        answer=answer,
        sources=sources,
        documents=final_docs,
        suggestions=suggestions,
    )


def ask_rag_stream(
    question,
    vectorstore,
    bm25_retriever,
    reranker,
    llm,
    chat_history="",
    debug=False,
    all_chunks=None,
):
    # Streaming RAG answer.
    question = str(question or "").strip()

    if not question:
        yield {"type": "done", **build_response(answer="No question entered.")}
        return

    retrieval_query = safe_rewrite_question(
        question=question,
        chat_history=chat_history,
        llm=llm,
    )

    final_docs = retrieve_documents(
        retrieval_query=retrieval_query,
        vectorstore=vectorstore,
        bm25_retriever=bm25_retriever,
        reranker=reranker,
        all_chunks=all_chunks,
        debug=debug,
    )

    if not final_docs:
        yield {"type": "done", **build_response(answer=NO_ANSWER_TEXT)}
        return

    strict_check = needs_strict_assumption_check(question)
    full_answer = ""

    for chunk in stream_answer(
        question=question,
        docs=final_docs,
        llm=llm,
        chat_history=chat_history,
        debug=debug,
        strict_assumption_check=strict_check,
    ):
        full_answer += chunk
        yield {"type": "chunk", "content": chunk}

    final_answer = clean_generated_answer(
        answer=full_answer,
        question=question,
    )

    sources = get_sources(final_docs[:SOURCE_TOP_N])

    if is_no_answer(final_answer):
        sources = []

    suggestions = safe_generate_suggestions(
        question=question,
        answer=final_answer,
        llm=llm,
    )

    yield {
        "type": "done",
        **build_response(
            answer=final_answer,
            sources=sources,
            documents=final_docs,
            suggestions=suggestions,
        ),
    }
