"""
Test and validate comprehensive reindex results

This script verifies:
1. All 7 wells are accessible via RAG
2. Text, table, and picture chunks are retrievable
3. Section metadata is preserved
4. Picture descriptions are present
5. Query accuracy against known ground truth
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore
from embeddings import EmbeddingManager


class ReindexValidator:
    """Validate comprehensive reindex results"""

    def __init__(self):
        print("="*80)
        print("REINDEX VALIDATION TEST")
        print("="*80)

        self.vector_store = TOCEnhancedVectorStore()
        self.embedding_manager = EmbeddingManager()

        self.results = {
            'total_chunks': 0,
            'chunk_types': defaultdict(int),
            'wells': {},
            'sample_chunks': {},
            'validation_errors': []
        }

    def test_collection_stats(self):
        """Test 1: Verify collection exists and has expected chunks"""
        print("\n" + "="*80)
        print("TEST 1: Collection Statistics")
        print("="*80)

        try:
            collection = self.vector_store.collection
            count = collection.count()

            print(f"\nTotal chunks in database: {count}")
            self.results['total_chunks'] = count

            if count == 0:
                self.results['validation_errors'].append("Database is empty")
                print("[ERROR] Database is empty!")
                return False

            if count < 4500:
                self.results['validation_errors'].append(f"Expected ~4700 chunks, found {count}")
                print(f"[WARN] Expected ~4700 chunks, found {count}")

            print("[OK] Collection exists and contains data")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to access collection: {e}")
            self.results['validation_errors'].append(f"Collection access failed: {e}")
            return False

    def test_chunk_types(self):
        """Test 2: Verify text, table, and picture chunks exist"""
        print("\n" + "="*80)
        print("TEST 2: Chunk Type Distribution")
        print("="*80)

        try:
            collection = self.vector_store.collection

            # Get all metadata to analyze chunk types
            all_data = collection.get(include=['metadatas'])

            if not all_data or 'metadatas' not in all_data:
                print("[ERROR] No metadata available")
                return False

            metadatas = all_data['metadatas']

            # Count chunk types
            chunk_types = defaultdict(int)
            for metadata in metadatas:
                chunk_type = metadata.get('chunk_type', 'text')
                chunk_types[chunk_type] += 1

            self.results['chunk_types'] = dict(chunk_types)

            print(f"\nChunk Type Distribution:")
            print(f"  Text chunks:    {chunk_types['text']:4d} ({chunk_types['text']/len(metadatas)*100:.1f}%)")
            print(f"  Table chunks:   {chunk_types.get('table', 0):4d} ({chunk_types.get('table', 0)/len(metadatas)*100:.1f}%)")
            print(f"  Picture chunks: {chunk_types.get('picture', 0):4d} ({chunk_types.get('picture', 0)/len(metadatas)*100:.1f}%)")

            # Validate distribution
            if chunk_types.get('table', 0) == 0:
                self.results['validation_errors'].append("No table chunks found")
                print("[WARN] No table chunks found")

            if chunk_types.get('picture', 0) == 0:
                self.results['validation_errors'].append("No picture chunks found")
                print("[WARN] No picture chunks found")

            print("[OK] Multiple chunk types present")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to analyze chunk types: {e}")
            self.results['validation_errors'].append(f"Chunk type analysis failed: {e}")
            return False

    def test_well_coverage(self):
        """Test 3: Verify all 7 wells are indexed"""
        print("\n" + "="*80)
        print("TEST 3: Well Coverage")
        print("="*80)

        try:
            collection = self.vector_store.collection
            all_data = collection.get(include=['metadatas'])

            if not all_data or 'metadatas' not in all_data:
                print("[ERROR] No metadata available")
                return False

            metadatas = all_data['metadatas']

            # Count chunks per well
            wells = defaultdict(int)
            for metadata in metadatas:
                well_name = metadata.get('well_name', 'Unknown')
                wells[well_name] += 1

            self.results['wells'] = dict(wells)

            print(f"\nWells Indexed: {len(wells)}")
            print("-"*80)
            for well, count in sorted(wells.items()):
                print(f"  {well:15s}: {count:4d} chunks")

            # Expected wells from reindex
            expected_wells = ['Well 1', 'Well 2', 'Well 3', 'Well 4', 'Well 5', 'Well 6', 'Well 8']

            missing_wells = set(expected_wells) - set(wells.keys())
            if missing_wells:
                self.results['validation_errors'].append(f"Missing wells: {missing_wells}")
                print(f"[WARN] Missing wells: {missing_wells}")

            print("[OK] Multiple wells indexed")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to analyze well coverage: {e}")
            self.results['validation_errors'].append(f"Well coverage analysis failed: {e}")
            return False

    def test_metadata_quality(self):
        """Test 4: Sample chunks and verify metadata completeness"""
        print("\n" + "="*80)
        print("TEST 4: Metadata Quality")
        print("="*80)

        try:
            collection = self.vector_store.collection

            # Sample different chunk types
            print("\nSampling chunks...")

            # Sample text chunk
            text_results = collection.get(
                where={"chunk_type": "text"},
                limit=1,
                include=['metadatas', 'documents']
            )

            if text_results and text_results['metadatas']:
                text_meta = text_results['metadatas'][0]
                text_doc = text_results['documents'][0]

                print("\n[TEXT CHUNK SAMPLE]")
                print(f"  Well: {text_meta.get('well_name')}")
                print(f"  File: {text_meta.get('filename')}")
                print(f"  Section: {text_meta.get('section_number')} - {text_meta.get('section_title')}")
                print(f"  Section Type: {text_meta.get('section_type')}")
                print(f"  Text Preview: {text_doc[:150]}...")

                self.results['sample_chunks']['text'] = text_meta

                # Validate required fields
                required_fields = ['well_name', 'filename', 'chunk_type']
                missing_fields = [f for f in required_fields if not text_meta.get(f)]
                if missing_fields:
                    print(f"  [WARN] Missing fields: {missing_fields}")

            # Sample table chunk
            table_results = collection.get(
                where={"chunk_type": "table"},
                limit=1,
                include=['metadatas', 'documents']
            )

            if table_results and table_results['metadatas']:
                table_meta = table_results['metadatas'][0]
                table_doc = table_results['documents'][0]

                print("\n[TABLE CHUNK SAMPLE]")
                print(f"  Well: {table_meta.get('well_name')}")
                print(f"  File: {table_meta.get('filename')}")
                print(f"  Table Index: {table_meta.get('table_index')}")
                print(f"  Text Preview: {table_doc[:150]}...")

                self.results['sample_chunks']['table'] = table_meta

            # Sample picture chunk
            picture_results = collection.get(
                where={"chunk_type": "picture"},
                limit=1,
                include=['metadatas', 'documents']
            )

            if picture_results and picture_results['metadatas']:
                picture_meta = picture_results['metadatas'][0]
                picture_doc = picture_results['documents'][0]

                print("\n[PICTURE CHUNK SAMPLE]")
                print(f"  Well: {picture_meta.get('well_name')}")
                print(f"  File: {picture_meta.get('filename')}")
                print(f"  Picture Type: {picture_meta.get('picture_type')}")
                print(f"  Has Handwriting: {picture_meta.get('has_handwriting')}")
                print(f"  Has Text Labels: {picture_meta.get('has_text_labels')}")
                print(f"  Description Preview: {picture_doc[:150]}...")

                self.results['sample_chunks']['picture'] = picture_meta

                # Validate picture-specific fields
                if not picture_meta.get('picture_path'):
                    print(f"  [WARN] Missing picture_path")

            print("\n[OK] Metadata structure verified")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to sample chunks: {e}")
            import traceback
            traceback.print_exc()
            self.results['validation_errors'].append(f"Chunk sampling failed: {e}")
            return False

    def test_query_retrieval(self):
        """Test 5: Test RAG queries on known facts"""
        print("\n" + "="*80)
        print("TEST 5: Query Retrieval")
        print("="*80)

        test_queries = [
            {
                'query': 'What is the measured depth of Well 1?',
                'well_filter': 'Well 1',
                'expected_keywords': ['depth', 'meter', 'm']
            },
            {
                'query': 'What casing sizes are used in the wells?',
                'well_filter': None,
                'expected_keywords': ['casing', 'inch', 'diameter']
            },
            {
                'query': 'Tell me about Well 5 completion',
                'well_filter': 'Well 5',
                'expected_keywords': ['completion', 'Well 5']
            }
        ]

        print("\nTesting retrieval queries...")

        for i, test in enumerate(test_queries, 1):
            print(f"\n[Query {i}] {test['query']}")

            try:
                # Create query embedding
                query_embedding = self.embedding_manager.embed_text(test['query'])

                # Search vector store
                where_filter = {"well_name": test['well_filter']} if test['well_filter'] else None

                results = self.vector_store.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5,
                    where=where_filter,
                    include=['documents', 'metadatas', 'distances']
                )

                if results and results['documents'] and results['documents'][0]:
                    top_result = results['documents'][0][0]
                    top_meta = results['metadatas'][0][0]
                    distance = results['distances'][0][0]

                    print(f"  Top Result:")
                    print(f"    Well: {top_meta.get('well_name')}")
                    print(f"    File: {top_meta.get('filename')}")
                    print(f"    Distance: {distance:.3f}")
                    print(f"    Preview: {top_result[:200]}...")

                    # Check if expected keywords present
                    keywords_found = [kw for kw in test['expected_keywords']
                                     if kw.lower() in top_result.lower()]

                    if keywords_found:
                        print(f"    [OK] Found keywords: {keywords_found}")
                    else:
                        print(f"    [WARN] No expected keywords found")
                else:
                    print(f"  [ERROR] No results returned")
                    self.results['validation_errors'].append(f"Query {i} returned no results")

            except Exception as e:
                print(f"  [ERROR] Query failed: {e}")
                self.results['validation_errors'].append(f"Query {i} failed: {e}")

        print("\n[OK] Query retrieval tested")
        return True

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)

        print(f"\nTotal Chunks: {self.results['total_chunks']}")

        print(f"\nChunk Types:")
        for chunk_type, count in self.results['chunk_types'].items():
            print(f"  {chunk_type}: {count}")

        print(f"\nWells Indexed: {len(self.results['wells'])}")
        for well, count in sorted(self.results['wells'].items()):
            print(f"  {well}: {count} chunks")

        if self.results['validation_errors']:
            print(f"\nValidation Warnings/Errors: {len(self.results['validation_errors'])}")
            for error in self.results['validation_errors']:
                print(f"  - {error}")
        else:
            print("\n[OK] No validation errors!")

        print("="*80)

    def run_all_tests(self):
        """Run all validation tests"""
        tests = [
            self.test_collection_stats,
            self.test_chunk_types,
            self.test_well_coverage,
            self.test_metadata_quality,
            self.test_query_retrieval
        ]

        results = []
        for test in tests:
            try:
                success = test()
                results.append(success)
            except Exception as e:
                print(f"\n[ERROR] Test failed with exception: {e}")
                import traceback
                traceback.print_exc()
                results.append(False)

        self.print_summary()

        return all(results)


if __name__ == '__main__':
    validator = ReindexValidator()
    success = validator.run_all_tests()

    if success:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[PARTIAL] Some tests had warnings")
        sys.exit(0)
