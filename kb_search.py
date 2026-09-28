"""
Advanced Knowledge Base (KB) Search Engine & Tool Suite.
Provides heading-aware chunking, BM25 scoring with phrase match boosting,
structured JSON indexing, and section extraction for the Knowledge Retrieval Specialist.
"""

import sys
import os
import re
import math
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", "./knowledge"))


@dataclass
class KBChunk:
    """Represents an indexed snippet with rich document and heading hierarchy metadata."""
    document_name: str
    heading_path: str
    content: str
    chunk_type: str  # "markdown", "json", "text"
    chunk_id: int
    char_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.char_count = len(self.content)


class KBSearchEngine:
    """
    In-memory hybrid retrieval engine providing heading-aware markdown parsing,
    structured JSON traversal, and BM25-based relevance scoring with exact-phrase boosting.
    """

    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = Path(knowledge_dir or KNOWLEDGE_DIR)
        self.chunks: List[KBChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 1.0
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}  # term -> list of (chunk_id, term_freq)
        self.doc_names: List[str] = []
        self._build_index()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Normalizes and extracts alphanumeric tokens from text."""
        cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
        return tokens

    def _build_index(self):
        """Scans knowledge directory, parses documents, and builds the inverted search index."""
        self.chunks = []
        if not self.knowledge_dir.exists():
            return

        supported_files = list(self.knowledge_dir.glob("**/*.*"))
        chunk_counter = 0

        for file_path in supported_files:
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            if ext not in [".md", ".txt", ".json", ".rst", ".csv"]:
                continue

            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if ext == ".md":
                doc_chunks = self._parse_markdown(file_path.name, raw_text, start_id=chunk_counter)
            elif ext == ".json":
                doc_chunks = self._parse_json(file_path.name, raw_text, start_id=chunk_counter)
            else:
                doc_chunks = self._parse_plaintext(file_path.name, raw_text, start_id=chunk_counter)

            chunk_counter += len(doc_chunks)
            self.chunks.extend(doc_chunks)

        # Build Inverted Index & BM25 metrics
        self.inverted_index = {}
        self.doc_lengths = []
        total_tokens = 0

        for chunk in self.chunks:
            full_text = f"{chunk.heading_path} {chunk.content}"
            tokens = self._tokenize(full_text)
            self.doc_lengths.append(len(tokens))
            total_tokens += len(tokens)

            tf_map: Dict[str, int] = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            for term, count in tf_map.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((chunk.chunk_id, count))

        num_chunks = len(self.chunks)
        self.avg_doc_len = (total_tokens / num_chunks) if num_chunks > 0 else 1.0
        self.doc_names = sorted(list(set(c.document_name for c in self.chunks)))

    def _parse_markdown(self, filename: str, text: str, start_id: int) -> List[KBChunk]:
        """Splits markdown into chunks respecting heading hierarchies (#, ##, ###)."""
        chunks: List[KBChunk] = []
        lines = text.splitlines()
        current_headings: List[str] = []
        current_lines: List[str] = []
        cid = start_id

        def commit_chunk():
            nonlocal cid, current_lines
            content = "\n".join(current_lines).strip()
            if content:
                heading_path = " > ".join(current_headings) if current_headings else "Overview"
                chunks.append(KBChunk(
                    document_name=filename,
                    heading_path=heading_path,
                    content=content,
                    chunk_type="markdown",
                    chunk_id=cid
                ))
                cid += 1
            current_lines = []

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if header_match:
                commit_chunk()
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                # Maintain heading stack depth
                if len(current_headings) >= level:
                    current_headings = current_headings[:level - 1]
                current_headings.append(title)
            else:
                current_lines.append(line)

        commit_chunk()
        return chunks

    def _parse_json(self, filename: str, text: str, start_id: int) -> List[KBChunk]:
        """Flattens structured JSON into thematic key-path chunks."""
        chunks: List[KBChunk] = []
        try:
            data = json.loads(text)
        except Exception:
            return self._parse_plaintext(filename, text, start_id)

        cid = start_id

        def walk(obj: Any, prefix: str = ""):
            nonlocal cid
            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, (dict, list)):
                        walk(v, p)
                    else:
                        content = f"{p}: {v}"
                        chunks.append(KBChunk(
                            document_name=filename,
                            heading_path=f"JSON Key: {p}",
                            content=content,
                            chunk_type="json",
                            chunk_id=cid,
                            metadata={"key": p, "value": v}
                        ))
                        cid += 1
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    p = f"{prefix}[{idx}]"
                    if isinstance(item, (dict, list)):
                        walk(item, p)
                    else:
                        content = f"{p}: {item}"
                        chunks.append(KBChunk(
                            document_name=filename,
                            heading_path=f"JSON Array: {p}",
                            content=content,
                            chunk_type="json",
                            chunk_id=cid,
                            metadata={"key": p, "value": item}
                        ))
                        cid += 1

        walk(data)
        return chunks

    def _parse_plaintext(self, filename: str, text: str, start_id: int) -> List[KBChunk]:
        """Chunks generic plain-text by double newlines."""
        chunks: List[KBChunk] = []
        cid = start_id
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for idx, para in enumerate(paragraphs):
            chunks.append(KBChunk(
                document_name=filename,
                heading_path=f"Section {idx + 1}",
                content=para,
                chunk_type="text",
                chunk_id=cid
            ))
            cid += 1
        return chunks

    def search(
        self,
        query: str,
        top_k: int = 4,
        document_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 search over all indexed chunks with exact-phrase boosting
        and heading relevance weighting.
        """
        if not self.chunks:
            self._build_index()

        if not self.chunks:
            return []

        query_lower = query.lower().strip()
        tokens = self._tokenize(query)
        if not tokens:
            return []

        k1 = 1.5
        b = 0.75
        num_docs = len(self.chunks)
        scores: Dict[int, float] = {}

        # BM25 Term scoring
        for term in tokens:
            if term not in self.inverted_index:
                continue

            postings = self.inverted_index[term]
            df = len(postings)
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)

            for chunk_id, tf in postings:
                doc_len = self.doc_lengths[chunk_id]
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                term_score = idf * (numerator / denominator)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + term_score

        # Bonuses for Heading matches and Exact Phrase matches
        for chunk_id in scores.keys():
            chunk = self.chunks[chunk_id]

            # Filter by document name if requested
            if document_filter and document_filter.lower() not in chunk.document_name.lower():
                scores[chunk_id] = -1.0
                continue

            chunk_lower = chunk.content.lower()
            heading_lower = chunk.heading_path.lower()

            # Exact phrase match bonus
            if query_lower in chunk_lower:
                scores[chunk_id] += 6.0

            # Heading contains query terms
            heading_matches = sum(1 for t in tokens if t in heading_lower)
            if heading_matches > 0:
                scores[chunk_id] += (heading_matches * 2.5)

        # Filter and rank results
        ranked_chunk_ids = sorted(
            [cid for cid, s in scores.items() if s > 0],
            key=lambda cid: scores[cid],
            reverse=True
        )

        results: List[Dict[str, Any]] = []
        for cid in ranked_chunk_ids[:top_k]:
            chunk = self.chunks[cid]
            raw_score = scores[cid]
            # Normalized relevance percentage
            relevance = round(min(1.0, raw_score / 15.0), 2)
            results.append({
                "document": chunk.document_name,
                "heading": chunk.heading_path,
                "score": round(raw_score, 2),
                "relevance": relevance,
                "type": chunk.chunk_type,
                "content": chunk.content
            })

        return results

    def extract_section(self, document_name: str, heading_query: str) -> Optional[str]:
        """Extracts full content from a specific section matching a heading query."""
        if not self.chunks:
            self._build_index()

        h_query = heading_query.lower().strip()
        d_query = document_name.lower().strip()

        for chunk in self.chunks:
            if d_query in chunk.document_name.lower():
                if h_query in chunk.heading_path.lower():
                    return (
                        f"### [{chunk.document_name}] > {chunk.heading_path}\n\n"
                        f"{chunk.content}"
                    )
        return None

    def query_structured_json(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Queries exclusively structured JSON knowledge key-value paths."""
        json_results = []
        all_matches = self.search(query, top_k=top_k * 2)
        for m in all_matches:
            if m["type"] == "json":
                json_results.append(m)
                if len(json_results) >= top_k:
                    break
        return json_results

    def get_catalog(self) -> Dict[str, Any]:
        """Generates a complete catalog of available knowledge documents and indexed sections."""
        if not self.chunks:
            self._build_index()

        catalog: Dict[str, List[str]] = {}
        for chunk in self.chunks:
            doc = chunk.document_name
            if doc not in catalog:
                catalog[doc] = []
            if chunk.heading_path not in catalog[doc]:
                catalog[doc].append(chunk.heading_path)

        return {
            "total_documents": len(catalog),
            "total_chunks": len(self.chunks),
            "catalog": catalog
        }


# Global engine singleton
_kb_engine: Optional[KBSearchEngine] = None

def get_kb_engine() -> KBSearchEngine:
    global _kb_engine
    if _kb_engine is None:
        _kb_engine = KBSearchEngine()
    return _kb_engine


# ==========================================
# CrewAI BaseTools for Knowledge Retrieval Specialist
# ==========================================

class AdvancedKBSearchInput(BaseModel):
    query: str = Field(..., description="The concept, policy, topic, or question to search for in the knowledge base.")
    document_filter: Optional[str] = Field(None, description="Optional document filename to limit search scope (e.g., 'company_handbook.md').")
    top_k: int = Field(default=4, description="Maximum number of relevant excerpts to return (1 to 8).")


class AdvancedKBSearchTool(BaseTool):
    name: str = "Advanced KB Search Engine"
    description: str = (
        "High-precision hybrid search engine over company knowledge documents, guides, and manuals. "
        "Uses heading-aware chunking and BM25 scoring with exact phrase match boosting. "
        "Returns precise sections, document citations, and relevance scores."
    )
    args_schema: Type[BaseModel] = AdvancedKBSearchInput

    def _run(self, query: str, document_filter: Optional[str] = None, top_k: int = 4) -> str:
        engine = get_kb_engine()
        results = engine.search(query=query, top_k=top_k, document_filter=document_filter)

        if not results:
            catalog = engine.get_catalog()
            docs = ", ".join(f"`{d}`" for d in catalog.get("catalog", {}).keys())
            return (
                f"No relevant excerpts found for query: '{query}'.\n"
                f"Available knowledge documents: {docs}.\n"
                "Try rephrasing or use 'KB Catalog Overview' to view available headings."
            )

        output = [f"### [Advanced KB Search Results: '{query}']\n"]
        for idx, r in enumerate(results, 1):
            output.append(
                f"**Match {idx}** | **Source**: `{r['document']}` | **Section**: *{r['heading']}* | **Relevance**: {int(r['relevance'] * 100)}%\n"
                f"{r['content']}\n"
            )

        return "\n---\n".join(output)


class KBSectionExtractorInput(BaseModel):
    document_name: str = Field(..., description="The name of the document to inspect (e.g. 'company_handbook.md').")
    heading: str = Field(..., description="The section title, heading, or topic to extract (e.g. 'Paid Time Off' or 'Work Schedule').")


class KBSectionExtractorTool(BaseTool):
    name: str = "KB Section Deep Extractor"
    description: str = (
        "Extracts an entire designated section or topic from a knowledge document by heading name. "
        "Use when you know the section name or need comprehensive details from a specific document chapter."
    )
    args_schema: Type[BaseModel] = KBSectionExtractorInput

    def _run(self, document_name: str, heading: str) -> str:
        engine = get_kb_engine()
        section_text = engine.extract_section(document_name, heading)
        if section_text:
            return section_text
        return f"Section '{heading}' not found in document '{document_name}'. Use 'Advanced KB Search Engine' to locate topics."


class KBStructuredQueryInput(BaseModel):
    query: str = Field(..., description="Query terms or JSON key to search across structured configuration and capability documents.")
    top_k: int = Field(default=5, description="Number of structured entries to return.")


class KBStructuredQueryTool(BaseTool):
    name: str = "KB Structured JSON Query"
    description: str = (
        "Queries structured JSON knowledge documents (e.g. AI capabilities, system architecture, provider configs). "
        "Returns dot-notation key paths, configuration values, and array items."
    )
    args_schema: Type[BaseModel] = KBStructuredQueryInput

    def _run(self, query: str, top_k: int = 5) -> str:
        engine = get_kb_engine()
        matches = engine.query_structured_json(query, top_k=top_k)
        if not matches:
            return f"No matching structured JSON entries found for '{query}'."

        output = [f"### [Structured JSON Query Results: '{query}']\n"]
        for m in matches:
            output.append(f"- **{m['document']}** (`{m['heading']}`):\n  {m['content']}")
        return "\n\n".join(output)


class KBCatalogOverviewInput(BaseModel):
    filter_type: str = Field(default="all", description="Filter catalog by 'all', 'markdown', or 'json'.")


class KBCatalogOverviewTool(BaseTool):
    name: str = "KB Catalog Overview"
    description: str = (
        "Returns the complete table of contents and index of all documents and sections available in the knowledge base. "
        "Use this tool to explore what topics, policies, and manuals exist before searching."
    )
    args_schema: Type[BaseModel] = KBCatalogOverviewInput

    def _run(self, filter_type: str = "all") -> str:
        engine = get_kb_engine()
        data = engine.get_catalog()
        catalog = data.get("catalog", {})

        output = [
            f"### [Knowledge Base Catalog Overview] ({data['total_documents']} Documents, {data['total_chunks']} Sections)\n"
        ]

        for doc, headings in catalog.items():
            if filter_type == "markdown" and not doc.endswith(".md"):
                continue
            if filter_type == "json" and not doc.endswith(".json"):
                continue

            output.append(f"#### 📄 `{doc}`")
            for h in headings[:8]:
                output.append(f"  - {h}")
            if len(headings) > 8:
                output.append(f"  - *...and {len(headings) - 8} more sections*")
            output.append("")

        return "\n".join(output)
