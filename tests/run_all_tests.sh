#!/bin/bash
# Run all Sub-Challenge 1 tests

echo "================================================================================"
echo "SUB-CHALLENGE 1: COMPREHENSIVE TEST SUITE"
echo "================================================================================"

# Check prerequisites
echo ""
echo "[1/5] Checking prerequisites..."

# Check if ground truth exists
if [ ! -f "tests/ground_truth.json" ]; then
    echo "⚠️  WARNING: Ground truth not found!"
    echo ""
    echo "You need to build ground truth first:"
    echo "  python tests/build_ground_truth.py --mode interactive"
    echo ""
    echo "Or create manual template:"
    echo "  python tests/build_ground_truth.py --mode template"
    echo ""
    exit 1
fi

echo "✓ Ground truth found"

# Check if RAG system files exist
if [ ! -f "src/rag_system.py" ]; then
    echo "✗ ERROR: RAG system not found!"
    exit 1
fi

echo "✓ RAG system found"

# Check if ChromaDB is running
if ! curl -s http://localhost:8000/api/v2/heartbeat > /dev/null 2>&1; then
    echo "⚠️  WARNING: ChromaDB might not be running"
    echo "   If tests fail, start with: docker-compose up -d chromadb"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  WARNING: Ollama might not be running"
    echo "   If tests fail, start with: ollama serve"
fi

echo ""
echo "[2/5] Running performance benchmark..."
echo "--------------------------------------------------------------------------------"

python tests/benchmark_performance.py
BENCH_EXIT=$?

echo ""
echo "[3/5] Running accuracy evaluation..."
echo "--------------------------------------------------------------------------------"

python tests/evaluate_rag_accuracy.py
EVAL_EXIT=$?

echo ""
echo "[4/5] Generating summary report..."
echo "--------------------------------------------------------------------------------"

# Create summary report
cat << SUMMARY

================================================================================ 
FINAL SUMMARY
================================================================================

Test Results:
  Performance Benchmark:  $( [ $BENCH_EXIT -eq 0 ] && echo "✓ PASSED" || echo "✗ FAILED" )
  Accuracy Evaluation:    $( [ $EVAL_EXIT -eq 0 ] && echo "✓ PASSED" || echo "✗ FAILED" )

Output Files:
  tests/benchmark_results.json     - Performance metrics
  tests/evaluation_results.json    - Accuracy metrics

SUMMARY

if [ $BENCH_EXIT -eq 0 ] && [ $EVAL_EXIT -eq 0 ]; then
    echo ""
    echo "✓ ALL TESTS PASSED!"
    echo ""
    echo "Next steps:"
    echo "  1. Review detailed results in output files"
    echo "  2. Document results in final report"
    echo "  3. Prepare demo for judges"
    echo ""
    exit 0
else
    echo ""
    echo "⚠️  SOME TESTS FAILED"
    echo ""
    echo "Review the output above to identify issues."
    echo "See tests/README.md for troubleshooting guide."
    echo ""
    exit 1
fi
