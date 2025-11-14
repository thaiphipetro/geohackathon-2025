"""
Create updated 06_sub_challenge_1_guide.ipynb - Sub-Challenge 1 Grading Guide

Based on plan: .claude/tasks/jupyter-notebook-update-plan.md
Task 2.2: Update 06_sub_challenge_1_guide.ipynb
"""
import json
from pathlib import Path


def create_sub_challenge_1_guide():
    """Create updated Sub-Challenge 1 guide notebook"""

    cells = []

    # Cell 0: Title
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Sub-Challenge 1: RAG-Based Question Answering Guide\n",
            "\n",
            "**Comprehensive guide for Sub-Challenge 1 (50% of total grade)**\n",
            "\n",
            "## Challenge Overview\n",
            "\n",
            "**Objective:** Build a RAG-based QA system that can accurately answer questions about well completion reports.\n",
            "\n",
            "**Weight:** 50% of total grade\n",
            "\n",
            "**Status:** Production-Ready System Available\n",
            "\n",
            "### What You Need to Do\n",
            "\n",
            "Create a system that:\n",
            "1. Retrieves relevant information from well completion reports\n",
            "2. Generates accurate, factual answers using an LLM\n",
            "3. Provides source citations for all answers\n",
            "4. Responds quickly (<30 seconds per query)\n",
            "5. Handles various question types reliably\n",
            "\n",
            "### Production System Provided\n",
            "\n",
            "This notebook demonstrates the **production-ready RAG QA system** that has been implemented for you. It includes:\n",
            "\n",
            "- Pre-indexed ChromaDB with 5,258 documents\n",
            "- TOC-aware metadata (93.1% coverage)\n",
            "- Ollama Llama 3.2 3B integration\n",
            "- Section-filtered query capabilities\n",
            "- Source citation for all answers\n",
            "\n",
            "### Prerequisites\n",
            "\n",
            "- Ollama installed with `llama3.2:3b` model\n",
            "- Pre-indexed database at `../chroma_db_toc_aware/`\n",
            "- Python packages installed (see `requirements.txt`)\n",
            "\n",
            "**No manual indexing required** - the database is pre-built and ready to use!"
        ]
    })

    # Cell 1: Grading Criteria Markdown
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Grading Criteria\n",
            "\n",
            "Your submission will be evaluated on four main criteria:\n",
            "\n",
            "### 1. Answer Quality (40% of Sub-Challenge 1 grade)\n",
            "\n",
            "**What is evaluated:**\n",
            "- Factual accuracy of answers\n",
            "- Relevance to the question asked\n",
            "- Completeness of information\n",
            "- Technical correctness\n",
            "- Clarity and coherence\n",
            "\n",
            "**How to score well:**\n",
            "- Use low temperature (0.1) for factual answers\n",
            "- Ground answers in retrieved context\n",
            "- Don't hallucinate information not in the documents\n",
            "- Provide specific technical details when available\n",
            "\n",
            "**Example Good Answer:**\n",
            "```\n",
            "According to Well 5 EOWR Section 4.2, the total depth is 3,456 meters MD (Measured Depth) \n",
            "and 3,420 meters TVD (True Vertical Depth). The well was drilled to the Upper Rotliegend \n",
            "formation.\n",
            "```\n",
            "\n",
            "**Example Poor Answer:**\n",
            "```\n",
            "The well is pretty deep, probably around 3000-4000 meters or so.\n",
            "```\n",
            "\n",
            "### 2. Source Citation (30% of Sub-Challenge 1 grade)\n",
            "\n",
            "**What is evaluated:**\n",
            "- Presence of source metadata\n",
            "- Accuracy of source attribution\n",
            "- Completeness of citation information\n",
            "- Traceability to original documents\n",
            "\n",
            "**Required metadata for each source:**\n",
            "- Well name (e.g., \"well_5\")\n",
            "- PDF filename\n",
            "- Page number\n",
            "- Section title\n",
            "- Section type (when available)\n",
            "\n",
            "**How to score well:**\n",
            "- Include all retrieved sources in response\n",
            "- Provide complete metadata for each source\n",
            "- Ensure sources are actually relevant to the answer\n",
            "- Make it easy to verify the information\n",
            "\n",
            "### 3. Response Time (20% of Sub-Challenge 1 grade)\n",
            "\n",
            "**Performance targets:**\n",
            "- **Excellent (<10s):** Full marks\n",
            "- **Good (10-20s):** 80% marks\n",
            "- **Acceptable (20-30s):** 60% marks\n",
            "- **Slow (>30s):** Reduced marks\n",
            "\n",
            "**Optimization tips:**\n",
            "- Use efficient embeddings (nomic-embed-text-v1.5 is good)\n",
            "- Limit retrieval to top-k=5 documents\n",
            "- Use smaller LLM (Llama 3.2 3B is sufficient)\n",
            "- Pre-index the database (don't index at query time)\n",
            "\n",
            "### 4. System Robustness (10% of Sub-Challenge 1 grade)\n",
            "\n",
            "**What is evaluated:**\n",
            "- Handles various question types\n",
            "- Error handling and edge cases\n",
            "- Consistency across multiple queries\n",
            "- Documentation and usability\n",
            "\n",
            "**How to score well:**\n",
            "- Test on diverse questions\n",
            "- Handle \"I don't know\" cases gracefully\n",
            "- Provide clear error messages\n",
            "- Include usage documentation\n",
            "\n",
            "### Grade Calculation\n",
            "\n",
            "```\n",
            "Sub-Challenge 1 Score = (Answer Quality × 0.4) + \n",
            "                        (Source Citation × 0.3) + \n",
            "                        (Response Time × 0.2) + \n",
            "                        (System Robustness × 0.1)\n",
            "                        \n",
            "Total Grade = Sub-Challenge 1 Score × 0.5 + \n",
            "              Sub-Challenge 2 Score × 0.2 + \n",
            "              Sub-Challenge 3 Score × 0.3\n",
            "```"
        ]
    })

    # Cell 2: Setup
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Setup and Imports\n",
            "import sys\n",
            "import time\n",
            "from pathlib import Path\n",
            "\n",
            "# Add src to path\n",
            "project_root = Path('.').absolute().parent\n",
            "sys.path.insert(0, str(project_root / 'src'))\n",
            "\n",
            "# Import production RAG QA system\n",
            "from rag_qa_system import WellReportQASystem, QAResult\n",
            "\n",
            "print(\"Production RAG QA System ready!\")"
        ]
    })

    # Cell 3: System initialization markdown
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## System Initialization\n",
            "\n",
            "Initialize the production RAG QA system with pre-indexed database."
        ]
    })

    # Cell 4: Initialize system
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Initialize RAG QA system\n",
            "qa_system = WellReportQASystem(\n",
            "    chroma_dir=\"../chroma_db_toc_aware\",\n",
            "    collection_name=\"well_reports_toc_aware\",\n",
            "    llm_model=\"llama3.2:3b\",\n",
            "    temperature=0.1,  # Low temperature for factual answers\n",
            "    top_k=5,          # Retrieve top 5 most relevant documents\n",
            "    verbose=True\n",
            ")\n",
            "\n",
            "# Verify system is ready\n",
            "stats = qa_system.get_statistics()\n",
            "print(f\"\\nSystem ready with {stats['total_documents']:,} documents from {stats['num_wells']} wells\")"
        ]
    })

    # Cell 5: Sample evaluation queries markdown
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Sample Evaluation Queries\n",
            "\n",
            "These are the types of questions that may be used for grading. Practice with these to ensure your system performs well."
        ]
    })

    # Cell 6: Helper function
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "def evaluate_query(question, expected_keywords=None, filter_metadata=None):\n",
            "    \"\"\"\n",
            "    Evaluate a single query and display grading-relevant information\n",
            "    \n",
            "    Args:\n",
            "        question: Question to ask\n",
            "        expected_keywords: Keywords that should appear in good answer\n",
            "        filter_metadata: Optional metadata filters\n",
            "    \"\"\"\n",
            "    print(\"=\" * 80)\n",
            "    print(f\"QUESTION: {question}\")\n",
            "    if filter_metadata:\n",
            "        print(f\"FILTER: {filter_metadata}\")\n",
            "    print(\"=\" * 80)\n",
            "    \n",
            "    # Measure response time\n",
            "    start = time.time()\n",
            "    result = qa_system.query(question, filter_metadata=filter_metadata)\n",
            "    latency = time.time() - start\n",
            "    \n",
            "    # Display answer\n",
            "    print(f\"\\nANSWER:\")\n",
            "    print(result.answer)\n",
            "    \n",
            "    # Grading metrics\n",
            "    print(f\"\\n{'='*80}\")\n",
            "    print(\"GRADING METRICS\")\n",
            "    print(f\"{'='*80}\")\n",
            "    \n",
            "    # 1. Answer Quality\n",
            "    print(f\"\\n1. ANSWER QUALITY (40%):\")\n",
            "    print(f\"   - Answer length: {len(result.answer)} characters\")\n",
            "    if expected_keywords:\n",
            "        found = [kw for kw in expected_keywords if kw.lower() in result.answer.lower()]\n",
            "        print(f\"   - Expected keywords found: {len(found)}/{len(expected_keywords)}\")\n",
            "        print(f\"     Keywords: {', '.join(found) if found else 'None'}\")\n",
            "    \n",
            "    # 2. Source Citation\n",
            "    print(f\"\\n2. SOURCE CITATION (30%):\")\n",
            "    print(f\"   - Number of sources: {result.metadata['num_sources']}\")\n",
            "    print(f\"   - Source details:\")\n",
            "    for i, source in enumerate(result.sources[:3], 1):\n",
            "        print(f\"     [{i}] Well: {source['well_name']}, \"\n",
            "              f\"PDF: {source['pdf_file']}, \"\n",
            "              f\"Page: {source['page']}, \"\n",
            "              f\"Section: {source['section_type']}\")\n",
            "    \n",
            "    # 3. Response Time\n",
            "    print(f\"\\n3. RESPONSE TIME (20%):\")\n",
            "    print(f\"   - Latency: {latency:.2f}s\")\n",
            "    if latency < 10:\n",
            "        grade = \"Excellent (100%)\")\n",
            "    elif latency < 20:\n",
            "        grade = \"Good (80%)\"\n",
            "    elif latency < 30:\n",
            "        grade = \"Acceptable (60%)\"\n",
            "    else:\n",
            "        grade = \"Slow (reduced marks)\"\n",
            "    print(f\"   - Performance grade: {grade}\")\n",
            "    \n",
            "    # 4. System Robustness\n",
            "    print(f\"\\n4. SYSTEM ROBUSTNESS (10%):\")\n",
            "    print(f\"   - Query completed: Yes\")\n",
            "    print(f\"   - Sources retrieved: {result.metadata['num_sources'] > 0}\")\n",
            "    print(f\"   - Answer generated: {len(result.answer) > 0}\")\n",
            "    \n",
            "    print(f\"\\n{'='*80}\\n\")\n",
            "    return result, latency"
        ]
    })

    # Cell 7: Query Type 1 - Technical specifications
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Evaluation Query 1: Technical Specifications\n",
            "result1, latency1 = evaluate_query(\n",
            "    \"What is the total depth and casing program for Well 5?\",\n",
            "    expected_keywords=[\"depth\", \"meters\", \"casing\", \"diameter\"]\n",
            ")"
        ]
    })

    # Cell 8: Query Type 2 - Geological information
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Evaluation Query 2: Geological Information\n",
            "result2, latency2 = evaluate_query(\n",
            "    \"Describe the geological formations encountered in Well 7\",\n",
            "    expected_keywords=[\"formation\", \"geology\", \"lithology\"],\n",
            "    filter_metadata={\"well_name\": \"well_7\"}\n",
            ")"
        ]
    })

    # Cell 9: Query Type 3 - Drilling operations
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Evaluation Query 3: Drilling Operations\n",
            "result3, latency3 = evaluate_query(\n",
            "    \"What drilling fluid was used and were there any drilling problems?\",\n",
            "    expected_keywords=[\"mud\", \"fluid\", \"drilling\"],\n",
            "    filter_metadata={\"section_type\": \"drilling\"}\n",
            ")"
        ]
    })

    # Cell 10: Query Type 4 - Cross-well comparison
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Evaluation Query 4: Cross-Well Comparison\n",
            "result4, latency4 = evaluate_query(\n",
            "    \"What is the reservoir pressure?\",\n",
            "    expected_keywords=[\"pressure\", \"bar\", \"reservoir\"]\n",
            ")"
        ]
    })

    # Cell 11: Query Type 5 - Edge case (info not available)
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Evaluation Query 5: Edge Case - Information Not Available\n",
            "result5, latency5 = evaluate_query(\n",
            "    \"What is the well's production forecast for next year?\",\n",
            "    expected_keywords=None  # Should say \"cannot find\" or similar\n",
            ")"
        ]
    })

    # Cell 12: Performance summary
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Performance Summary\n",
            "latencies = [latency1, latency2, latency3, latency4, latency5]\n",
            "avg_latency = sum(latencies) / len(latencies)\n",
            "\n",
            "print(\"=\" * 80)\n",
            "print(\"OVERALL PERFORMANCE SUMMARY\")\n",
            "print(\"=\" * 80)\n",
            "print(f\"\\nTotal queries: {len(latencies)}\")\n",
            "print(f\"Average latency: {avg_latency:.2f}s\")\n",
            "print(f\"Min latency: {min(latencies):.2f}s\")\n",
            "print(f\"Max latency: {max(latencies):.2f}s\")\n",
            "\n",
            "# Estimate response time grade\n",
            "if avg_latency < 10:\n",
            "    time_grade = 100\n",
            "elif avg_latency < 20:\n",
            "    time_grade = 80\n",
            "elif avg_latency < 30:\n",
            "    time_grade = 60\n",
            "else:\n",
            "    time_grade = 40\n",
            "\n",
            "print(f\"\\nEstimated Response Time Grade: {time_grade}% (20% of total)\")\n",
            "print(\"=\" * 80)"
        ]
    })

    # Cell 13: How to use filters markdown
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## How to Use Filters\n",
            "\n",
            "The production system supports intelligent filtering to improve answer quality and reduce response time.\n",
            "\n",
            "### Available Filters\n",
            "\n",
            "**1. Well Name Filter**\n",
            "```python\n",
            "filter_metadata={\"well_name\": \"well_5\"}\n",
            "```\n",
            "\n",
            "**2. Section Type Filter**\n",
            "```python\n",
            "filter_metadata={\"section_type\": \"casing\"}  # or \"geology\", \"drilling\", etc.\n",
            "```\n",
            "\n",
            "**3. Combined Filters (AND)**\n",
            "```python\n",
            "filter_metadata={\n",
            "    \"$and\": [\n",
            "        {\"well_name\": \"well_7\"},\n",
            "        {\"section_type\": \"completion\"}\n",
            "    ]\n",
            "}\n",
            "```\n",
            "\n",
            "### Available Section Types\n",
            "\n",
            "The system recognizes these section types (from TOC-aware indexing):\n",
            "- `casing` - Casing program and specifications\n",
            "- `geology` - Geological formations and lithology\n",
            "- `drilling` - Drilling operations and problems\n",
            "- `completion` - Well completion details\n",
            "- `testing` - Well testing and production data\n",
            "- `mud` - Drilling fluid specifications\n",
            "- `cementing` - Cementing operations\n",
            "- `logging` - Well logging data\n",
            "- `perforation` - Perforation details\n",
            "- `summary` - Executive summaries\n",
            "- `none` - Sections without classified type\n",
            "\n",
            "### When to Use Filters\n",
            "\n",
            "**Use well name filter when:**\n",
            "- Question is specific to one well\n",
            "- Reduces search space and improves speed\n",
            "\n",
            "**Use section type filter when:**\n",
            "- Question is about specific technical topic\n",
            "- Improves relevance of retrieved documents\n",
            "- Reduces noise from unrelated sections\n",
            "\n",
            "**Use combined filters when:**\n",
            "- Need high precision\n",
            "- Question is very specific"
        ]
    })

    # Cell 14: Testing your own queries
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Test Your Own Queries\n",
            "\n",
            "Use this cell to test custom queries and practice for evaluation."
        ]
    })

    # Cell 15: Custom query cell
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Test your own query here!\n",
            "custom_question = \"What is the inner diameter of the production casing?\"\n",
            "custom_filter = {\"section_type\": \"casing\"}  # Optional\n",
            "custom_keywords = [\"diameter\", \"casing\"]     # Keywords you expect in good answer\n",
            "\n",
            "result_custom, latency_custom = evaluate_query(\n",
            "    custom_question,\n",
            "    expected_keywords=custom_keywords,\n",
            "    filter_metadata=custom_filter\n",
            ")"
        ]
    })

    # Cell 16: Submission checklist
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Submission Checklist\n",
            "\n",
            "Before submitting your Sub-Challenge 1 solution, verify:\n",
            "\n",
            "### Answer Quality (40%)\n",
            "- [ ] Answers are factual and grounded in source documents\n",
            "- [ ] No hallucinations or unsupported claims\n",
            "- [ ] Technical terminology is correct\n",
            "- [ ] Answers are clear and complete\n",
            "- [ ] System says \"I don't know\" when information is not available\n",
            "\n",
            "### Source Citation (30%)\n",
            "- [ ] Every answer includes source metadata\n",
            "- [ ] Sources include: well name, PDF file, page number, section title\n",
            "- [ ] Sources are actually relevant to the answer\n",
            "- [ ] Easy to verify information in original documents\n",
            "- [ ] At least 3-5 sources retrieved per query\n",
            "\n",
            "### Response Time (20%)\n",
            "- [ ] Average query time <10s for excellent grade\n",
            "- [ ] Average query time <20s for good grade\n",
            "- [ ] No query takes >30s\n",
            "- [ ] System is responsive and doesn't hang\n",
            "\n",
            "### System Robustness (10%)\n",
            "- [ ] Handles various question types\n",
            "- [ ] Error handling for edge cases\n",
            "- [ ] Clear documentation provided\n",
            "- [ ] Easy to install and run\n",
            "- [ ] Code is clean and well-organized\n",
            "\n",
            "### Technical Requirements\n",
            "- [ ] Uses production RAG QA system (`src/rag_qa_system.py`)\n",
            "- [ ] ChromaDB pre-indexed (no indexing at query time)\n",
            "- [ ] Ollama Llama 3.2 3B for generation\n",
            "- [ ] All dependencies in `requirements.txt`\n",
            "- [ ] No Docker required\n",
            "- [ ] Runs on CPU only\n",
            "\n",
            "## Tips for High Grades\n",
            "\n",
            "1. **Use the production system** - It's already optimized for all criteria\n",
            "2. **Test on diverse questions** - Make sure it works for all query types\n",
            "3. **Use appropriate filters** - Improves both quality and speed\n",
            "4. **Document your approach** - Clear README helps grading\n",
            "5. **Verify source citations** - Manually check a few to ensure accuracy\n",
            "\n",
            "## Next Steps\n",
            "\n",
            "1. Practice with the sample evaluation queries above\n",
            "2. Test your own questions to understand system capabilities\n",
            "3. Review `07_production_rag_qa_demo.ipynb` for detailed system guide\n",
            "4. Move to Sub-Challenge 2 (Parameter Extraction - 20%)\n",
            "5. Complete Sub-Challenge 3 (Agentic Workflow - 30%)\n",
            "\n",
            "**Good luck with your submission!**"
        ]
    })

    # Create notebook structure
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    # Write notebook
    output_path = Path("notebooks/06_sub_challenge_1_guide_updated.ipynb")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)

    print(f"Created updated Sub-Challenge 1 guide: {output_path}")
    print(f"Total cells: {len(cells)}")
    print(f"\\nNotebook sections:")
    print(f"  1. Challenge Overview & Prerequisites")
    print(f"  2. Grading Criteria (detailed breakdown)")
    print(f"  3. System Initialization")
    print(f"  4. Sample Evaluation Queries (5 types)")
    print(f"  5. How to Use Filters")
    print(f"  6. Test Your Own Queries")
    print(f"  7. Submission Checklist")


if __name__ == '__main__':
    create_sub_challenge_1_guide()
