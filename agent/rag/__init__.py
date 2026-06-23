"""retrieval augmented generation bits.

this is optional. if you do not install the rag extras (chromadb / faiss / sentence
transformers) none of this loads and the rest of the agent carries on fine. when it is
installed you can drop documents in, embed them, and let the agent search over them.
"""

from agent.rag.vectorstore import VectorStore, simple_chunk

__all__ = ["VectorStore", "simple_chunk"]
