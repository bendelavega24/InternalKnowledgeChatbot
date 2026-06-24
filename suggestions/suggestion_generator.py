"""Generate short follow-up question suggestions."""

import re

MAX_SUGGESTIONS = 3
MAX_WORDS_PER_SUGGESTION = 8
NO_ANSWER_MARKERS = [
    "i cannot find",
    "cannot find",
    "not found",
    "wala sa",
    "hindi ko mahanap",
]


def extract_text(response):
    # LangChain/Ollama response -> plain text.
    if hasattr(response, "content"):
        return response.content

    return str(response)


def normalize_suggestion_lines(response_text):
    # Linisin ang model output at gawing max 3 unique suggestions.
    suggestions = []
    seen = set()

    for raw_line in str(response_text or "").splitlines():
        line = raw_line.strip().lstrip("-•123456789. )").strip()
        line = re.sub(r"^(Question|Suggestion)\s*\d*\s*:\s*", "", line, flags=re.I)

        if not line:
            continue

        for part in re.split(r"(?<=\?)\s+", line):
            part = part.strip()
            key = part.lower()

            if not part or key in seen:
                continue

            seen.add(key)
            suggestions.append(part)

            if len(suggestions) >= MAX_SUGGESTIONS:
                return suggestions

    return suggestions[:MAX_SUGGESTIONS]


def generate_suggestions(question, answer, llm):
    # Huwag mag-suggest kapag fallback/no-answer ang sagot.
    answer_text = str(answer or "")

    if any(marker in answer_text.lower() for marker in NO_ANSWER_MARKERS):
        return []

    prompt = f"""
Generate exactly 3 short follow-up questions.

Question:
{question}

Answer:
{answer}

Rules:
- One question per line.
- Maximum {MAX_WORDS_PER_SUGGESTION} words per question.
- Use the same language as the Question.
- Do not number them.
- Do not explain.
"""

    response = llm.invoke(prompt)
    return normalize_suggestion_lines(extract_text(response))
