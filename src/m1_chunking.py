"""
Module 1: Advanced Chunking Strategies
=======================================
Implement semantic, hierarchical, và structure-aware chunking.
So sánh với basic chunking (baseline) để thấy improvement.

Test: pytest tests/test_m1.py
"""

import os, sys, glob, re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (DATA_DIR, HIERARCHICAL_PARENT_SIZE, HIERARCHICAL_CHILD_SIZE,
                    SEMANTIC_THRESHOLD)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Load all markdown/text files from data/. (Đã implement sẵn)"""
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {"source": os.path.basename(fp)}})
    return docs


# ─── Baseline: Basic Chunking (để so sánh) ──────────────


def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    """
    Basic chunking: split theo paragraph (\\n\\n).
    Đây là baseline — KHÔNG phải mục tiêu của module này.
    (Đã implement sẵn)
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for i, para in enumerate(paragraphs):
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
    return chunks


# ─── Strategy 1: Semantic Chunking ───────────────────────


def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    """
    Split text by sentence similarity — nhóm câu cùng chủ đề.
    Tốt hơn basic vì không cắt giữa ý.

    Args:
        text: Input text.
        threshold: Cosine similarity threshold. Dưới threshold → tách chunk mới.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        List of Chunk objects grouped by semantic similarity.
    """
    metadata = metadata or {}
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n\n', text) if s.strip()]
    if not sentences:
        return []

    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences)

    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

    chunks = []
    current_group = [sentences[0]]
    for i in range(1, len(sentences)):
        sim = cosine_sim(embeddings[i - 1], embeddings[i])
        if sim < threshold:
            chunks.append(Chunk(
                text=" ".join(current_group),
                metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"}
            ))
            current_group = []
        current_group.append(sentences[i])
    if current_group:
        chunks.append(Chunk(
            text=" ".join(current_group),
            metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"}
        ))
    return chunks


# ─── Strategy 2: Hierarchical Chunking ──────────────────


def chunk_hierarchical(text: str, parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:
    """
    Parent-child hierarchy: retrieve child (precision) → return parent (context).
    Đây là default recommendation cho production RAG.

    Args:
        text: Input text.
        parent_size: Chars per parent chunk.
        child_size: Chars per child chunk.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        (parents, children) — mỗi child có parent_id link đến parent.
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    parents, children = [], []
    current, p_index = "", 0

    for para in paragraphs:
        if len(current) + len(para) > parent_size and current:
            pid = f"parent_{p_index}"
            parents.append(Chunk(
                text=current.strip(),
                metadata={**metadata, "chunk_type": "parent", "parent_id": pid}
            ))
            for j in range(0, len(current), child_size):
                child_text = current[j:j + child_size].strip()
                if child_text:
                    children.append(Chunk(
                        text=child_text,
                        metadata={**metadata, "chunk_type": "child"},
                        parent_id=pid
                    ))
            p_index += 1
            current = ""
        current += para + "\n\n"

    if current.strip():
        pid = f"parent_{p_index}"
        parents.append(Chunk(
            text=current.strip(),
            metadata={**metadata, "chunk_type": "parent", "parent_id": pid}
        ))
        for j in range(0, len(current), child_size):
            child_text = current[j:j + child_size].strip()
            if child_text:
                children.append(Chunk(
                    text=child_text,
                    metadata={**metadata, "chunk_type": "child"},
                    parent_id=pid
                ))

    return parents, children


# ─── Strategy 3: Structure-Aware Chunking ────────────────


def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """
    Parse markdown headers → chunk theo logical structure.
    Giữ nguyên tables, code blocks, lists — không cắt giữa chừng.

    Args:
        text: Markdown text.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        List of Chunk objects, mỗi chunk = 1 section (header + content).
    """
    metadata = metadata or {}
    sections = re.split(r'(^#{1,3}\s+.+$)', text, flags=re.MULTILINE)
    chunks = []
    current_header, current_content = "", ""

    for part in sections:
        if re.match(r'^#{1,3}\s+', part):
            if current_content.strip():
                chunks.append(Chunk(
                    text=f"{current_header}\n{current_content}".strip(),
                    metadata={**metadata, "section": current_header.strip(), "strategy": "structure"}
                ))
            current_header = part.strip()
            current_content = ""
        else:
            current_content += part

    if current_content.strip():
        chunks.append(Chunk(
            text=f"{current_header}\n{current_content}".strip(),
            metadata={**metadata, "section": current_header.strip(), "strategy": "structure"}
        ))
    return chunks


# ─── A/B Test: Compare All Strategies ────────────────────


def compare_strategies(documents: list[dict]) -> dict:
    """
    Run all strategies on documents and compare.

    Returns:
        {"basic": {...}, "semantic": {...}, "hierarchical": {...}, "structure": {...}}
    """
    results = {}
    for strategy, fn in [
        ("basic",     lambda d: chunk_basic(d["text"], metadata=d["metadata"])),
        ("semantic",  lambda d: chunk_semantic(d["text"], metadata=d["metadata"])),
        ("structure", lambda d: chunk_structure_aware(d["text"], metadata=d["metadata"])),
    ]:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(fn(doc))
        lengths = [len(c.text) for c in all_chunks]
        results[strategy] = {
            "num_chunks": len(all_chunks),
            "avg_length": int(sum(lengths) / max(len(lengths), 1)),
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
        }

    p_all, c_all = [], []
    for doc in documents:
        p, c = chunk_hierarchical(doc["text"], metadata=doc["metadata"])
        p_all.extend(p)
        c_all.extend(c)
    lengths = [len(c.text) for c in c_all]
    results["hierarchical"] = {
        "num_chunks": f"{len(p_all)}p/{len(c_all)}c",
        "avg_length": int(sum(lengths) / max(len(lengths), 1)),
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
    }

    print(f"\n{'Strategy':<15} | {'Chunks':>8} | {'Avg Len':>8} | {'Min':>6} | {'Max':>6}")
    print("-" * 55)
    for name, stats in results.items():
        print(f"{name:<15} | {str(stats['num_chunks']):>8} | {stats['avg_length']:>8} | {stats['min_length']:>6} | {stats['max_length']:>6}")
    return results


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    results = compare_strategies(docs)
    for name, stats in results.items():
        print(f"  {name}: {stats}")
