from collections import defaultdict

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import CHUNK_OVERLAP, CHUNK_SIZE, MIN_DOCUMENT_LENGTH


DEFAULT_SEPARATORS = [
    "\n# ",
    "\n## ",
    "\n### ",
    "\n\n",
    "\n",
    ". ",
    "。",
    "、",
    " ",
    "",
]


def validate_chunk_settings(chunk_size, chunk_overlap):
    # I-check kung valid ang chunk settings.
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must not be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


def get_valid_documents(docs, min_length=MIN_DOCUMENT_LENGTH):
    # Tanggalin ang empty o sobrang ikling documents bago i-chunk.
    valid_docs = []

    for doc in docs or []:
        text = str(getattr(doc, "page_content", "") or "").strip()
        if len(text) >= min_length:
            valid_docs.append(doc)

    return valid_docs


def get_source_key(chunk):
    # Source key para per-file ang chunk numbering.
    metadata = chunk.metadata or {}
    return metadata.get("source") or metadata.get("file_name") or "unknown"


def add_chunk_metadata(chunks, chunk_size, chunk_overlap):
    # Lagyan ng chunk metadata para madali sa retrieval/source/debug.
    source_counts = defaultdict(int)

    for global_index, chunk in enumerate(chunks):
        metadata = dict(chunk.metadata or {})
        source_key = get_source_key(chunk)
        source_index = source_counts[source_key]
        source_counts[source_key] += 1

        metadata["chunk_index"] = source_index
        metadata["global_chunk_index"] = global_index
        metadata["chunk_id"] = f"{source_key}::chunk_{source_index}"
        metadata["chunk_size"] = chunk_size
        metadata["chunk_overlap"] = chunk_overlap
        chunk.metadata = metadata

    return chunks


def chunk_documents(docs, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    # Main function para hatiin ang cleaned documents into chunks.
    validate_chunk_settings(chunk_size, chunk_overlap)
    valid_docs = get_valid_documents(docs)

    if not valid_docs:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=DEFAULT_SEPARATORS,
    )

    chunks = splitter.split_documents(valid_docs)
    return add_chunk_metadata(chunks, chunk_size, chunk_overlap)
