import shutil
from pathlib import Path

from langchain_chroma import Chroma

from config.settings import CHROMA_COLLECTION_NAME, CHROMA_PATH


def has_chroma_files(persist_directory=CHROMA_PATH):
    # Check kung may existing ChromaDB folder na may laman.
    path = Path(persist_directory)
    return path.exists() and path.is_dir() and any(path.iterdir())


def validate_chunks(chunks):
    # Stop kapag walang chunks na ise-save.
    if not chunks:
        raise ValueError("No chunks received. Check loading, cleaning, or chunking.")


def validate_chroma_folder(persist_directory):
    # Check kung valid ang existing ChromaDB folder.
    path = Path(persist_directory)

    if not path.exists():
        raise FileNotFoundError(f"ChromaDB folder not found: {persist_directory}")

    if not path.is_dir():
        raise NotADirectoryError(f"ChromaDB path is not a folder: {persist_directory}")

    if not any(path.iterdir()):
        raise FileNotFoundError(f"ChromaDB folder is empty: {persist_directory}")


def reset_chroma_folder(persist_directory=CHROMA_PATH):
    # Burahin ang old vector DB bago full re-ingest para iwas duplicate vectors.
    path = Path(persist_directory)

    if path.exists():
        shutil.rmtree(path)


def create_chroma_vectorstore(
    chunks,
    embedding_model,
    persist_directory=CHROMA_PATH,
    collection_name=CHROMA_COLLECTION_NAME,
):
    # Gumawa ng bagong ChromaDB mula sa chunks.
    validate_chunks(chunks)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_name=collection_name,
    )


def load_chroma_vectorstore(
    embedding_model,
    persist_directory=CHROMA_PATH,
    collection_name=CHROMA_COLLECTION_NAME,
):
    # Mag-load ng existing ChromaDB.
    validate_chroma_folder(persist_directory)

    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model,
        collection_name=collection_name,
    )


def get_chroma_document_count(vectorstore):
    # Kunin kung ilang vectors/documents ang nasa collection.
    return vectorstore._collection.count()
