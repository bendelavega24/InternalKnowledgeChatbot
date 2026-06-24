"""Small session-memory helper for follow-up questions."""

MEMORY_KEY = "chat_memory"


def init_memory(st):
    # Gumawa ng memory list once per Streamlit session.
    st.session_state.setdefault(MEMORY_KEY, [])


def get_conversation_history(st, limit=6):
    # Ibalik ang latest turns bilang prompt-ready text.
    init_memory(st)
    memory = st.session_state.get(MEMORY_KEY, [])

    if limit is not None:
        memory = memory[-limit:]

    return "\n".join(memory)


def save_to_memory(st, question, answer):
    # Isave ang isang user/assistant exchange.
    init_memory(st)
    question = str(question or "").strip()
    answer = str(answer or "").strip()

    if not question and not answer:
        return

    st.session_state[MEMORY_KEY].extend([
        f"User: {question}",
        f"Assistant: {answer}",
    ])


def rebuild_conversation_memory(st, messages):
    # I-rebuild ang prompt memory base sa visible chat messages.
    rebuilt = []
    last_question = None

    for message in messages or []:
        role = message.get("role")
        content = str(message.get("content", "")).strip()

        if not content:
            continue

        if role == "user":
            last_question = content
            continue

        if role == "assistant" and last_question:
            rebuilt.extend([
                f"User: {last_question}",
                f"Assistant: {content}",
            ])
            last_question = None

    st.session_state[MEMORY_KEY] = rebuilt


def clear_conversation_memory(st):
    # Burahin ang memory ng current Streamlit session.
    st.session_state[MEMORY_KEY] = []
