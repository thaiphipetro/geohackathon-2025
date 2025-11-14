"""
RAG-Based QA System for Well Completion Reports

Production-ready RAG system with:
- TOC-aware ChromaDB retrieval
- Ollama Llama 3.2 3B integration
- Custom prompts for well completion reports
- Source citation and metadata tracking

Sub-Challenge 1: RAG-based summarization (50% of grade)
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM


@dataclass
class QAResult:
    """Result from QA system with sources"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class WellReportQASystem:
    """
    RAG-based QA system for well completion reports

    Features:
    - TOC-aware retrieval with section type filtering
    - Ollama integration with streaming support
    - Custom prompts for oil & gas domain
    - Source citation with metadata
    """

    def __init__(
        self,
        chroma_dir: str = "./chroma_db_toc_aware",
        collection_name: str = "well_reports_toc_aware",
        embedding_model: str = "nomic-ai/nomic-embed-text-v1.5",
        llm_model: str = "llama3.2:3b",
        temperature: float = 0.1,
        top_k: int = 5,
        verbose: bool = False
    ):
        """
        Initialize RAG QA system

        Args:
            chroma_dir: Path to ChromaDB directory
            collection_name: ChromaDB collection name
            embedding_model: HuggingFace embedding model
            llm_model: Ollama model name
            temperature: LLM temperature (0.1 for factual answers)
            top_k: Number of documents to retrieve
            verbose: Enable verbose logging
        """
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.llm_model = llm_model
        self.temperature = temperature
        self.top_k = top_k
        self.verbose = verbose

        # Initialize components
        self._init_embeddings()
        self._init_vectorstore()
        self._init_llm()

        if self.verbose:
            print(f"[OK] RAG QA System initialized")
            print(f"  Embedding model: {embedding_model}")
            print(f"  LLM model: {llm_model}")
            print(f"  Temperature: {temperature}")
            print(f"  Top-k retrieval: {top_k}")

    def _init_embeddings(self):
        """Initialize embedding model"""
        if self.verbose:
            print(f"[LOAD] Loading embeddings: {self.embedding_model_name}...")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={'device': 'cpu', 'trust_remote_code': True},
            encode_kwargs={'normalize_embeddings': True}
        )

        if self.verbose:
            print("[OK] Embeddings loaded")

    def _init_vectorstore(self):
        """Initialize ChromaDB vectorstore"""
        if self.verbose:
            print(f"[LOAD] Loading ChromaDB: {self.chroma_dir}...")

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.chroma_dir
        )

        # Get collection stats
        collection = self.vectorstore._collection
        count = collection.count()

        if self.verbose:
            print(f"[OK] ChromaDB loaded ({count} documents)")

    def _init_llm(self):
        """Initialize Ollama LLM"""
        if self.verbose:
            print(f"[LOAD] Initializing Ollama: {self.llm_model}...")

        self.llm = OllamaLLM(
            model=self.llm_model,
            temperature=self.temperature
        )

        if self.verbose:
            print(f"[OK] Ollama initialized")

    def _create_prompt(self, question: str, context_docs: List[Any]) -> str:
        """
        Create prompt with context for LLM

        Args:
            question: User question
            context_docs: Retrieved documents

        Returns:
            Formatted prompt string
        """
        # Format context from documents
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            well = doc.metadata.get('well_name', 'Unknown')
            section = doc.metadata.get('section_title', 'Unknown')
            page = doc.metadata.get('page', 'N/A')
            content = doc.page_content

            context_parts.append(
                f"[Source {i}] Well: {well}, Section: {section}, Page: {page}\n{content}"
            )

        context = "\n\n".join(context_parts)

        # Custom prompt for well completion reports
        prompt = f"""You are an expert in oil and gas well completion engineering. Use the following context from well completion reports to answer the question.

Context:
{context}

Question: {question}

Instructions:
1. Provide a clear, factual answer based ONLY on the context provided
2. If the context doesn't contain the answer, say "I cannot find this information in the provided documents"
3. Cite specific sections or wells when possible (e.g., "According to Well 5 EOWR, Section 3.2...")
4. Use technical terminology appropriate for petroleum engineering
5. Be concise but complete

Answer:"""

        return prompt

    def query(
        self,
        question: str,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> QAResult:
        """
        Query the RAG system

        Args:
            question: User question
            filter_metadata: Optional metadata filters (e.g., {"well_name": "well_5"})

        Returns:
            QAResult with answer and sources
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"QUERY: {question}")
            print(f"{'='*80}\n")

        # Retrieve relevant documents
        search_kwargs = {"k": self.top_k}
        if filter_metadata:
            search_kwargs["filter"] = filter_metadata
            if self.verbose:
                print(f"[FILTER] {filter_metadata}")

        retrieved_docs = self.vectorstore.similarity_search(
            question,
            **search_kwargs
        )

        if self.verbose:
            print(f"[RETRIEVAL] Found {len(retrieved_docs)} documents")

        # Create prompt with context
        prompt = self._create_prompt(question, retrieved_docs)

        # Get answer from LLM
        if self.verbose:
            print(f"[LLM] Generating answer...\n")

        answer = self.llm.invoke(prompt)

        if self.verbose:
            print(f"\n[OK] Answer generated")

        # Extract sources with metadata
        sources = []
        for doc in retrieved_docs:
            source_info = {
                'content': doc.page_content,
                'well_name': doc.metadata.get('well_name', 'N/A'),
                'source_type': doc.metadata.get('source_type', 'N/A'),
                'section_title': doc.metadata.get('section_title', 'N/A'),
                'section_type': doc.metadata.get('section_type', 'N/A'),
                'page': doc.metadata.get('page', 'N/A'),
                'pdf_file': doc.metadata.get('pdf_file', 'N/A')
            }
            sources.append(source_info)

        # Create result
        qa_result = QAResult(
            question=question,
            answer=answer,
            sources=sources,
            metadata={
                'num_sources': len(sources),
                'filter': filter_metadata,
                'model': self.llm_model,
                'temperature': self.temperature
            }
        )

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"ANSWER: {qa_result.answer}")
            print(f"\n[SOURCES] {len(sources)} documents retrieved")
            print(f"{'='*80}\n")

        return qa_result

    def query_with_section_filter(
        self,
        question: str,
        section_type: str,
        well_name: Optional[str] = None
    ) -> QAResult:
        """
        Query with section type filtering

        Args:
            question: User question
            section_type: Section type to filter (e.g., "casing", "geology")
            well_name: Optional well name filter

        Returns:
            QAResult with answer and sources
        """
        filter_dict = {"section_type": section_type}

        if well_name:
            filter_dict = {
                "$and": [
                    {"section_type": section_type},
                    {"well_name": well_name}
                ]
            }

        return self.query(question, filter_metadata=filter_dict)

    def list_available_wells(self) -> List[str]:
        """
        Get list of available wells in the database

        Returns:
            List of well names
        """
        collection = self.vectorstore._collection
        all_docs = collection.get(include=['metadatas'], limit=10000)

        wells = set()
        for meta in all_docs['metadatas']:
            well_name = meta.get('well_name')
            if well_name:
                wells.add(well_name)

        return sorted(list(wells))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Dictionary with statistics
        """
        collection = self.vectorstore._collection
        count = collection.count()

        all_docs = collection.get(include=['metadatas'], limit=10000)

        # Count by source type
        source_types = {}
        section_types = {}
        wells = set()

        for meta in all_docs['metadatas']:
            source_type = meta.get('source_type', 'unknown')
            section_type = meta.get('section_type', 'none')
            well_name = meta.get('well_name')

            source_types[source_type] = source_types.get(source_type, 0) + 1
            section_types[section_type] = section_types.get(section_type, 0) + 1
            if well_name:
                wells.add(well_name)

        return {
            'total_documents': count,
            'source_types': source_types,
            'section_types': section_types,
            'num_wells': len(wells),
            'wells': sorted(list(wells))
        }


def main():
    """Demo usage"""
    print("=" * 80)
    print("WELL REPORT RAG QA SYSTEM - DEMO")
    print("=" * 80)

    # Initialize system
    qa_system = WellReportQASystem(verbose=True)

    # Show statistics
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)
    stats = qa_system.get_statistics()
    print(f"\nTotal documents: {stats['total_documents']}")
    print(f"Number of wells: {stats['num_wells']}")
    print(f"Wells: {', '.join(stats['wells'])}")
    print(f"\nSource types:")
    for source_type, count in sorted(stats['source_types'].items()):
        print(f"  {source_type}: {count}")

    # Example queries
    queries = [
        "What is the total depth of Well 5?",
        "Describe the casing program for Well 3",
        "What is the geological formation in Well 7?"
    ]

    print("\n" + "=" * 80)
    print("EXAMPLE QUERIES")
    print("=" * 80)

    for i, query in enumerate(queries, 1):
        print(f"\n[QUERY {i}] {query}")
        result = qa_system.query(query)

        print(f"\n[ANSWER]")
        print(result.answer)

        print(f"\n[SOURCES] {result.metadata['num_sources']} documents:")
        for j, source in enumerate(result.sources[:3], 1):
            print(f"\n  Source {j}:")
            print(f"    Well: {source['well_name']}")
            print(f"    Section: {source['section_title']} ({source['section_type']})")
            print(f"    Page: {source['page']}")
            print(f"    Content: {source['content'][:100]}...")

        print("\n" + "-" * 80)


if __name__ == '__main__':
    main()
