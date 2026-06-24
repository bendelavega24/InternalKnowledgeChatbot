import argparse
from pathlib import Path

from test_utils import (
    clean_preview,
    prepare_project_path,
    resolve_from_project,
    write_report,
)

PROJECT_ROOT = prepare_project_path(__file__)

from config.settings import DATA_PATH, LOAD_RECURSIVE, PREVIEW_CHARS
from loaders.document_loader import load_documents


DEFAULT_OUTPUT_FILE = Path(__file__).resolve().parent / "document_loader_test_result.txt"


def build_result_text(documents, report, preview_chars, max_preview_docs):
    # Gumawa ng readable terminal/report output.
    lines = [
        "DOCUMENT LOADER TEST RESULT",
        "=" * 50,
        f"Data folder      : {report['data_path']}",
        f"Recursive        : {report['recursive']}",
        f"Loaded files     : {report['loaded_files']}",
        f"Loaded documents : {report['loaded_docs']}",
        f"Skipped files    : {len(report['skipped_files'])}",
        f"Failed files     : {len(report['failed_files'])}",
        "",
        "LOADED FILES",
        "-" * 50,
    ]

    if report["loaded_file_details"]:
        for item in report["loaded_file_details"]:
            lines.append(f"- {item['file_name']} | {item['docs_loaded']} docs")
    else:
        lines.append("No loaded files.")

    lines.extend(["", "FAILED FILES", "-" * 50])

    if report["failed_files"]:
        for item in report["failed_files"]:
            lines.append(f"- {item['file_path']}")
            lines.append(f"  {item['error_type']}: {item['error_message']}")
    else:
        lines.append("No failed files.")

    lines.extend(["", "SKIPPED FILES", "-" * 50])

    if report["skipped_files"]:
        for item in report["skipped_files"]:
            lines.append(f"- {item['file_path']}")
            lines.append(f"  Reason: {item['reason']}")
    else:
        lines.append("No skipped files.")

    lines.extend(["", "DOCUMENT PREVIEW", "-" * 50])

    if documents:
        for index, doc in enumerate(documents[:max_preview_docs], start=1):
            metadata = doc.metadata or {}
            lines.append(f"Document #{index}")
            lines.append(f"File   : {metadata.get('file_name', 'N/A')}")
            lines.append(f"Source : {metadata.get('source', 'N/A')}")
            lines.append(f"Preview: {clean_preview(doc.page_content, preview_chars)}")
            lines.append("")
    else:
        lines.append("No document preview available.")

    return "\n".join(lines)


def main():
    # Main runner ng document loader test.
    parser = argparse.ArgumentParser(description="Test loaders/document_loader.py")
    parser.add_argument("data_path", nargs="?", default=DATA_PATH, help="Document folder. Default comes from config/settings.py")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Output .txt file path")
    parser.add_argument("--no-recursive", action="store_true", help="Do not read subfolders")
    parser.add_argument("--preview-chars", type=int, default=PREVIEW_CHARS, help="Preview characters per document")
    parser.add_argument("--max-preview-docs", type=int, default=5, help="Number of documents to preview")
    args = parser.parse_args()

    data_path = resolve_from_project(PROJECT_ROOT, args.data_path)
    output_path = Path(args.output)

    if not output_path.is_absolute():
        output_path = Path(__file__).resolve().parent / output_path

    try:
        documents, report = load_documents(
            data_path=data_path,
            recursive=LOAD_RECURSIVE and not args.no_recursive,
            return_report=True,
        )

        result_text = build_result_text(
            documents=documents,
            report=report,
            preview_chars=args.preview_chars,
            max_preview_docs=args.max_preview_docs,
        )

    except Exception as error:
        result_text = "\n".join([
            "DOCUMENT LOADER TEST RESULT",
            "=" * 50,
            f"Data folder : {data_path}",
            "",
            "ERROR",
            "-" * 50,
            f"{type(error).__name__}: {error}",
        ])

    write_report(output_path, result_text)
    print(result_text)
    print(f"\nResult saved to: {output_path}")


if __name__ == "__main__":
    main()
