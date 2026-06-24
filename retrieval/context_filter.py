import re

from config.settings import (
    MAX_CONTEXT_CHARS,
    MIN_CONTEXT_LENGTH,
    MIN_QUALITY_SCORE,
)


SAFE_PUNCTUATION = set(".,;:!?()[]{}'\"-/–—%#_+=<>@&*")


def is_readable_char(char):
    # Unicode-friendly para hindi ma-penalize ang Japanese text.
    return char.isalnum() or char.isspace() or char in SAFE_PUNCTUATION


def text_quality_score(text):
    # Basic readable score para ma-filter ang sirang OCR/noisy chunks.
    text = str(text or "")
    if not text.strip():
        return 0.0

    total_chars = max(len(text), 1)
    readable_chars = sum(1 for char in text if is_readable_char(char))
    readable_ratio = readable_chars / total_chars

    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    short_words = [word for word in words if len(word) <= 2]
    short_word_ratio = len(short_words) / max(len(words), 1)

    weird_chars = sum(1 for char in text if not is_readable_char(char))
    weird_ratio = weird_chars / total_chars

    return readable_ratio - (short_word_ratio * 0.25) - weird_ratio


def filter_low_quality_docs(docs, min_score=MIN_QUALITY_SCORE, min_length=MIN_CONTEXT_LENGTH):
    # Tanggalin ang sobrang ikli o maingay na chunks.
    clean_docs = []

    for doc in docs or []:
        text = (doc.page_content or "").strip()

        if len(text) < min_length:
            continue

        score = text_quality_score(text)

        if score >= min_score:
            doc.metadata = dict(doc.metadata or {})
            doc.metadata["quality_score"] = float(score)
            clean_docs.append(doc)

    return clean_docs


def limit_context_docs(docs, max_chars=MAX_CONTEXT_CHARS):
    # Limitahan ang final context size habang pinapanatili ang ranking order.
    selected_docs = []
    total_chars = 0

    for doc in docs or []:
        text_length = len(doc.page_content or "")

        if total_chars + text_length > max_chars:
            if not selected_docs:
                selected_docs.append(doc)
            break

        selected_docs.append(doc)
        total_chars += text_length

    return selected_docs


def count_keyword_matches(docs, keywords):
    # Bilangin kung ilang keywords ang nasa final context.
    if not docs or not keywords:
        return 0

    context_text = " ".join(doc.page_content or "" for doc in docs).lower()
    return sum(1 for keyword in keywords if str(keyword).lower() in context_text)


def has_min_keyword_matches(docs, keywords, min_matches=1):
    # Check kung sapat ang keyword hits.
    return count_keyword_matches(docs, keywords) >= min_matches


def get_document_key(doc):
    # Stable key para sa duplicate removal.
    metadata = doc.metadata or {}
    source = metadata.get("source", "")
    page = metadata.get("page", "")
    chunk_id = metadata.get("chunk_id") or metadata.get("chunk_index", "")

    if chunk_id != "":
        return (source, page, chunk_id)

    preview = (doc.page_content or "")[:250]
    return (source, page, preview)


def remove_duplicate_docs(docs):
    # Tanggalin duplicate chunks pero i-keep ang unang lumabas.
    unique_docs = []
    seen = set()

    for doc in docs or []:
        key = get_document_key(doc)

        if key in seen:
            continue

        seen.add(key)
        unique_docs.append(doc)

    return unique_docs


def get_chunk_index(doc):
    # Kunin ang chunk index mula metadata.
    chunk_index = (doc.metadata or {}).get("chunk_index")

    if chunk_index is None:
        return None

    try:
        return int(chunk_index)
    except (TypeError, ValueError):
        return None


def expand_neighbor_chunks(selected_docs, all_chunks, window=1):
    # Optional: isama ang katabing chunks para hindi bitin ang context.
    if not selected_docs or not all_chunks:
        return selected_docs

    chunks_by_source = {}

    for chunk in all_chunks:
        metadata = chunk.metadata or {}
        source = metadata.get("source", "")
        chunk_index = get_chunk_index(chunk)

        if chunk_index is None:
            continue

        chunks_by_source.setdefault(source, {})[chunk_index] = chunk

    expanded_docs = []

    for doc in selected_docs:
        metadata = doc.metadata or {}
        source = metadata.get("source", "")
        chunk_index = get_chunk_index(doc)

        if chunk_index is None:
            expanded_docs.append(doc)
            continue

        source_chunks = chunks_by_source.get(source, {})

        for index in range(chunk_index - window, chunk_index + window + 1):
            neighbor_doc = source_chunks.get(index)
            if neighbor_doc:
                expanded_docs.append(neighbor_doc)

    return remove_duplicate_docs(expanded_docs)
