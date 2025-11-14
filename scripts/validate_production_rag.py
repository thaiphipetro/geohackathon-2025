"""
Production RAG QA System Validation Script

This script performs comprehensive validation of the RAG QA system:
1. Database accessibility and statistics
2. Sample query testing with quality metrics
3. Performance benchmarking
4. Error handling validation
5. System integration testing

Usage:
    python scripts/validate_production_rag.py
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "PASS" if passed else "FAIL"
    symbol = "[+]" if passed else "[X]"
    print(f"{symbol} {test_name}: {status}")
    if details:
        print(f"    {details}")

class ProductionValidator:
    """Comprehensive validation for production RAG QA system."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "metrics": {},
            "errors": []
        }
        self.qa_system = None

    def validate_dependencies(self) -> bool:
        """Validate all required dependencies are installed."""
        print_section("1. DEPENDENCY VALIDATION")

        required_modules = [
            ("langchain_chroma", "Chroma"),
            ("langchain_huggingface", "HuggingFaceEmbeddings"),
            ("langchain_ollama", "OllamaLLM"),
            ("chromadb", "ChromaDB client")
        ]

        all_passed = True
        for module_name, description in required_modules:
            try:
                __import__(module_name)
                print_result(f"Import {description}", True)
            except ImportError as e:
                print_result(f"Import {description}", False, str(e))
                all_passed = False
                self.results["errors"].append(f"Missing dependency: {module_name}")

        return all_passed

    def validate_database(self) -> bool:
        """Validate ChromaDB database exists and is accessible."""
        print_section("2. DATABASE VALIDATION")

        chroma_dir = Path("chroma_db_toc_aware")

        # Check directory exists
        if not chroma_dir.exists():
            print_result("Database directory exists", False, str(chroma_dir))
            self.results["errors"].append(f"Database directory not found: {chroma_dir}")
            return False

        print_result("Database directory exists", True, str(chroma_dir))

        # Check sqlite file
        sqlite_file = chroma_dir / "chroma.sqlite3"
        if not sqlite_file.exists():
            print_result("SQLite database file exists", False)
            return False

        file_size_mb = sqlite_file.stat().st_size / (1024 * 1024)
        print_result("SQLite database file exists", True, f"{file_size_mb:.2f} MB")
        self.results["metrics"]["database_size_mb"] = file_size_mb

        # Try to load database
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings

            embeddings = HuggingFaceEmbeddings(
                model_name="nomic-ai/nomic-embed-text-v1.5",
                model_kwargs={"trust_remote_code": True}
            )

            vectorstore = Chroma(
                collection_name="well_reports_toc_aware",
                embedding_function=embeddings,
                persist_directory=str(chroma_dir)
            )

            # Get collection count
            collection = vectorstore._collection
            doc_count = collection.count()

            print_result("Database loads successfully", True, f"{doc_count} documents")
            self.results["metrics"]["total_documents"] = doc_count

            # Get sample metadata
            if doc_count > 0:
                sample_docs = collection.get(limit=10, include=["metadatas"])
                wells = set()
                section_types = set()

                for metadata in sample_docs["metadatas"]:
                    if "well_name" in metadata:
                        wells.add(metadata["well_name"])
                    if "section_type" in metadata:
                        section_types.add(metadata["section_type"])

                print_result("Metadata available", True,
                           f"{len(wells)} wells, {len(section_types)} section types")
                self.results["metrics"]["unique_wells"] = len(wells)
                self.results["metrics"]["unique_section_types"] = len(section_types)

            return True

        except Exception as e:
            print_result("Database loads successfully", False, str(e))
            self.results["errors"].append(f"Database load error: {str(e)}")
            return False

    def validate_ollama(self) -> bool:
        """Validate Ollama is running and model is available."""
        print_section("3. OLLAMA VALIDATION")

        try:
            from langchain_ollama import OllamaLLM

            llm = OllamaLLM(model="llama3.2:3b", temperature=0.1)

            # Test connection with simple query
            start = time.time()
            response = llm.invoke("Say 'test' and nothing else.")
            latency = time.time() - start

            print_result("Ollama connection", True, f"Latency: {latency:.2f}s")
            print_result("Model llama3.2:3b available", True)
            self.results["metrics"]["ollama_test_latency"] = latency

            return True

        except Exception as e:
            print_result("Ollama connection", False, str(e))
            self.results["errors"].append(f"Ollama error: {str(e)}")
            return False

    def validate_rag_system_init(self) -> bool:
        """Validate RAG QA system initializes correctly."""
        print_section("4. RAG SYSTEM INITIALIZATION")

        try:
            from rag_qa_system import WellReportQASystem

            start = time.time()
            self.qa_system = WellReportQASystem(
                chroma_dir="chroma_db_toc_aware",
                collection_name="well_reports_toc_aware",
                llm_model="llama3.2:3b",
                temperature=0.1,
                top_k=5,
                verbose=False
            )
            init_time = time.time() - start

            print_result("RAG system initialization", True, f"Time: {init_time:.2f}s")
            self.results["metrics"]["system_init_time"] = init_time

            # Get statistics
            stats = self.qa_system.get_statistics()
            print_result("System statistics available", True,
                        f"{stats['total_documents']} docs, {len(stats['wells'])} wells")
            self.results["metrics"]["system_stats"] = stats

            return True

        except Exception as e:
            print_result("RAG system initialization", False, str(e))
            self.results["errors"].append(f"RAG init error: {str(e)}")
            return False

    def validate_query_quality(self) -> bool:
        """Test sample queries and measure quality."""
        print_section("5. QUERY QUALITY VALIDATION")

        if not self.qa_system:
            print_result("Query testing", False, "System not initialized")
            return False

        # Test queries with expected keywords
        test_queries = [
            {
                "question": "What is the total depth of Well 5?",
                "expected_keywords": ["depth", "well", "5", "meter", "m"],
                "category": "factual"
            },
            {
                "question": "Describe the casing program for Well 7.",
                "expected_keywords": ["casing", "well", "7"],
                "category": "descriptive"
            },
            {
                "question": "What drilling challenges were encountered?",
                "expected_keywords": ["drilling", "challenge", "problem"],
                "category": "analytical"
            }
        ]

        query_results = []
        total_queries = len(test_queries)
        passed_queries = 0

        for i, test in enumerate(test_queries, 1):
            print(f"\nQuery {i}/{total_queries}: {test['question']}")

            try:
                start = time.time()
                result = self.qa_system.query(test["question"])
                latency = time.time() - start

                # Check if answer is not empty
                has_answer = len(result.answer.strip()) > 0

                # Check for expected keywords (case-insensitive)
                answer_lower = result.answer.lower()
                keyword_matches = sum(1 for kw in test["expected_keywords"]
                                    if kw.lower() in answer_lower)
                keyword_ratio = keyword_matches / len(test["expected_keywords"])

                # Check source citation
                has_sources = len(result.sources) > 0

                # Overall pass if has answer, sources, and some keyword matches
                passed = has_answer and has_sources and keyword_ratio >= 0.3

                if passed:
                    passed_queries += 1

                print_result(f"  Answer generated", has_answer,
                           f"{len(result.answer)} chars" if has_answer else "")
                print_result(f"  Keyword match", keyword_ratio >= 0.3,
                           f"{keyword_ratio:.0%} ({keyword_matches}/{len(test['expected_keywords'])})")
                print_result(f"  Sources cited", has_sources,
                           f"{len(result.sources)} sources" if has_sources else "")
                print_result(f"  Latency", latency < 30, f"{latency:.2f}s")

                query_results.append({
                    "question": test["question"],
                    "category": test["category"],
                    "latency": latency,
                    "answer_length": len(result.answer),
                    "source_count": len(result.sources),
                    "keyword_ratio": keyword_ratio,
                    "passed": passed
                })

            except Exception as e:
                print_result(f"  Query execution", False, str(e))
                self.results["errors"].append(f"Query error: {test['question']}: {str(e)}")

        self.results["metrics"]["query_results"] = query_results
        self.results["metrics"]["query_pass_rate"] = passed_queries / total_queries

        print(f"\nQuery Quality Summary: {passed_queries}/{total_queries} passed ({passed_queries/total_queries:.0%})")

        return passed_queries >= total_queries * 0.7  # 70% pass rate required

    def validate_performance(self) -> bool:
        """Benchmark query performance."""
        print_section("6. PERFORMANCE BENCHMARKING")

        if not self.qa_system:
            print_result("Performance testing", False, "System not initialized")
            return False

        # Run 5 iterations of a standard query
        test_question = "What is the total depth of Well 5?"
        latencies = []

        print(f"Running 5 iterations: '{test_question}'")

        for i in range(5):
            try:
                start = time.time()
                self.qa_system.query(test_question)
                latency = time.time() - start
                latencies.append(latency)
                print(f"  Iteration {i+1}: {latency:.2f}s")
            except Exception as e:
                print_result(f"  Iteration {i+1}", False, str(e))

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)

            print(f"\nPerformance Metrics:")
            print(f"  Average: {avg_latency:.2f}s")
            print(f"  Min: {min_latency:.2f}s")
            print(f"  Max: {max_latency:.2f}s")

            self.results["metrics"]["performance"] = {
                "avg_latency": avg_latency,
                "min_latency": min_latency,
                "max_latency": max_latency
            }

            # Pass if average < 10s (target from grading criteria)
            passed = avg_latency < 10.0
            print_result("Performance target (<10s avg)", passed, f"{avg_latency:.2f}s")

            return passed

        return False

    def validate_error_handling(self) -> bool:
        """Test error handling for edge cases."""
        print_section("7. ERROR HANDLING VALIDATION")

        if not self.qa_system:
            print_result("Error handling test", False, "System not initialized")
            return False

        test_cases = [
            ("empty_query", ""),
            ("very_long_query", "What is " * 100),
            ("out_of_domain", "What is the recipe for chocolate cake?"),
            ("special_chars", "What is the depth??? <<>>"),
        ]

        passed_tests = 0
        for test_name, query in test_cases:
            try:
                result = self.qa_system.query(query)
                # Should return something without crashing
                has_answer = hasattr(result, 'answer')
                print_result(f"  {test_name}", has_answer, "Handled gracefully")
                if has_answer:
                    passed_tests += 1
            except Exception as e:
                print_result(f"  {test_name}", False, str(e))

        return passed_tests >= len(test_cases) * 0.75  # 75% should handle gracefully

    def save_results(self):
        """Save validation results to file."""
        output_dir = Path("outputs/validation")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nValidation report saved to: {output_file}")

    def run_validation(self) -> bool:
        """Run complete validation suite."""
        print("\n" + "=" * 80)
        print("  PRODUCTION RAG QA SYSTEM VALIDATION")
        print("=" * 80)

        validation_steps = [
            ("Dependencies", self.validate_dependencies),
            ("Database", self.validate_database),
            ("Ollama", self.validate_ollama),
            ("RAG System Init", self.validate_rag_system_init),
            ("Query Quality", self.validate_query_quality),
            ("Performance", self.validate_performance),
            ("Error Handling", self.validate_error_handling),
        ]

        results = []
        for step_name, step_func in validation_steps:
            try:
                passed = step_func()
                results.append((step_name, passed))
                self.results["tests"].append({
                    "name": step_name,
                    "passed": passed
                })
            except Exception as e:
                print_result(f"{step_name} (EXCEPTION)", False, str(e))
                results.append((step_name, False))
                self.results["errors"].append(f"{step_name} exception: {str(e)}")

        # Summary
        print_section("VALIDATION SUMMARY")

        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)

        for step_name, passed in results:
            print_result(step_name, passed)

        print(f"\nOverall: {passed_count}/{total_count} tests passed ({passed_count/total_count:.0%})")

        self.results["summary"] = {
            "total_tests": total_count,
            "passed_tests": passed_count,
            "pass_rate": passed_count / total_count,
            "production_ready": passed_count >= total_count * 0.85  # 85% threshold
        }

        self.save_results()

        if self.results["summary"]["production_ready"]:
            print("\n[+] SYSTEM IS PRODUCTION READY!")
        else:
            print("\n[X] SYSTEM NEEDS FIXES BEFORE PRODUCTION")
            print("\nErrors encountered:")
            for error in self.results["errors"]:
                print(f"  - {error}")

        return self.results["summary"]["production_ready"]


if __name__ == "__main__":
    validator = ProductionValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)
