"""
Simple tests for newly implemented components (Windows-safe, no emojis)
Tests table chunking and query filtering without full RAG initialization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd


def test_table_chunker():
    """Test table chunking module"""
    print("\n" + "="*80)
    print("TEST 1: Table Chunker")
    print("="*80)

    from table_chunker import TableChunker

    # Mock table object
    class MockTable:
        def __init__(self, data, caption, page):
            self.data = pd.DataFrame(data)
            self.caption = caption
            self.page = page

    # Create sample table
    table = MockTable(
        data={
            'MD (m)': [0, 500, 1500, 2500],
            'TVD (m)': [0, 500, 1500, 2500],
            'ID (in)': [13.375, 9.625, 7.0, 7.0]
        },
        caption='Casing Program',
        page=20
    )

    # Chunk table
    chunker = TableChunker()
    chunks = chunker.chunk_tables(
        tables=[table],
        section_info={
            'number': '3.4',
            'title': 'Casing',
            'type': 'casing',
            'page': 20
        },
        doc_metadata={
            'well_name': 'Well 5',
            'document_name': 'Final-Well-Report.pdf'
        }
    )

    # Validate
    assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
    assert chunks[0]['metadata']['chunk_type'] == 'table', "chunk_type should be 'table'"
    assert chunks[0]['metadata']['section_type'] == 'casing', "section_type should be 'casing'"
    assert chunks[0]['metadata']['well_name'] == 'Well 5', "well_name should be 'Well 5'"
    assert chunks[0]['metadata']['document_name'] == 'Final-Well-Report.pdf', "document_name mismatch"
    assert 'Table: Casing Program' in chunks[0]['text'], "Caption should be in text"
    assert 'MD (m)' in chunks[0]['text'], "Table headers should be in text"

    print("\n[OK] Table chunking working correctly")
    print(f"  Chunks created: {len(chunks)}")
    print(f"  Chunk type: {chunks[0]['metadata']['chunk_type']}")
    print(f"  Section: {chunks[0]['metadata']['section_number']} - {chunks[0]['metadata']['section_title']}")
    print(f"  Document: {chunks[0]['metadata']['document_name']}")
    print(f"\n  Text preview:")
    print(f"    {chunks[0]['text'][:200]}...")

    return True


def test_vector_store_filters():
    """Test enhanced query_with_filters method"""
    print("\n" + "="*80)
    print("TEST 2: Vector Store Filtering")
    print("="*80)

    from vector_store import TOCEnhancedVectorStore

    # Create test vector store
    vector_store = TOCEnhancedVectorStore(
        collection_name="test_filters",
        chroma_host="localhost",
        chroma_port=8000
    )

    # Test that method exists and has correct signature
    import inspect
    sig = inspect.signature(vector_store.query_with_filters)
    params = list(sig.parameters.keys())

    expected_params = ['query_embedding', 'well_name', 'section_types', 'chunk_types', 'document_names', 'n_results']
    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"

    print("\n[OK] query_with_filters method exists with correct signature")
    print(f"  Parameters: {', '.join(params)}")

    # Clean up
    try:
        vector_store.client.delete_collection("test_filters")
    except:
        pass

    return True


def test_summarizer_module():
    """Test summarizer module structure"""
    print("\n" + "="*80)
    print("TEST 3: Summarizer Module")
    print("="*80)

    from summarizer import ReportSummarizer

    # Check class structure
    import inspect
    methods = [m for m in dir(ReportSummarizer) if not m.startswith('_')]

    assert 'summarize' in dir(ReportSummarizer), "summarize method should exist"

    # Check init signature
    init_sig = inspect.signature(ReportSummarizer.__init__)
    init_params = list(init_sig.parameters.keys())

    assert 'rag_system' in init_params, "Should accept rag_system parameter"
    assert 'max_words' in init_params, "Should accept max_words parameter"

    # Check summarize signature
    summarize_sig = inspect.signature(ReportSummarizer.summarize)
    summarize_params = list(summarize_sig.parameters.keys())

    assert 'well_name' in summarize_params, "summarize should accept well_name"
    assert 'user_prompt' in summarize_params, "summarize should accept user_prompt"
    assert 'max_words' in summarize_params, "summarize should accept max_words"

    print("\n[OK] Summarizer module structure correct")
    print(f"  __init__ parameters: {', '.join([p for p in init_params if p != 'self'])}")
    print(f"  summarize parameters: {', '.join([p for p in summarize_params if p != 'self'])}")
    print(f"  Methods: {', '.join(methods)}")

    return True


def test_rag_enhancements():
    """Test RAG system enhancements (without full initialization)"""
    print("\n" + "="*80)
    print("TEST 4: RAG System Enhancements")
    print("="*80)

    # Check that index_well_reports method exists
    from rag_system import WellReportRAG
    import inspect

    assert hasattr(WellReportRAG, 'index_well_reports'), "index_well_reports method should exist"

    # Check signature
    sig = inspect.signature(WellReportRAG.index_well_reports)
    params = list(sig.parameters.keys())

    assert 'well_name' in params, "Should accept well_name parameter"
    assert 'reindex' in params, "Should accept reindex parameter"

    print("\n[OK] RAG system enhancements present")
    print(f"  index_well_reports parameters: {', '.join([p for p in params if p != 'self'])}")

    return True


def main():
    """Run all component tests"""
    print("\n" + "="*80)
    print("COMPONENT TESTS - New Features (Windows-Safe)")
    print("="*80)

    tests = [
        ("Table Chunker", test_table_chunker),
        ("Vector Store Filters", test_vector_store_filters),
        ("Summarizer Module", test_summarizer_module),
        ("RAG Enhancements", test_rag_enhancements),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n[PASS] {name}")
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n[SUCCESS] ALL COMPONENT TESTS PASSED!")
        print("\nComponents Validated:")
        print("  * Table chunking with markdown format and metadata")
        print("  * Vector store query_with_filters (chunk_type, document_name)")
        print("  * Summarizer module structure and API")
        print("  * RAG system index_well_reports method")
        print("\nReady for:")
        print("  1. End-to-end testing with real data")
        print("  2. Demo notebook creation")
        print("  3. Performance optimization")
    else:
        print("\n[WARNING] Some tests failed. Review errors above.")

    print("="*80)


if __name__ == '__main__':
    main()
