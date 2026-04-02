import logging

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# System prompt — this is the KEY to good RAG answers
# It constrains the LLM to ONLY use provided context, cite sources,
# and say "I don't know" when the context doesn't contain the answer.
# Without this, the LLM would hallucinate from its training data.
SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided document chunks.

Rules:
1. ONLY use information from the provided chunks to answer. Do NOT use your training data.
2. Cite your sources using [Page X] format after each claim.
3. If the chunks don't contain enough information to answer, say "I don't have enough information in the provided documents to answer this question."
4. Be concise and direct. Don't add filler or unnecessary context.
5. If multiple chunks support the same point, cite all relevant pages."""


def generate_answer(query: str, chunks: list[dict]) -> str:
    """
    Generate an answer using Gemini, grounded in the provided chunks.

    Input:
    - query: the user's question
    - chunks: top re-ranked chunks (each has "text", "page_number")

    The prompt structure:
    1. System instructions (how to behave)
    2. Context (the actual chunks with page numbers)
    3. Question (what the user asked)
    """
    # Build context from chunks
    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"[Page {chunk['page_number']}]:\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Build the full prompt
    user_prompt = f"""Context from the document:

{context}

---

Question: {query}

Answer based ONLY on the context above. Cite pages using [Page X] format."""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=user_prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.1,  # low = more factual, less creative
        },
    )

    answer = response.text
    logger.info(f"Generated answer ({len(answer)} chars) for query: {query[:50]}...")

    return answer
