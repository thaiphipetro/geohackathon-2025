# Sub-Challenge 1: Testing Suite

Comprehensive testing infrastructure for RAG system validation.

## Quick Start

### 1. Build Ground Truth (Manual - 1-2 hours)

```bash
# Option A: Interactive mode (query RAG and validate answers)
python tests/build_ground_truth.py --mode interactive

# Option B: Template mode (manually fill from PDFs)
python tests/build_ground_truth.py --mode template
# Then edit: tests/ground_truth_template.json
# Rename to: tests/ground_truth.json
```

### 2. Run Performance Benchmark (~5 minutes)

```bash
python tests/benchmark_performance.py
```

**Expected Output:**
```
PERFORMANCE BENCHMARK REPORT
Total Queries:       14
Average:             6.5s
Target:              <10.0s
Status:              ✓ MEETS TARGET
```

### 3. Run Accuracy Evaluation (~10 minutes)

```bash
# Requires ground_truth.json from step 1
python tests/evaluate_rag_accuracy.py
```

**Expected Output:**
```
RAG ACCURACY EVALUATION REPORT
Total Questions:     30
Passed (≥80%):       27 (90.0%)
Accuracy:            92.3%
Target:              90.0%
Status:              ✓ MEETS TARGET
```

---

## Test Files

### Test Questions (`test_questions.json`)

30 questions across 10 categories:
- **well_identification** (3) - Well names and IDs
- **location** (3) - Coordinates and locations
- **dates** (3) - Drilling dates and timelines
- **operator** (3) - Company and contractor info
- **depth** (3) - MD, TVD, and well depth
- **casing** (3) - Casing sizes and specifications
- **equipment** (3) - Drilling equipment
- **summarization** (3) - Summary questions
- **missing_info** (3) - Questions with no answers
- **multi_well** (3) - Cross-well comparisons

### Ground Truth (`ground_truth.json`)

Manually validated answers for each test question.

**Structure:**
```json
{
  "metadata": {
    "created": "2025-11-08",
    "method": "manual_validation",
    "total_questions": 30,
    "validated": 30
  },
  "answers": {
    "Q001": {
      "question": "What wells are reported?",
      "well": "Well 5",
      "category": "well_identification",
      "answer": "NLW-GT-03",
      "expected_info": ["NLW-GT-03", "well name"],
      "validated": true
    }
  }
}
```

---

## Scripts

### `build_ground_truth.py`

Interactive tool to create ground truth dataset.

**Usage:**
```bash
# Interactive mode: Query RAG and validate
python tests/build_ground_truth.py --mode interactive

# Template mode: Create manual template
python tests/build_ground_truth.py --mode template
```

**Interactive Mode:**
- Queries RAG system for each question
- Shows answer and sources
- Allows you to:
  - **ENTER** - Accept answer as-is
  - **edit** - Modify the answer
  - **skip** - Skip this question
  - **quit** - Save and exit

**Template Mode:**
- Creates `ground_truth_template.json`
- You manually fill in answers from PDFs
- Rename to `ground_truth.json` when done

---

### `evaluate_rag_accuracy.py`

Automated accuracy evaluation against ground truth.

**Usage:**
```bash
python tests/evaluate_rag_accuracy.py [options]

Options:
  --ground-truth PATH   Path to ground truth file (default: tests/ground_truth.json)
  --output PATH         Path to save results (default: tests/evaluation_results.json)
  --verbose             Show detailed results
```

**Output:**
- `evaluation_results.json` - Full results with individual scores
- Console report with summary and failed questions

**Metrics:**
- **Accuracy**: Percentage of questions answered correctly
- **Pass Rate**: Percentage of questions with ≥80% accuracy
- **Category Breakdown**: Accuracy by question category
- **Failed Questions**: List of questions that failed

**Success Criteria:**
- ✓ Average accuracy ≥90%
- ✓ Pass rate ≥80%
- ✓ All categories ≥75% accuracy

---

### `benchmark_performance.py`

Performance benchmarking suite.

**Usage:**
```bash
python tests/benchmark_performance.py [options]

Options:
  --output PATH         Path to save results (default: tests/benchmark_results.json)
```

**Output:**
- `benchmark_results.json` - Detailed timing data
- Console report with performance statistics

**Metrics:**
- **Average Time**: Mean query time
- **Median Time**: Median query time
- **95th Percentile**: 95th percentile time
- **Category Breakdown**: Time by question category
- **Component Timing**: Embedding, retrieval, LLM times

**Success Criteria:**
- ✓ Average time <10 seconds
- ✓ 95th percentile <15 seconds
- ✓ All categories <12 seconds

---

## Running All Tests

### Quick Test (5 minutes)

```bash
# Run performance benchmark only
python tests/benchmark_performance.py
```

### Full Test Suite (15 minutes)

```bash
# 1. Build ground truth (if not done yet)
python tests/build_ground_truth.py --mode interactive

# 2. Run performance benchmark
python tests/benchmark_performance.py

# 3. Run accuracy evaluation
python tests/evaluate_rag_accuracy.py
```

### Automated CI/CD Test

```bash
# Run both tests and fail if either doesn't meet target
python tests/benchmark_performance.py && python tests/evaluate_rag_accuracy.py
```

---

## Interpreting Results

### Performance Results

**Good:**
```
Average Time:            6.5s    ✓
95th percentile:         9.2s    ✓
Status:                  ✓ MEETS TARGET
```

**Needs Improvement:**
```
Average Time:            12.3s   ✗ TOO SLOW
95th percentile:         18.5s   ✗
Status:                  ✗ TOO SLOW
```

**Optimization Targets:**
- Embedding: <1s
- Retrieval: <2s
- LLM: <6s
- Total: <10s

### Accuracy Results

**Good:**
```
Accuracy:                92.3%   ✓
Pass Rate:               90.0%   ✓
Status:                  ✓ MEETS TARGET
```

**Needs Improvement:**
```
Accuracy:                85.2%   ✗ BELOW TARGET
Pass Rate:               73.3%   ✗
Status:                  ✗ BELOW TARGET
```

**Common Issues:**
- Missing information → Check indexing
- Wrong well → Check metadata filtering
- Incorrect numbers → Check table extraction
- Generic answers → Improve LLM prompts

---

## Troubleshooting

### Issue: "Ground truth file not found"

**Solution:**
```bash
python tests/build_ground_truth.py --mode interactive
```

### Issue: "ChromaDB connection failed"

**Solution:**
```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Start ChromaDB if needed
docker-compose up -d chromadb
```

### Issue: "Ollama connection failed"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Issue: "Slow queries (>10s)"

**Causes:**
- LLM generation is slow (CPU-bound)
- Too many chunks retrieved
- Large context size

**Solutions:**
- Reduce n_results from 5 to 3
- Use more specific queries
- Optimize chunk size

### Issue: "Low accuracy (<90%)"

**Causes:**
- Poor retrieval (wrong chunks)
- Poor LLM generation
- Incorrect ground truth

**Solutions:**
- Check retrieval quality
- Improve section filtering
- Tune embedding parameters
- Review failed questions

---

## File Outputs

After running all tests, you'll have:

```
tests/
├── test_questions.json              ✓ 30 test questions
├── ground_truth.json                ✓ Validated answers
├── evaluation_results.json          ✓ Accuracy results
├── benchmark_results.json           ✓ Performance results
└── ground_truth_template.json       Optional manual template
```

---

## Next Steps After Testing

### If All Tests Pass ✓

1. Document results in final report
2. Create demo video
3. Prepare submission

### If Performance Fails (<10s)

1. Profile slow queries
2. Optimize LLM parameters
3. Reduce chunk retrieval
4. Re-benchmark

### If Accuracy Fails (<90%)

1. Analyze failed questions
2. Improve retrieval strategy
3. Enhance LLM prompts
4. Re-evaluate

---

## Judge Evaluation Criteria

Based on hackathon requirements:

| Criterion | Weight | Target | How We Test |
|-----------|--------|--------|-------------|
| **Accuracy** | High | >90% | `evaluate_rag_accuracy.py` |
| **Speed** | High | <10s | `benchmark_performance.py` |
| **Completeness** | Medium | All info | Test question coverage |
| **Minimal Prompts** | Low | 1 query | Single-shot testing |

**Our Targets:**
- ✓ Accuracy: ≥90%
- ✓ Speed: <10s average, <15s p95
- ✓ Coverage: 30 questions across 10 categories
- ✓ Single-shot: All questions answered in 1 query

---

## Tips for Building Ground Truth

### DO:
- ✓ Read the actual PDF to verify answers
- ✓ Use exact numbers from documents
- ✓ Include all expected information
- ✓ Mark "not found" for missing info

### DON'T:
- ✗ Accept RAG answers without verification
- ✗ Guess or estimate values
- ✗ Skip difficult questions
- ✗ Use approximate numbers

### Quality Checklist:
- [ ] Answer is factually correct
- [ ] Answer is complete
- [ ] Source page/section noted
- [ ] Expected info is present
- [ ] Confidence level marked

---

## Contact

For issues or questions about the testing suite:
1. Check this README
2. Review test output files
3. Check `.claude/tasks/sub-challenge-1-status-assessment.md`
