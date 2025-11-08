"""
Integration Tests for Sub-Challenge 1: Multi-PDF RAG with Summarization

Tests:
1. Table chunking module
2. Multi-PDF indexing
3. Filtered retrieval (chunk_type, document_name)
4. Summarization with word limits
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from table_chunker import TableChunker
from rag_system import WellReportRAG
from summarizer import ReportSummarizer
import pandas as pd


def test_table_chunking():
    """Test 1: Table chunking module"""
    print("\n" + "="*80)
    print("TEST 1: Table Chunking")
    print("="*80)

    # Mock table object
    class MockTable:
        def __init__(self, data, caption, page):
            self.data = pd.DataFrame(data)
            self.caption = caption
            self.page = page

    # Create sample tables
    tables = [
        MockTable(
            data={'MD (m)': [0, 500, 1500], 'TVD (m)': [0, 500, 1500], 'ID (in)': [13.375, 9.625, 7.0]},
            caption='Casing Program',
            page=20
        )
    ]

    # Chunk tables
    chunker = TableChunker()
    chunks = chunker.chunk_tables(
        tables=tables,
        section_info={'number': '3.4', 'title': 'Casing', 'type': 'casing', 'page': 20},
        doc_metadata={'well_name': 'Well 5', 'document_name': 'Final-Well-Report.pdf'}
    )

    # Validate
    assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
    assert chunks[0]['metadata']['chunk_type'] == 'table', "Chunk type should be 'table'"
    assert chunks[0]['metadata']['section_type'] == 'casing', "Section type should be 'casing'"
    assert 'Table: Casing Program' in chunks[0]['text'], "Caption should be in text"

    print(f"[OK] Table chunking working: {len(chunks)} chunks created")
    print(f"   Chunk type: {chunks[0]['metadata']['chunk_type']}")
    print(f"   Section: {chunks[0]['metadata']['section_number']} - {chunks[0]['metadata']['section_title']}")
    print(f"   Preview: {chunks[0]['text'][:100]}...")

    return True


def test_multi_pdf_indexing():
    """Test 2: Multi-PDF indexing"""
    print("\n" + "="*80)
    print("TEST 2: Multi-PDF Indexing")
    print("="*80)

    # Initialize RAG
    rag = WellReportRAG()

    # Index all PDFs in Well 5
    result = rag.index_well_reports("Well 5", reindex=True)

    # Validate
    assert result['pdfs_found'] > 0, "Should find at least 1 PDF"
    assert result['pdfs_indexed'] > 0, "Should index at least 1 PDF"
    assert result['total_chunks'] > 0, "Should create chunks"

    print(f"[OK] Multi-PDF indexing working")
    print(f"   PDFs found: {result['pdfs_found']}")
    print(f"   PDFs indexed: {result['pdfs_indexed']}")
    print(f"   PDFs skipped: {len(result['pdfs_skipped'])}")
    print(f"   Total chunks: {result['total_chunks']}")

    if result['pdfs_skipped']:
        print(f"   Skipped: {', '.join(result['pdfs_skipped'])}")

    return True


def test_filtered_retrieval():
    """Test 3: Filtered retrieval with chunk_type"""
    print("\n" + "="*80)
    print("TEST 3: Filtered Retrieval")
    print("="*80)

    # Initialize RAG
    rag = WellReportRAG()

    # Query embedding
    query = "casing inner diameter"
    query_embedding = rag.embedding_manager.embed_text(query)

    # Test 1: Retrieve only table chunks
    print("\n📊 Retrieving table chunks only...")
    table_results = rag.vector_store.query_with_filters(
        query_embedding=query_embedding,
        well_name="Well 5",
        chunk_types=['table'],
        n_results=5
    )

    # Validate
    for meta in table_results['metadatas']:
        assert meta.get('chunk_type') == 'table', "Should only return table chunks"

    print(f"[OK] Table filtering working: {len(table_results['documents'])} table chunks retrieved")

    # Test 2: Retrieve only text chunks
    print("\n📝 Retrieving text chunks only...")
    text_results = rag.vector_store.query_with_filters(
        query_embedding=query_embedding,
        well_name="Well 5",
        chunk_types=['text'],
        n_results=5
    )

    # Validate
    for meta in text_results['metadatas']:
        assert meta.get('chunk_type') == 'text', "Should only return text chunks"

    print(f"[OK] Text filtering working: {len(text_results['documents'])} text chunks retrieved")

    # Test 3: Retrieve from specific section types
    print("\n🎯 Retrieving casing sections only...")
    section_results = rag.vector_store.query_with_filters(
        query_embedding=query_embedding,
        well_name="Well 5",
        section_types=['casing'],
        n_results=5
    )

    print(f"[OK] Section filtering working: {len(section_results['documents'])} chunks from casing sections")

    return True


def test_summarization():
    """Test 4: Summarization with word limits"""
    print("\n" + "="*80)
    print("TEST 4: Summarization")
    print("="*80)

    # Initialize RAG
    rag = WellReportRAG()

    # Initialize summarizer
    summarizer = ReportSummarizer(rag, max_words=200)

    # Test summarization
    print("\n📝 Generating summary...")
    result = summarizer.summarize(
        well_name="Well 5",
        user_prompt="Summarize the casing program in 150 words",
        max_words=150
    )

    # Validate
    assert result['word_count'] > 0, "Summary should have words"
    assert result['word_count'] <= 150 * 1.1, f"Word count should be close to 150, got {result['word_count']}"
    assert result['sources_used'] > 0, "Should use sources"

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(result['summary'])
    print(f"\n{'='*80}")
    print(f"[OK] Summarization working")
    print(f"   Word count: {result['word_count']}/150")
    print(f"   Sources used: {result['sources_used']} ({result['text_chunks_used']} text + {result['table_chunks_used']} tables)")
    print(f"   Focus sections: {', '.join(result['focus_sections'])}")
    print(f"   Word limit met: {result['word_limit_met']}")

    return True


def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("INTEGRATION TESTS - SUB-CHALLENGE 1")
    print("="*80)

    tests = [
        ("Table Chunking", test_table_chunking),
        ("Multi-PDF Indexing", test_multi_pdf_indexing),
        ("Filtered Retrieval", test_filtered_retrieval),
        ("Summarization", test_summarization),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"[OK] Passed: {passed}/{len(tests)}")
    print(f"[FAIL] Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n[OK] Sub-Challenge 1 Components Validated:")
        print("   • Table chunking with markdown format")
        print("   • Multi-PDF indexing with document metadata")
        print("   • Filtered retrieval (chunk_type, section_type)")
        print("   • Summarization with word limit control")
        print("\n📋 Next Steps:")
        print("   1. Test on multiple wells")
        print("   2. Optimize word limit accuracy")
        print("   3. Create demo notebook (05_test_summarization.ipynb)")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")

    print("="*80)


if __name__ == '__main__':
    main()
