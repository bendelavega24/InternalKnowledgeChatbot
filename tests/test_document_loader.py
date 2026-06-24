from pathlib import Path
import argparse
import sys


## Inaayos ang import path para makita ang loaders folder kahit saan i-run.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from loaders.document_loader import load_documents


## Nililinis ang preview para readable sa terminal at output file.
def clean_preview(text, limit):
    if not text:
        return ""

    text = str(text).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = " ".join(text.split())

    if len(text) > limit:
        return text[:limit].rstrip() + "..."

    return text


## Gumagawa ng readable text output ng test result.
def build_output_text(output_path, docs, report, preview_chars, max_preview_docs):
    lines = []

    lines.append("=" * 60)
    lines.append("DOCUMENT LOADER TEST RESULT")
    lines.append("=" * 60)
    lines.append(f"Data folder          : {report['data_path']}")
    lines.append(f"Recursive loading    : {report['recursive']}")
    lines.append(f"Output file          : {output_path}")
    lines.append(f"Supported extensions : {', '.join(report['supported_extensions'])}")
    lines.append("")
    lines.append(f"Loaded files         : {report['loaded_files']}")
    lines.append(f"Loaded docs          : {report['loaded_docs']}")
    lines.append(f"Skipped files        : {len(report['skipped_files'])}")
    lines.append(f"Failed files         : {len(report['failed_files'])}")

    lines.append("")
    lines.append("LOADED FILES")
    lines.append("-" * 60)

    if report["loaded_file_details"]:
        for item in report["loaded_file_details"]:
            lines.append(f"File : {item['file_name']}")
            lines.append(f"Path : {item['file_path']}")
            lines.append(f"Type : {item['file_ext']}")
            lines.append(f"Docs : {item['docs_loaded']}")
            lines.append("")
    else:
        lines.append("No files were loaded.")

    lines.append("")
    lines.append("DOCUMENT PREVIEW")
    lines.append("-" * 60)

    if docs:
        for index, doc in enumerate(docs[:max_preview_docs], start=1):
            metadata = getattr(doc, "metadata", {}) or {}
            source = metadata.get("source", "")
            file_name = metadata.get("file_name", Path(source).name if source else "Unknown")
            page = metadata.get("page", metadata.get("page_number", ""))
            content = getattr(doc, "page_content", "")

            lines.append(f"Doc #{index}")
            lines.append(f"File    : {file_name}")
            lines.append(f"Source  : {source}")

            if page != "":
                lines.append(f"Page    : {page}")

            lines.append(f"Chars   : {len(content)}")
            lines.append(f"Preview : {clean_preview(content, preview_chars)}")
            lines.append("")
    else:
        lines.append("No document preview available.")

    if report["skipped_files"]:
        lines.append("")
        lines.append("SKIPPED FILES")
        lines.append("-" * 60)

        for item in report["skipped_files"]:
            lines.append(f"File   : {item['file_path']}")
            lines.append(f"Reason : {item['reason']}")
            lines.append("")

    if report["failed_files"]:
        lines.append("")
        lines.append("FAILED FILES")
        lines.append("-" * 60)

        for item in report["failed_files"]:
            lines.append(f"File  : {item['file_path']}")
            lines.append(f"Error : {item['error_type']} - {item['error_message']}")
            lines.append("")

    return "\n".join(lines)


## Ito ang function na tatawagin ng main.py.
def run_document_loader_test(
    data_path="data",
    output_file="document_loader_test_output.txt",
    recursive=True,
    preview_chars=250,
    max_preview_docs=10,
):
    data_path = Path(data_path)
    output_path = Path(output_file)

    try:
        docs, report = load_documents(
            data_path=data_path,
            recursive=recursive,
            return_report=True,
        )

        output_text = build_output_text(
            output_path=output_path,
            docs=docs,
            report=report,
            preview_chars=preview_chars,
            max_preview_docs=max_preview_docs,
        )

    except Exception as error:
        output_text = "\n".join(
            [
                "=" * 60,
                "DOCUMENT LOADER TEST RESULT",
                "=" * 60,
                f"Data folder : {data_path}",
                f"Output file : {output_path}",
                "",
                "ERROR",
                "-" * 60,
                f"{type(error).__name__}: {error}",
            ]
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")

    print(output_text)
    print("")
    print(f"Saved test output to: {output_path}")


## Optional: pwede pa rin i-run direct itong test file kung kailangan.
def main():
    parser = argparse.ArgumentParser(description="Test document loading output.")
    parser.add_argument("data_path", nargs="?", default="data", help="Folder path ng documents.")
    parser.add_argument("--output", default="document_loader_test_output.txt", help="Output text file path.")
    parser.add_argument("--no-recursive", action="store_true", help="Huwag basahin ang subfolders.")
    parser.add_argument("--preview-chars", type=int, default=250, help="Preview characters per document.")
    parser.add_argument("--max-preview-docs", type=int, default=10, help="Maximum docs na ipi-preview.")
    args = parser.parse_args()

    run_document_loader_test(
        data_path=args.data_path,
        output_file=args.output,
        recursive=not args.no_recursive,
        preview_chars=args.preview_chars,
        max_preview_docs=args.max_preview_docs,
    )


if __name__ == "__main__":
    main()
