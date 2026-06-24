"""Rewrite follow-up questions into standalone retrieval queries."""


def extract_text(response):
    # LangChain/Ollama response -> plain text.
    if hasattr(response, "content"):
        return response.content

    return str(response)


def clean_rewritten_question(text, fallback_question):
    # Kunin lang ang unang useful line para iwas explanation ng small models.
    text = str(text or "").strip()

    if not text:
        return fallback_question

    for label in ["Standalone Question:", "Rewritten Question:", "Question:", "Answer:"]:
        if text.lower().startswith(label.lower()):
            text = text[len(label):].strip()

    for line in text.splitlines():
        line = line.strip().strip('"').strip("'")

        if line:
            return line

    return fallback_question


def rewrite_question(question, chat_history, llm):
    # Rewrite lang kapag may chat history.
    question = str(question or "").strip()
    chat_history = str(chat_history or "").strip()

    if not question or not chat_history:
        return question

    prompt = f"""
Rewrite the follow-up question as one standalone question for document retrieval.

Conversation History:
{chat_history}

Follow-up Question:
{question}

Rules:
- Use history only to resolve references such as this, that, it, he, she, they, or the policy.
- Preserve the original meaning.
- Keep the same language as the follow-up question.
- Do not answer the question.
- Return only one standalone question.

Standalone Question:
"""

    response = llm.invoke(prompt)

    return clean_rewritten_question(
        text=extract_text(response),
        fallback_question=question,
    )
