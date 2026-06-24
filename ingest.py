import json
import shutil
import time
from contextlib import contextmanager
from pathlib import Path

from config.settings import (
    CHROMA_PATH,
    DATA_PATH,
    FORCE_REINGEST,
    INGEST_RESULT_FILE,
    LOAD_RECURSIVE,
)
from embeddings.embedding_model import get_embedding_model
from loaders.document_loader import load_documents, validate_data_path
from preprocessing.chunker import chunk_documents
from preprocessing.cleaner import clean_documents
from utils.chunk_cache import get_file_signature, save_chunks_cache
from vectorstore.chroma_store import (
    create_chroma_vectorstore,
    get_chroma_document_count,
    has_chroma_files,
    reset_chroma_folder,
)


INGEST_META_FILE = Path(CHROMA_PATH) / "ingest_meta.json"


def format_seconds(seconds):
    # Gawing readable ang seconds.
    if seconds < 60:
        return f"{seconds:.2f} sec"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes} min {remaining_seconds:.2f} sec"


def add_line(lines, text=""):
    # Magdagdag ng isang line sa report.
    lines.append(str(text))


def add_header(lines, title):
    # Magdagdag ng section header sa report.
    add_line(lines, "")
    add_line(lines, "=" * 70)
    add_line(lines, title)
    add_line(lines, "=" * 70)


def show_status(text):
    # Minimal terminal status.
    print(text, flush=True)


def save_result(lines, result_file=INGEST_RESULT_FILE):
    # I-save ang full ingest report.
    result_path = Path(result_file)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text("\n".join(lines), encoding="utf-8")


@contextmanager
def timer(stage_name, timings, lines):
    # Timer para sa bawat ingest stage.
    show_status(f"[START] {stage_name}")
    add_line(lines, f"[START] {stage_name}")
    start_time = time.perf_counter()

    try:
        yield
    except Exception as error:
        elapsed_time = time.perf_counter() - start_time
        timings[stage_name] = elapsed_time
        show_status(f"[FAILED] {stage_name} - {format_seconds(elapsed_time)}")
        add_line(lines, f"[FAILED] {stage_name} - {format_seconds(elapsed_time)}")
        add_line(lines, f"Error type    : {type(error).__name__}")
        add_line(lines, f"Error message : {error}")
        raise
    else:
        elapsed_time = time.perf_counter() - start_time
        timings[stage_name] = elapsed_time
        show_status(f"[DONE]  {stage_name} - {format_seconds(elapsed_time)}")
        add_line(lines, f"[DONE]  {stage_name} - {format_seconds(elapsed_time)}")


def read_json(path):
    # Safe JSON reader.
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path, data):
    # Safe JSON writer.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_ingest_metadata():
    # Current data signature para malaman kung stale na ang vector DB.
    return {
        "data_path": str(DATA_PATH),
        "data_signature": get_file_signature(DATA_PATH),
    }


def chroma_is_current():
    # Current lang kapag may Chroma files at tugma ang ingest metadata.
    if not has_chroma_files(CHROMA_PATH):
        return False

    return read_json(INGEST_META_FILE) == get_ingest_metadata()


def should_skip_ingest():
    # Skip lang kapag current ang ChromaDB at hindi naka-force.
    return chroma_is_current() and not FORCE_REINGEST


def add_start_section(lines):
    # Starting information ng ingest report.
    add_header(lines, "RAG INGESTION STARTED")
    add_line(lines, f"Data path         : {DATA_PATH}")
    add_line(lines, f"Persist directory : {CHROMA_PATH}")
    add_line(lines, f"Result file       : {INGEST_RESULT_FILE}")
    add_line(lines, f"Force re-ingest   : {FORCE_REINGEST}")


def add_loader_report(lines, report):
    # Summary ng document loader.
    add_header(lines, "DOCUMENT LOADER REPORT")
    add_line(lines, f"Loaded files      : {report.get('loaded_files', 0)}")
    add_line(lines, f"Loaded documents  : {report.get('loaded_docs', 0)}")
    add_line(lines, f"Skipped files     : {len(report.get('skipped_files', []))}")
    add_line(lines, f"Failed files      : {len(report.get('failed_files', []))}")

    if report.get("failed_files"):
        add_line(lines, "")
        add_line(lines, "Failed file details:")
        for item in report["failed_files"]:
            add_line(lines, f"- {item['file_path']} | {item['error_type']}: {item['error_message']}")

    if report.get("skipped_files"):
        add_line(lines, "")
        add_line(lines, "Skipped file details:")
        for item in report["skipped_files"]:
            add_line(lines, f"- {item['file_path']} | {item['reason']}")


def add_skip_section(lines):
    # Reason kung bakit na-skip ang ingestion.
    add_header(lines, "INGESTION SKIPPED")
    add_line(lines, f"Existing vector database is current : {CHROMA_PATH}")
    add_line(lines, "Reason                              : Data files did not change")
    add_line(lines, "")
    add_line(lines, "To force re-ingestion in PowerShell:")
    add_line(lines, '  $env:FORCE_REINGEST="1"')
    add_line(lines, "  python ingest.py")
    add_line(lines, "")
    add_line(lines, "To force re-ingestion in CMD:")
    add_line(lines, "  set FORCE_REINGEST=1")
    add_line(lines, "  python ingest.py")


def add_summary_section(lines, docs, cleaned_docs, chunks, vector_count, timings):
    # Final summary ng ingest.
    total_time = sum(timings.values())

    add_header(lines, "INGESTION SUMMARY")
    add_line(lines, f"Documents loaded  : {len(docs)}")
    add_line(lines, f"Cleaned documents : {len(cleaned_docs)}")
    add_line(lines, f"Chunks created    : {len(chunks)}")
    add_line(lines, f"Vectors saved     : {vector_count}")
    add_line(lines, f"Vector DB folder  : {CHROMA_PATH}")

    add_line(lines, "")
    add_line(lines, "Timing:")

    for stage_name, elapsed_time in timings.items():
        percent = (elapsed_time / total_time * 100) if total_time else 0
        add_line(lines, f"- {stage_name:<24} {format_seconds(elapsed_time):>14} ({percent:>5.1f}%)")

    add_line(lines, "")
    add_line(lines, f"Total time        : {format_seconds(total_time)}")

    if timings:
        slowest_stage = max(timings, key=timings.get)
        add_line(lines, f"Main bottleneck   : {slowest_stage}")


def show_terminal_summary(timings):
    # Maikling timing summary sa terminal.
    total_time = sum(timings.values())

    show_status("")
    show_status("INGESTION TIMING SUMMARY")
    show_status("-" * 40)

    for stage_name, elapsed_time in timings.items():
        show_status(f"{stage_name:<24}: {format_seconds(elapsed_time)}")

    show_status("-" * 40)
    show_status(f"Total time              : {format_seconds(total_time)}")
    show_status(f"Full report saved to    : {INGEST_RESULT_FILE}")


def rebuild_chroma_if_needed():
    # Burahin ang old Chroma kapag re-ingest para iwas duplicate vectors.
    if has_chroma_files(CHROMA_PATH):
        reset_chroma_folder(CHROMA_PATH)


def run_ingestion(lines, timings):
    # Load documents.
    with timer("Load documents", timings, lines):
        docs, loader_report = load_documents(
            DATA_PATH,
            recursive=LOAD_RECURSIVE,
            return_report=True,
        )

    add_loader_report(lines, loader_report)

    if not docs:
        raise ValueError("No documents were loaded. Check your data folder.")

    # Clean documents.
    with timer("Clean documents", timings, lines):
        cleaned_docs = clean_documents(docs)

    if not cleaned_docs:
        raise ValueError("No cleaned documents were created. Check your cleaner.")

    # Chunk documents.
    with timer("Chunk documents", timings, lines):
        chunks = chunk_documents(cleaned_docs)

    if not chunks:
        raise ValueError("No chunks were created. Check your chunker.")

    # Save chunk cache para mabilis ang test/chatbot startup.
    with timer("Save chunk cache", timings, lines):
        save_chunks_cache(chunks, data_path=DATA_PATH)

    # Load embedding model.
    with timer("Load embedding model", timings, lines):
        embedding_model = get_embedding_model()

    # Reset old Chroma and embed fresh vectors.
    with timer("Embed and save vectors", timings, lines):
        rebuild_chroma_if_needed()
        vectorstore = create_chroma_vectorstore(
            chunks=chunks,
            embedding_model=embedding_model,
            persist_directory=CHROMA_PATH,
        )
        vector_count = get_chroma_document_count(vectorstore)
        write_json(INGEST_META_FILE, get_ingest_metadata())

    return docs, cleaned_docs, chunks, vector_count


def main():
    # Main runner ng ingestion.
    lines = []
    timings = {}

    show_status("RAG ingestion started...")
    show_status(f"Data path         : {DATA_PATH}")
    show_status(f"Persist directory : {CHROMA_PATH}")
    show_status(f"Result file       : {INGEST_RESULT_FILE}")
    show_status("")

    add_start_section(lines)

    try:
        validate_data_path(DATA_PATH)

        if should_skip_ingest():
            show_status("[SKIPPED] Existing ChromaDB is current. No embedding was performed.")
            show_status(f"Full report saved to: {INGEST_RESULT_FILE}")
            add_skip_section(lines)
            return

        docs, cleaned_docs, chunks, vector_count = run_ingestion(lines, timings)
        add_summary_section(lines, docs, cleaned_docs, chunks, vector_count, timings)
        add_header(lines, "EMBEDDING SUCCESS")
        show_terminal_summary(timings)

    except Exception as error:
        add_header(lines, "INGESTION FAILED")
        add_line(lines, f"Error type    : {type(error).__name__}")
        add_line(lines, f"Error message : {error}")

        show_status("")
        show_status("[FAILED] RAG ingestion failed.")
        show_status(f"Error type    : {type(error).__name__}")
        show_status(f"Error message : {error}")
        show_status(f"Full report saved to: {INGEST_RESULT_FILE}")

    finally:
        save_result(lines)


if __name__ == "__main__":
    main()
