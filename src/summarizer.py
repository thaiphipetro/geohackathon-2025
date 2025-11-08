"""
Report Summarizer - TOC-guided summarization with word limit control

Purpose:
    Generate accurate, complete summaries of well reports with specified word limits

Key Features:
    - User prompt-driven focus areas
    - Context-aware table prioritization
    - Word budget allocation (70% text, 30% tables)
    - Iterative refinement for word limit control
"""

import os
from typing import List, Dict, Optional
import ollama


class ReportSummarizer:
    """
    Generate summaries from well reports with word limit control

    Architecture:
        1. Parse user prompt → identify focus sections
        2. Retrieve text chunks (main content)
        3. Retrieve table chunks (structured data)
        4. Prioritize tables based on query context
        5. Allocate word budget (70% text, 30% tables)
        6. Generate summary with Ollama
        7. Iterative refinement if over word limit

    Example:
        summarizer = ReportSummarizer(rag_system, max_words=500)
        result = summarizer.summarize(
            well_name="Well 5",
            user_prompt="Summarize the casing program",
            max_words=200
        )
    """

    def __init__(self, rag_system, max_words: int = 500):
        """
        Initialize summarizer

        Args:
            rag_system: WellReportRAG instance
            max_words: Default maximum words for summaries
        """
        self.rag = rag_system
        self.max_words = max_words

    def summarize(self,
                  well_name: str,
                  user_prompt: str,
                  max_words: Optional[int] = None) -> Dict:
        """
        Generate summary based on user prompt

        Args:
            well_name: Well identifier
            user_prompt: User's request (e.g., "Summarize the casing program in 200 words")
            max_words: Maximum words (overrides default)

        Returns:
            {
                'summary': str,
                'word_count': int,
                'sources_used': int,
                'text_chunks_used': int,
                'table_chunks_used': int,
                'focus_sections': List[str],
                'word_limit_met': bool
            }
        """
        max_words = max_words or self.max_words

        print(f"\n{'='*80}")
        print(f"SUMMARIZING: {user_prompt}")
        print(f"Target: {max_words} words max")
        print(f"{'='*80}")

        # Step 1: Parse user prompt for focus areas
        print(f"\n[TARGET] Identifying focus areas...")
        focus_sections = self._parse_user_prompt(user_prompt)
        print(f"[OK] Focus sections: {', '.join(focus_sections)}")

        # Step 2: Retrieve text chunks
        print(f"\n Retrieving text chunks...")
        text_chunks = self._retrieve_text_chunks(well_name, focus_sections, n_results=10)
        print(f"[OK] Retrieved {len(text_chunks)} text chunks")

        # Step 3: Retrieve table chunks
        print(f"\n[STATS] Retrieving table chunks...")
        table_chunks = self._retrieve_table_chunks(well_name, focus_sections, n_results=5)
        print(f"[OK] Retrieved {len(table_chunks)} table chunks")

        # Step 4: Prioritize tables based on context
        print(f"\n  Prioritizing tables...")
        prioritized_tables = self._prioritize_tables(table_chunks, user_prompt)
        print(f"[OK] Prioritized {len(prioritized_tables)} tables")

        # Step 5: Allocate word budget
        text_budget = int(max_words * 0.7)
        table_budget = int(max_words * 0.3)
        print(f"\n Word budget: {text_budget} (text) + {table_budget} (tables) = {max_words} total")

        # Step 6: Generate summary
        print(f"\n🤖 Generating summary...")
        summary = self._generate_summary(
            text_chunks=text_chunks,
            table_chunks=prioritized_tables,
            user_prompt=user_prompt,
            text_budget=text_budget,
            table_budget=table_budget
        )

        # Count words
        word_count = len(summary.split())
        print(f"[OK] Summary generated: {word_count} words")

        # Step 7: Refine if over limit
        if word_count > max_words:
            print(f"\n[INIT] Refining summary ({word_count} > {max_words})...")
            summary = self._compress_summary(summary, max_words)
            word_count = len(summary.split())
            print(f"[OK] Compressed to {word_count} words")

        word_limit_met = word_count <= max_words

        print(f"\n{'='*80}")
        print(f"[OK] SUMMARIZATION COMPLETE")
        print(f"   Word count: {word_count}/{max_words}")
        print(f"   Status: {'[OK] Within limit' if word_limit_met else '[WARN] Over limit'}")
        print(f"{'='*80}")

        return {
            'summary': summary,
            'word_count': word_count,
            'sources_used': len(text_chunks) + len(prioritized_tables),
            'text_chunks_used': len(text_chunks),
            'table_chunks_used': len(prioritized_tables),
            'focus_sections': focus_sections,
            'word_limit_met': word_limit_met
        }

    def _parse_user_prompt(self, prompt: str) -> List[str]:
        """
        Extract focus areas from user prompt

        Uses the RAG system's query intent mapper

        Args:
            prompt: User's request

        Returns:
            List of section types
        """
        return self.rag.intent_mapper.get_section_types(prompt)

    def _retrieve_text_chunks(self,
                             well_name: str,
                             section_types: List[str],
                             n_results: int = 10) -> List[Dict]:
        """
        Retrieve text chunks for summarization

        Args:
            well_name: Well identifier
            section_types: Section types to focus on
            n_results: Number of chunks to retrieve

        Returns:
            List of chunk dictionaries
        """
        # Generate embedding for generic retrieval
        # Use a broad query to get representative chunks
        generic_query = f"Provide comprehensive information about {', '.join(section_types)}"
        query_embedding = self.rag.embedding_manager.embed_text(generic_query)

        # Retrieve with filters
        results = self.rag.vector_store.query_with_filters(
            query_embedding=query_embedding,
            well_name=well_name,
            section_types=section_types if section_types else None,
            chunk_types=['text'],
            n_results=n_results
        )

        # Build chunk list
        chunks = []
        for doc, meta in zip(results['documents'], results['metadatas']):
            chunks.append({
                'text': doc,
                'metadata': meta
            })

        return chunks

    def _retrieve_table_chunks(self,
                              well_name: str,
                              section_types: List[str],
                              n_results: int = 5) -> List[Dict]:
        """
        Retrieve table chunks for summarization

        Args:
            well_name: Well identifier
            section_types: Section types to focus on
            n_results: Number of table chunks to retrieve

        Returns:
            List of table chunk dictionaries
        """
        # Generic query for table retrieval
        generic_query = f"Tables related to {', '.join(section_types)}"
        query_embedding = self.rag.embedding_manager.embed_text(generic_query)

        # Retrieve with filters
        results = self.rag.vector_store.query_with_filters(
            query_embedding=query_embedding,
            well_name=well_name,
            section_types=section_types if section_types else None,
            chunk_types=['table'],
            n_results=n_results
        )

        # Build chunk list
        chunks = []
        for doc, meta in zip(results['documents'], results['metadatas']):
            chunks.append({
                'text': doc,
                'metadata': meta
            })

        return chunks

    def _prioritize_tables(self, table_chunks: List[Dict], user_prompt: str) -> List[Dict]:
        """
        Rank tables by relevance to user prompt

        Context-aware prioritization:
        - If prompt mentions "lithology" → prioritize stratigraphy tables
        - If prompt mentions "casing" → prioritize casing program tables
        - If prompt mentions "depth" → prioritize trajectory tables

        Args:
            table_chunks: List of table chunks
            user_prompt: User's request

        Returns:
            Sorted list of table chunks (most relevant first)
        """
        # Define keyword → section type mapping
        priorities = {
            'lithology': ['stratigraphy', 'geology', 'formation'],
            'strat': ['stratigraphy', 'geology'],
            'casing': ['casing', 'completion', 'tubular'],
            'tubing': ['casing', 'completion', 'tubular'],
            'depth': ['trajectory', 'depth', 'borehole'],
            'trajectory': ['trajectory', 'depth'],
            'pressure': ['pressure', 'test', 'formation'],
            'production': ['production', 'test', 'flow'],
        }

        # Score each table
        scored = []
        for chunk in table_chunks:
            score = 0
            section_type = chunk['metadata'].get('section_type', '').lower()

            # Check each keyword in prompt
            for keyword, relevant_types in priorities.items():
                if keyword in user_prompt.lower():
                    # Boost score if section type matches
                    if any(rt in section_type for rt in relevant_types):
                        score += 1

            # Default score if no matches (to preserve order)
            scored.append((score, chunk))

        # Sort by score (highest first)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return sorted chunks
        return [chunk for score, chunk in scored]

    def _generate_summary(self,
                         text_chunks: List[Dict],
                         table_chunks: List[Dict],
                         user_prompt: str,
                         text_budget: int,
                         table_budget: int) -> str:
        """
        Generate summary using Ollama LLM

        Args:
            text_chunks: Retrieved text chunks
            table_chunks: Prioritized table chunks
            user_prompt: User's request
            text_budget: Word budget for text content
            table_budget: Word budget for table content

        Returns:
            Summary string
        """
        # Build context from chunks
        context_parts = []

        # Add text chunks
        context_parts.append("## Text Content:")
        for i, chunk in enumerate(text_chunks[:5]):  # Top 5 text chunks
            context_parts.append(f"\n[Text {i+1}] {chunk['text'][:500]}...")  # Truncate for context

        # Add table chunks
        if table_chunks:
            context_parts.append("\n\n## Tables:")
            for i, chunk in enumerate(table_chunks[:3]):  # Top 3 tables
                context_parts.append(f"\n[Table {i+1}]\n{chunk['text'][:500]}...")  # Truncate

        context = "\n".join(context_parts)

        # Build prompt
        total_budget = text_budget + table_budget
        prompt = f"""You are a geothermal engineer writing well report summaries.

User Request: {user_prompt}

Available Information:
{context}

Task: Create a {total_budget}-word summary that:
1. Directly addresses the user's request
2. Includes key information from both text and tables
3. Is accurate, complete, and factual
4. Stays within the {total_budget}-word limit (CRITICAL!)
5. Uses clear, professional language

Summary ({total_budget} words max):"""

        # Generate with Ollama
        try:
            response = ollama.chat(
                model=self.rag.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a factual technical writer. Be concise and accurate.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={
                    'temperature': 0.1,  # Low temperature for factual summaries
                    'num_predict': total_budget * 2  # Allow some buffer
                }
            )

            return response['message']['content'].strip()

        except Exception as e:
            print(f"[ERROR] Ollama error: {e}")
            return f"Error generating summary: {e}"

    def _compress_summary(self, summary: str, max_words: int) -> str:
        """
        Iteratively compress summary to meet word limit

        Args:
            summary: Original summary
            max_words: Target word count

        Returns:
            Compressed summary
        """
        prompt = f"""Compress this summary to EXACTLY {max_words} words while preserving all key facts and numbers:

Original Summary:
{summary}

Compressed ({max_words} words, no more!):"""

        try:
            response = ollama.chat(
                model=self.rag.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.1,
                    'num_predict': max_words * 2
                }
            )

            return response['message']['content'].strip()

        except Exception as e:
            print(f"[ERROR] Compression error: {e}")
            # Fallback: truncate to word limit
            words = summary.split()
            return ' '.join(words[:max_words]) + '...'


def main():
    """Test the summarizer"""
    from rag_system import WellReportRAG

    print("="*80)
    print("REPORT SUMMARIZER - TEST")
    print("="*80)

    # Initialize RAG system
    rag = WellReportRAG()

    # Index Well 5
    print("\n[LOAD] Indexing Well 5...")
    rag.index_well_reports("Well 5", reindex=True)

    # Initialize summarizer
    summarizer = ReportSummarizer(rag, max_words=200)

    # Test summarization
    test_prompt = "Summarize the casing program in 150 words"

    result = summarizer.summarize(
        well_name="Well 5",
        user_prompt=test_prompt,
        max_words=150
    )

    # Display results
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(result['summary'])
    print(f"\n{'='*80}")
    print(f"Metrics:")
    print(f"  Word count: {result['word_count']}/150")
    print(f"  Sources used: {result['sources_used']} ({result['text_chunks_used']} text + {result['table_chunks_used']} tables)")
    print(f"  Focus sections: {', '.join(result['focus_sections'])}")
    print(f"  Word limit met: {result['word_limit_met']}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
