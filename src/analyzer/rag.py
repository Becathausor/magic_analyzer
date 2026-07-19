"""RAG over the MTG knowledge documents (data/knowledge/): rules, glossary,
archetypes and the WotC Commander Bracket system.

Documents are chunked and embedded once, then the FAISS index is cached to
disk (data/.knowledge_index/) and only rebuilt when the documents change.
"""

from __future__ import annotations

import hashlib
import logging
import pathlib

from langchain_classic.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.tools import BaseTool
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .langchain_client import get_embeddings

logger = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"
INDEX_CACHE_DIR = PROJECT_ROOT / "data" / ".knowledge_index"
HASH_FILENAME = "docs_hash.txt"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

RETRIEVER_TOOL_NAME = "search_mtg_rules_and_brackets"
RETRIEVER_TOOL_DESCRIPTION = (
    "Search MTG Commander reference material: glossary definitions (ramp, removal, "
    "card draw, win conditions), common deck archetypes, and the WotC Commander "
    "Bracket system (1 to 5) definitions and restrictions."
)


def _load_documents(knowledge_dir: pathlib.Path) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    documents = []
    for path in sorted(knowledge_dir.glob("*.md")):
        for chunk in splitter.split_text(path.read_text()):
            documents.append(Document(page_content=chunk, metadata={"source": path.name}))
    return documents


def _docs_hash(knowledge_dir: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(knowledge_dir.glob("*.md")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_knowledge_index(
    *,
    knowledge_dir: pathlib.Path = KNOWLEDGE_DIR,
    cache_dir: pathlib.Path = INDEX_CACHE_DIR,
    embeddings: Embeddings | None = None,
) -> FAISS:
    """Build (or load from cache) the FAISS index over the knowledge documents."""
    embeddings = embeddings or get_embeddings()
    current_hash = _docs_hash(knowledge_dir)
    hash_file = cache_dir / HASH_FILENAME

    if hash_file.exists() and hash_file.read_text() == current_hash:
        try:
            return FAISS.load_local(str(cache_dir), embeddings, allow_dangerous_deserialization=True)
        except Exception:
            logger.exception("Failed to load cached knowledge index, rebuilding")

    documents = _load_documents(knowledge_dir)
    index = FAISS.from_documents(documents, embeddings)
    cache_dir.mkdir(parents=True, exist_ok=True)
    index.save_local(str(cache_dir))
    hash_file.write_text(current_hash)
    return index


def get_rules_search_tool(
    *,
    index: FAISS | None = None,
    embeddings: Embeddings | None = None,
) -> BaseTool:
    """Return a LangChain tool the synthesis agent can call to search the knowledge base."""
    index = index or build_knowledge_index(embeddings=embeddings)
    retriever = index.as_retriever(search_kwargs={"k": 4})
    return create_retriever_tool(
        retriever,
        name=RETRIEVER_TOOL_NAME,
        description=RETRIEVER_TOOL_DESCRIPTION,
    )
