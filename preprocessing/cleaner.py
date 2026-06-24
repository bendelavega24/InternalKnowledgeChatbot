import re

from langchain_core.documents import Document

from config.settings import MIN_CLEAN_TEXT_LENGTH


REFERENCE_HEADINGS = (
    "references",
    "notes",
    "external links",
    "see also",
    "bibliography",
    "further reading",
)

NOISE_KEYWORDS = (
    "http://",
    "https://",
    "retrieved",
    "archived",
    "isbn",
    "web.archive.org",
    "books.google.com",
    "internet archive",
    "librivox",
    "jstor",
)

MONTH_PATTERN = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)


def is_noise_line(line):
    # Tanggalin ang obvious scraped/footer noise, pero huwag maging harsh sa SOP/Japanese text.
    line = str(line or "").strip()
    lower = line.lower()

    if not line:
        return True

    if lower.endswith("- wikipedia") and len(line) < 100:
        return True

    if re.fullmatch(r"\d+\s*/\s*\d+", line):
        return True

    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(am|pm)?", lower):
        return True

    if any(keyword in lower for keyword in NOISE_KEYWORDS):
        return True

    return False


def remove_reference_sections(text):
    # Tanggalin ang references section kapag nasa dulo na ng document.
    headings = "|".join(re.escape(heading) for heading in REFERENCE_HEADINGS)
    pattern = re.compile(
        rf"(^|\n)\s*#{{0,6}}\s*\*{{0,2}}\s*({headings})\s*\*{{0,2}}\s*(\n|$)",
        flags=re.IGNORECASE,
    )
    match = pattern.search(text)

    if match and match.start() > 300:
        return text[:match.start()]

    return text


def remove_markdown_and_links(text):
    # Gawing plain text ang markdown links at citations.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\[\d+\]", " ", text)
    text = re.sub(r"[-_=*#~—]{3,}", " ", text)
    text = re.sub(r"[_`~]+", " ", text)
    return text


def normalize_symbols(text):
    # Tanggalin control chars at symbols na karaniwang extraction noise.
    text = text.replace("�", " ")
    text = re.sub(r"[\x00-\x09\x0B-\x1F\x7F-\x9F]", " ", text)
    text = re.sub(r"[«»§¤©®™†‡•]", " ", text)
    text = re.sub(r"\|{2,}", " ", text)
    return text


def fix_common_ocr_errors(text):
    # Maliit na OCR fixes; hindi domain-specific sa final company docs.
    text = re.sub(r"~*—+\s*ccx«\s*a~*", " ", text, flags=re.IGNORECASE)
    text = re.sub(
        rf"\b({MONTH_PATTERN})\s+a\s+(\d{{1,2}})",
        r"\1 \2",
        text,
        flags=re.IGNORECASE,
    )

    replacements = {
        r"\bdisbande d\b": "disbanded",
        r"\blepros\s+y\b": "leprosy",
        r"Generalof": "General of",
    }

    for wrong_text, correct_text in replacements.items():
        text = re.sub(wrong_text, correct_text, text, flags=re.IGNORECASE)

    text = re.sub(r"Jesú\s+s", "Jesús", text)
    text = re.sub(r"\bccx\b", " ", text, flags=re.IGNORECASE)
    return text.replace("<<", "")


def normalize_spacing(text):
    # Ayusin ang sobrang spaces at blank lines.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def clean_text(text):
    # Main cleaning flow bago chunking at embedding.
    if not text:
        return ""

    text = str(text)
    text = remove_reference_sections(text)
    text = remove_markdown_and_links(text)
    text = normalize_symbols(text)
    text = fix_common_ocr_errors(text)

    clean_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not is_noise_line(line):
            clean_lines.append(line)

    return normalize_spacing("\n".join(clean_lines))


def clean_documents(docs, min_length=MIN_CLEAN_TEXT_LENGTH):
    # Linisin ang list of LangChain Document objects.
    cleaned_docs = []

    for doc in docs or []:
        cleaned_text = clean_text(getattr(doc, "page_content", ""))

        if len(cleaned_text) < min_length:
            continue

        cleaned_docs.append(
            Document(
                page_content=cleaned_text,
                metadata=dict(doc.metadata or {}),
            )
        )

    return cleaned_docs
