from langchain_core.embeddings import Embeddings

from analyzer.rag import build_knowledge_index, get_rules_search_tool


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[float(len(text) % 7), float(index)] for index, text in enumerate(texts)]

    def embed_query(self, text):
        return [float(len(text) % 7), 0.0]


def test_build_knowledge_index_indexes_markdown_docs(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "doc1.md").write_text("Ramp means accelerating your available mana.")
    cache_dir = tmp_path / "cache"

    index = build_knowledge_index(knowledge_dir=knowledge_dir, cache_dir=cache_dir, embeddings=FakeEmbeddings())

    results = index.similarity_search("ramp", k=1)
    assert "Ramp means" in results[0].page_content
    assert (cache_dir / "docs_hash.txt").exists()


def test_build_knowledge_index_reuses_cache_when_docs_unchanged(tmp_path, monkeypatch):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "doc1.md").write_text("Removal destroys or exiles a permanent.")
    cache_dir = tmp_path / "cache"
    embeddings = FakeEmbeddings()

    build_knowledge_index(knowledge_dir=knowledge_dir, cache_dir=cache_dir, embeddings=embeddings)

    import analyzer.rag as rag_module

    def fail_if_called(_knowledge_dir):
        raise AssertionError("_load_documents should not be called when the cache is still valid")

    monkeypatch.setattr(rag_module, "_load_documents", fail_if_called)

    build_knowledge_index(knowledge_dir=knowledge_dir, cache_dir=cache_dir, embeddings=embeddings)


def test_build_knowledge_index_rebuilds_when_docs_change(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    doc_path = knowledge_dir / "doc1.md"
    doc_path.write_text("Removal destroys or exiles a permanent.")
    cache_dir = tmp_path / "cache"
    embeddings = FakeEmbeddings()

    build_knowledge_index(knowledge_dir=knowledge_dir, cache_dir=cache_dir, embeddings=embeddings)

    doc_path.write_text("Card draw gives you extra cards in hand.")
    index = build_knowledge_index(knowledge_dir=knowledge_dir, cache_dir=cache_dir, embeddings=embeddings)

    results = index.similarity_search("draw", k=1)
    assert "Card draw" in results[0].page_content


def test_get_rules_search_tool_wraps_index_as_named_tool(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "doc1.md").write_text("Card draw gives you extra cards in hand.")
    cache_dir = tmp_path / "cache"
    index = build_knowledge_index(knowledge_dir=knowledge_dir, cache_dir=cache_dir, embeddings=FakeEmbeddings())

    tool = get_rules_search_tool(index=index)

    assert tool.name == "search_mtg_rules_and_brackets"
