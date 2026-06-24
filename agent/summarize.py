"""map-reduce summarisation for context that's too big for one prompt.

split the text into chunks, summarise each chunk (the "map"), then summarise the joined
summaries (the "reduce"). it recurses if the combined summaries are still too long, so it
scales to arbitrarily large inputs. the per-chunk summariser is injectable, so the chunking
and reduction logic is fully testable without a model.
"""

from __future__ import annotations


def chunk(text: str, size: int = 1200) -> list[str]:
    """split text into ~size-character chunks, breaking on paragraph then whitespace."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, buf = [], ""
    for para in text.split("\n\n"):
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}" if buf else para
        else:
            if buf:
                chunks.append(buf)
            # a single paragraph bigger than `size` gets hard-split on words
            while len(para) > size:
                cut = para.rfind(" ", 0, size)
                cut = cut if cut > 0 else size
                chunks.append(para[:cut].strip())
                para = para[cut:].strip()
            buf = para
    if buf:
        chunks.append(buf)
    return chunks


def _default_summarizer(settings=None):
    from agent.llm import complete

    def summarize_one(text: str) -> str:
        return complete(
            f"Summarise the following faithfully in 2-3 sentences:\n\n{text}",
            settings=settings,
            system="You are a precise summariser. Keep facts, drop filler.",
        )

    return summarize_one


def summarize(
    text: str,
    summarize_one=None,
    chunk_size: int = 1200,
    max_depth: int = 3,
    settings=None,
) -> str:
    """summarise `text` by mapping over chunks and reducing. returns the final summary."""
    summarize_one = summarize_one or _default_summarizer(settings)
    chunks = chunk(text, chunk_size)
    if not chunks:
        return ""
    if len(chunks) == 1:
        return summarize_one(chunks[0]).strip()

    summaries = [summarize_one(c).strip() for c in chunks]
    combined = "\n\n".join(summaries)
    if max_depth <= 1 or len(combined) <= chunk_size:
        return summarize_one(combined).strip()
    # still too big -> recurse on the combined summaries
    return summarize(combined, summarize_one, chunk_size, max_depth - 1, settings)
