# Hybrid LangGraph + Pydantic AI Implementation Plan

**Status:** Implementation Plan
**Created:** 2025-11-10
**Approach:** Use both LangGraph and Pydantic AI for their complementary strengths

---

## Executive Summary

**Strategy:** Hybrid approach leveraging both frameworks
- **Pydantic AI**: Structured parameter extraction (Sub-Challenge 2, 20%)
- **LangGraph**: Agent orchestration (Sub-Challenge 3, 30%)
- **Either**: RAG queries (Sub-Challenge 1, 50%)

**Key Insight:** Don't choose one - use both for maximum effectiveness

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph ReAct Agent                     │
│                   (Sub-Challenge 3 - 30%)                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Tool 1:    │  │   Tool 2:    │  │   Tool 3:    │     │
│  │  Query RAG   │  │   Extract    │  │    Nodal     │     │
│  │              │  │  Parameters  │  │   Analysis   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
    ┌──────────┐   ┌─────────────────┐   ┌──────────┐
    │ ChromaDB │   │  Pydantic AI     │   │  Nodal   │
    │   RAG    │   │  Agent with      │   │ Analysis │
    │  System  │   │  Validation      │   │  Wrapper │
    │          │   │ (Sub-Challenge 2)│   │          │
    └──────────┘   └─────────────────┘   └──────────┘
```

---

## Project Structure

```
src/
├── models/                          # Pydantic models (shared)
│   ├── __init__.py
│   ├── well_data.py                # WellSection, WellCompletionData
│   └── validators.py               # Physics validators
│
├── rag_system.py                   # Sub-Challenge 1 (existing)
├── embeddings.py                   # (existing)
├── vector_store.py                 # (existing)
│
├── extraction_agent.py             # ⭐ NEW: Pydantic AI agent
│   └── Sub-Challenge 2 implementation
│
├── orchestrator_agent.py           # ⭐ NEW: LangGraph agent
│   └── Sub-Challenge 3 implementation
│
├── tools/                          # LangGraph tools
│   ├── __init__.py
│   ├── rag_tool.py                # Wraps RAG system
│   ├── extraction_tool.py         # Wraps Pydantic AI agent
│   └── nodal_tool.py              # Wraps NodalAnalysis.py
│
└── nodal_analysis_wrapper.py      # (existing)
```

---

## Implementation Details

### Phase 1: Shared Models (Day 1, 2 hours)

**File: `src/models/well_data.py`**

```python
"""
Shared Pydantic models for well completion data
Used by both Pydantic AI and LangGraph
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class WellSection(BaseModel):
    """Single casing section with depth and diameter"""

    measured_depth: float = Field(
        description="Measured Depth (MD) in meters - distance along wellbore"
    )
    true_vertical_depth: float = Field(
        description="True Vertical Depth (TVD) in meters - vertical distance"
    )
    inner_diameter: float = Field(
        description="Inner Diameter (ID) in meters - pipe internal diameter"
    )

    @field_validator('measured_depth', 'true_vertical_depth', 'inner_diameter')
    @classmethod
    def must_be_positive(cls, v: float, info) -> float:
        if v <= 0:
            raise ValueError(f'{info.field_name} must be positive, got {v}')
        return v


class WellCompletionData(BaseModel):
    """Complete well trajectory for nodal analysis"""

    well_name: str = Field(description="Well identifier (e.g., 'NLW-GT-03')")
    sections: List[WellSection] = Field(
        min_length=2,
        description="Casing sections ordered by depth"
    )
    unit_system: str = Field(default="meters", description="Units for depths")

    @field_validator('sections')
    @classmethod
    def sections_ordered_by_depth(cls, sections: List[WellSection]) -> List[WellSection]:
        """Ensure sections are ordered by increasing MD"""
        if len(sections) < 2:
            raise ValueError('At least 2 sections required')

        for i in range(len(sections) - 1):
            if sections[i].measured_depth >= sections[i+1].measured_depth:
                raise ValueError('Sections must be ordered by increasing MD')

        return sections

    def to_nodal_format(self) -> List[dict]:
        """
        Export to NodalAnalysis.py format

        Returns:
            [
                {"MD": 0.0, "TVD": 0.0, "ID": 0.3397},
                {"MD": 500.0, "TVD": 500.0, "ID": 0.2445},
                ...
            ]
        """
        return [
            {
                "MD": section.measured_depth,
                "TVD": section.true_vertical_depth,
                "ID": section.inner_diameter
            }
            for section in self.sections
        ]
```

**File: `src/models/validators.py`**

```python
"""
Physics-based validators for well data
Used with Pydantic AI's ModelRetry for automatic correction
"""

from pydantic_ai import ModelRetry


def validate_depth_relationship(md: float, tvd: float) -> None:
    """
    Ensure MD >= TVD (fundamental physical constraint)

    Raises:
        ModelRetry: With explanation for the LLM to retry
    """
    if md < tvd:
        raise ModelRetry(
            f'Measured Depth ({md}m) must be >= True Vertical Depth ({tvd}m). '
            f'MD is measured along the wellbore path, TVD is straight down. '
            f'For vertical wells MD≈TVD, for deviated wells MD>TVD.'
        )


def validate_diameter_range(id_meters: float) -> None:
    """
    Ensure diameter is within realistic casing range

    Common casing sizes: 4.5" to 20" (0.11m to 0.51m)
    """
    if id_meters < 0.10 or id_meters > 0.60:
        raise ModelRetry(
            f'Inner Diameter {id_meters}m is outside realistic range (0.10-0.60m). '
            f'Common casing: 7" (0.178m), 9⅝" (0.245m), 13⅜" (0.340m). '
            f'If value is in inches, convert: ID_meters = ID_inches × 0.0254'
        )


def validate_section_consistency(sections: list[dict]) -> None:
    """
    Ensure sections form a valid completion string

    Rules:
    - Diameters decrease with depth (telescoping)
    - No gaps or overlaps in MD
    """
    for i in range(len(sections) - 1):
        curr = sections[i]
        next_section = sections[i + 1]

        # Check diameter telescoping
        if curr['inner_diameter'] <= next_section['inner_diameter']:
            raise ModelRetry(
                f'Casing must telescope (decrease in diameter with depth). '
                f'Section at {curr["measured_depth"]}m has ID={curr["inner_diameter"]}m, '
                f'but next section at {next_section["measured_depth"]}m has larger ID={next_section["inner_diameter"]}m'
            )
```

---

### Phase 2: Pydantic AI Extraction Agent (Days 2-3, 8 hours)

**File: `src/extraction_agent.py`**

```python
"""
Pydantic AI Agent for extracting structured well completion parameters
Sub-Challenge 2 (20% of grade)

Key Features:
- Automatic Pydantic validation
- Physics-based validators with ModelRetry
- Type-safe output guaranteed
"""

from dataclasses import dataclass
from typing import Optional
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from models.well_data import WellSection, WellCompletionData
from models.validators import (
    validate_depth_relationship,
    validate_diameter_range,
    validate_section_consistency
)
from rag_system import RAGSystem


@dataclass
class ExtractionDependencies:
    """Dependencies injected into extraction agent"""
    rag_system: RAGSystem
    well_name: str


class WellParameterExtractor:
    """
    Extracts MD, TVD, ID from well documents using Pydantic AI

    Advantages over plain LLM:
    - Automatic retry on validation errors
    - Physics constraints enforced
    - Type-safe output
    """

    def __init__(self, ollama_base_url: str = "http://localhost:11434/v1"):
        # Initialize Ollama via OpenAI-compatible API
        ollama_model = OpenAIChatModel(
            model_name='llama3.2:3b',
            provider=OllamaProvider(base_url=ollama_base_url)
        )

        # Create agent with structured output
        self.agent = Agent[ExtractionDependencies, WellCompletionData](
            model=ollama_model,
            output_type=WellCompletionData,
            deps_type=ExtractionDependencies,
            system_prompt=self._get_system_prompt(),
            retries=3  # Allow 3 attempts per validation failure
        )

        # Register output validator
        self.agent.output_validator(self._validate_output)

    def _get_system_prompt(self) -> str:
        return """You are a well completion data extraction expert.

Your task: Extract casing completion data from well reports.

REQUIRED DATA:
1. Measured Depth (MD) - distance along wellbore in METERS
2. True Vertical Depth (TVD) - vertical distance in METERS
3. Inner Diameter (ID) - pipe internal diameter in METERS

CRITICAL RULES:
- MD must be >= TVD (physical law)
- ID must be positive and realistic (0.10-0.60 meters)
- Diameters decrease with depth (telescoping)
- Convert inches to meters: multiply by 0.0254

COMMON CASING SIZES (for reference):
- 7" = 0.178m
- 9⅝" = 0.245m
- 13⅜" = 0.340m

If data is missing or unclear, query the documents using available tools."""

    @staticmethod
    async def _validate_output(
        ctx: RunContext[ExtractionDependencies],
        output: WellCompletionData
    ) -> WellCompletionData:
        """
        Validate extracted data with physics constraints

        Raises ModelRetry on validation failure, providing feedback to LLM
        """
        # Validate each section
        for i, section in enumerate(output.sections):
            # Check MD >= TVD
            validate_depth_relationship(
                section.measured_depth,
                section.true_vertical_depth
            )

            # Check diameter range
            validate_diameter_range(section.inner_diameter)

        # Validate section consistency (telescoping, etc.)
        sections_dict = [
            {
                'measured_depth': s.measured_depth,
                'true_vertical_depth': s.true_vertical_depth,
                'inner_diameter': s.inner_diameter
            }
            for s in output.sections
        ]
        validate_section_consistency(sections_dict)

        return output

    @Agent.tool
    async def search_casing_tables(
        self,
        ctx: RunContext[ExtractionDependencies],
        query: str
    ) -> str:
        """Search well documents for casing completion tables"""
        # Use RAG system to find relevant chunks
        results = ctx.deps.rag_system.query(
            query,
            well_filter=ctx.deps.well_name,
            chunk_type_filter='table',  # Focus on table chunks
            top_k=5
        )
        return results['answer']

    @Agent.tool
    async def search_well_documents(
        self,
        ctx: RunContext[ExtractionDependencies],
        query: str
    ) -> str:
        """Search all well documents (text, tables, pictures)"""
        results = ctx.deps.rag_system.query(
            query,
            well_filter=ctx.deps.well_name,
            top_k=10
        )
        return results['answer']

    async def extract(
        self,
        well_name: str,
        rag_system: RAGSystem
    ) -> WellCompletionData:
        """
        Extract well completion parameters

        Args:
            well_name: Well identifier (e.g., "NLW-GT-03")
            rag_system: RAG system to query documents

        Returns:
            WellCompletionData with validated sections

        Raises:
            Exception: If extraction fails after retries
        """
        deps = ExtractionDependencies(
            rag_system=rag_system,
            well_name=well_name
        )

        result = await self.agent.run(
            f'Extract the casing completion data for {well_name}. '
            f'Find the MD, TVD, and ID for each casing section.',
            deps=deps
        )

        return result.output

    def extract_sync(
        self,
        well_name: str,
        rag_system: RAGSystem
    ) -> WellCompletionData:
        """Synchronous version of extract()"""
        import asyncio
        return asyncio.run(self.extract(well_name, rag_system))


# Example usage
if __name__ == '__main__':
    from rag_system import RAGSystem

    rag = RAGSystem()
    extractor = WellParameterExtractor()

    # Extract with automatic validation
    result = extractor.extract_sync('NLW-GT-03', rag)

    print(f"Extracted {len(result.sections)} sections")
    print(f"Export format: {result.to_nodal_format()}")
```

---

### Phase 3: LangGraph Orchestration Agent (Days 4-6, 12 hours)

**File: `src/tools/rag_tool.py`**

```python
"""LangGraph tool wrapping RAG system"""

from langchain_core.tools import tool
from rag_system import RAGSystem

# Initialize RAG system (singleton)
_rag_system = None

def get_rag_system() -> RAGSystem:
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system


@tool
def query_well_documents(question: str, well_name: str = None) -> str:
    """
    Query well completion reports using RAG.

    Args:
        question: Natural language question about well data
        well_name: Optional well filter (e.g., "Well 5", "NLW-GT-03")

    Returns:
        Answer with source citations

    Examples:
        - "What is the total depth of Well 5?"
        - "Find the 9⅝ inch casing depth for NLW-GT-03"
        - "What casing sizes were used in Well 5?"
    """
    rag = get_rag_system()
    result = rag.query(question, well_filter=well_name, top_k=10)
    return result['answer']
```

**File: `src/tools/extraction_tool.py`**

```python
"""LangGraph tool wrapping Pydantic AI extraction agent"""

from langchain_core.tools import tool
from extraction_agent import WellParameterExtractor
from tools.rag_tool import get_rag_system
import json

# Initialize extractor (singleton)
_extractor = None

def get_extractor() -> WellParameterExtractor:
    global _extractor
    if _extractor is None:
        _extractor = WellParameterExtractor()
    return _extractor


@tool
def extract_well_parameters(well_name: str) -> str:
    """
    Extract structured casing completion parameters (MD, TVD, ID) from well documents.

    This tool uses Pydantic AI with physics-based validation to ensure accurate extraction.

    Args:
        well_name: Well identifier (e.g., "NLW-GT-03", "Well 5")

    Returns:
        JSON string with validated well completion data in NodalAnalysis.py format:
        {
            "well_name": "NLW-GT-03",
            "sections": [
                {"MD": 0.0, "TVD": 0.0, "ID": 0.3397},
                {"MD": 500.0, "TVD": 500.0, "ID": 0.2445},
                ...
            ]
        }

    The tool automatically:
    - Validates MD >= TVD (physics constraint)
    - Checks diameter ranges (0.10-0.60m)
    - Ensures telescoping (diameters decrease with depth)
    - Retries up to 3 times on validation errors
    """
    extractor = get_extractor()
    rag = get_rag_system()

    try:
        result = extractor.extract_sync(well_name, rag)

        # Convert to NodalAnalysis.py format
        output = {
            'well_name': result.well_name,
            'sections': result.to_nodal_format()
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error extracting parameters: {str(e)}"
```

**File: `src/tools/nodal_tool.py`**

```python
"""LangGraph tool wrapping NodalAnalysis.py"""

from langchain_core.tools import tool
from pathlib import Path
import json
import sys

# Add NodalAnalysis.py to path
nodal_path = Path("Training data-shared with participants")
sys.path.insert(0, str(nodal_path))


@tool
def run_nodal_analysis(well_trajectory_json: str) -> str:
    """
    Run nodal analysis to calculate well flow rate and bottom hole pressure.

    Args:
        well_trajectory_json: JSON string with well trajectory in format:
            {
                "well_name": "NLW-GT-03",
                "sections": [
                    {"MD": 0.0, "TVD": 0.0, "ID": 0.3397},
                    {"MD": 500.0, "TVD": 500.0, "ID": 0.2445},
                    ...
                ]
            }

    Returns:
        JSON string with nodal analysis results:
        {
            "well_name": "NLW-GT-03",
            "flow_rate": 1234.5,
            "bottom_hole_pressure": 230.0,
            "units": {"flow_rate": "m3/day", "pressure": "bar"}
        }

    Note: NodalAnalysis.py uses hardcoded reservoir parameters:
    - Reservoir pressure: 230 bar
    - Wellhead pressure: 10 bar
    - Productivity Index (PI): 5.0
    - ESP depth: 500m
    """
    try:
        from NodalAnalysis import calculate_flow_rate

        # Parse input
        data = json.loads(well_trajectory_json)
        well_name = data['well_name']
        trajectory = data['sections']

        # Run analysis
        results = calculate_flow_rate(trajectory)

        # Format output
        output = {
            'well_name': well_name,
            'flow_rate': results['flow_rate'],
            'bottom_hole_pressure': results['bhp'],
            'units': {
                'flow_rate': 'm3/day',
                'pressure': 'bar'
            }
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error running nodal analysis: {str(e)}"
```

**File: `src/orchestrator_agent.py`**

```python
"""
LangGraph ReAct Agent for well performance analysis workflow
Sub-Challenge 3 (30% of grade)

Orchestrates:
1. RAG queries (Sub-Challenge 1)
2. Parameter extraction (Sub-Challenge 2)
3. Nodal analysis (final output)
"""

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from tools.rag_tool import query_well_documents
from tools.extraction_tool import extract_well_parameters
from tools.nodal_tool import run_nodal_analysis


class WellAnalysisOrchestrator:
    """
    Orchestrates end-to-end well performance analysis

    Workflow:
    User query → Agent decides → Tools (RAG/Extract/Analyze) → Response

    Example queries:
    - "Analyze the performance of Well 5"
    - "What is the flow rate for NLW-GT-03?"
    - "Extract casing data and run nodal analysis for Well 5"
    """

    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        temperature: float = 0.1
    ):
        # Initialize Ollama model
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature
        )

        # Define tools
        self.tools = [
            query_well_documents,
            extract_well_parameters,
            run_nodal_analysis
        ]

        # Create ReAct agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self._get_system_prompt()
        )

    def _get_system_prompt(self) -> str:
        return """You are a well performance analysis expert for geothermal wells.

Your capabilities:
1. Query well documents (completion reports, technical logs, etc.)
2. Extract structured casing data (MD, TVD, ID)
3. Run nodal analysis to calculate flow rates

WORKFLOW FOR WELL ANALYSIS:
1. Use query_well_documents to understand the well
2. Use extract_well_parameters to get MD, TVD, ID
3. Use run_nodal_analysis with the extracted data
4. Summarize results for the user

IMPORTANT:
- Always extract parameters before running nodal analysis
- Cite document sources when answering questions
- If extraction fails, ask user for clarification
- Keep responses concise and technical

TARGET: Complete analysis in ≤3 tool calls."""

    def analyze(self, user_query: str) -> dict:
        """
        Run well analysis based on user query

        Args:
            user_query: Natural language query (e.g., "Analyze Well 5 performance")

        Returns:
            {
                'messages': [...],  # Full conversation history
                'output': str,      # Final response
                'tool_calls': int   # Number of tools used
            }
        """
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        messages = result['messages']
        final_message = messages[-1]

        # Count tool calls
        tool_calls = sum(
            1 for msg in messages
            if hasattr(msg, 'tool_calls') and msg.tool_calls
        )

        return {
            'messages': messages,
            'output': final_message.content,
            'tool_calls': tool_calls
        }

    def stream_analyze(self, user_query: str):
        """
        Stream well analysis responses

        Yields:
            Step-by-step agent actions and outputs
        """
        for step in self.agent.stream(
            {"messages": [{"role": "user", "content": user_query}]},
            stream_mode="values"
        ):
            yield step


# Example usage
if __name__ == '__main__':
    orchestrator = WellAnalysisOrchestrator()

    # Test query
    result = orchestrator.analyze(
        "Extract the casing completion data for Well 5 and run nodal analysis"
    )

    print(f"Tool calls: {result['tool_calls']}")
    print(f"Response:\n{result['output']}")
```

---

## Testing Strategy

### Unit Tests

**File: `tests/test_extraction_agent.py`**

```python
"""Unit tests for Pydantic AI extraction agent"""

import pytest
from pydantic_ai.models.function import FunctionModel
from extraction_agent import WellParameterExtractor
from models.well_data import WellCompletionData


@pytest.mark.asyncio
async def test_extraction_with_mock():
    """Test extraction with mocked LLM responses"""

    def mock_llm(messages, info):
        # Return hardcoded valid extraction
        return {
            'well_name': 'Test Well',
            'sections': [
                {'measured_depth': 0, 'true_vertical_depth': 0, 'inner_diameter': 0.340},
                {'measured_depth': 500, 'true_vertical_depth': 500, 'inner_diameter': 0.245},
                {'measured_depth': 1500, 'true_vertical_depth': 1500, 'inner_diameter': 0.178}
            ]
        }

    extractor = WellParameterExtractor()

    # Override with mock
    with extractor.agent.override(model=FunctionModel(mock_llm)):
        result = await extractor.extract('Test Well', mock_rag_system)

    assert isinstance(result, WellCompletionData)
    assert len(result.sections) == 3
    assert result.sections[0].measured_depth == 0


def test_physics_validators():
    """Test that physics validators catch errors"""
    from models.validators import validate_depth_relationship
    from pydantic_ai import ModelRetry

    # Should raise ModelRetry when MD < TVD
    with pytest.raises(ModelRetry):
        validate_depth_relationship(md=100, tvd=150)

    # Should pass when MD >= TVD
    validate_depth_relationship(md=150, tvd=100)  # OK
```

### Integration Tests

**File: `tests/test_orchestrator.py`**

```python
"""Integration tests for LangGraph orchestrator"""

import pytest
from orchestrator_agent import WellAnalysisOrchestrator


def test_end_to_end_workflow():
    """Test complete workflow: query → extract → analyze"""

    orchestrator = WellAnalysisOrchestrator()

    result = orchestrator.analyze(
        "Extract casing data for Well 5 and calculate flow rate"
    )

    # Verify workflow completed
    assert result['tool_calls'] <= 3  # Target: ≤3 tool calls
    assert 'flow_rate' in result['output'].lower()

    # Verify tools were called in order
    messages = result['messages']
    tool_names = [
        msg.tool_calls[0]['name']
        for msg in messages
        if hasattr(msg, 'tool_calls') and msg.tool_calls
    ]

    assert 'extract_well_parameters' in tool_names
    assert 'run_nodal_analysis' in tool_names
```

---

## Timeline & Milestones

### Week 1: Sub-Challenge 1 (RAG - 50%)

**Days 1-2: Setup & Testing**
- ✅ ChromaDB indexed (already done)
- ⬜ Test RAG queries on all 8 wells
- ⬜ Measure accuracy, tune chunk size/overlap

**Days 3-4: Integration**
- ⬜ Wrap RAG in LangChain tool
- ⬜ Test with Ollama Llama 3.2 3B
- ⬜ Optimize temperature (0.1 for factual answers)

**Target:** <10s per query, >90% accuracy

---

### Week 2: Sub-Challenge 2 (Extraction - 20%)

**Days 5-7: Pydantic AI Implementation**
- ⬜ Define Pydantic models (Day 5, 2h)
- ⬜ Implement extraction agent (Days 5-6, 8h)
- ⬜ Add physics validators (Day 6, 2h)
- ⬜ Test on all 8 wells (Day 7, 4h)

**Days 8-9: Validation & Export**
- ⬜ Test ModelRetry mechanism
- ⬜ Verify NodalAnalysis.py format
- ⬜ Measure accuracy vs manual extraction

**Target:** <15s per well, <5% error vs manual

---

### Week 3: Sub-Challenge 3 (Agent - 30%)

**Days 10-12: LangGraph Implementation**
- ⬜ Create tools (Day 10, 4h)
- ⬜ Implement orchestrator (Day 11, 6h)
- ⬜ Test workflow (Day 12, 4h)

**Days 13-14: Optimization**
- ⬜ Optimize for ≤3 tool calls
- ⬜ Add error recovery
- ⬜ End-to-end testing on all wells

**Target:** <30s end-to-end, >95% success rate, ≤3 tool calls

---

### Week 4: Polish & Submission

**Days 15-17: Testing & Documentation**
- ⬜ Comprehensive test suite
- ⬜ Performance benchmarks
- ⬜ README with setup instructions

**Days 18-19: Demo Preparation**
- ⬜ Demo script
- ⬜ Video recording (<10 min)
- ⬜ Handle edge cases

**Day 20: Submission**
- ⬜ Final testing
- ⬜ Package submission
- ⬜ Submit before deadline

---

## Dependencies

```bash
# Install all required packages
pip install \
    langgraph \
    langchain-ollama \
    pydantic-ai \
    pydantic \
    chromadb \
    sentence-transformers \
    docling \
    pytest \
    pytest-asyncio
```

**Verify Ollama:**
```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b "Test message"
```

---

## Performance Targets

| Sub-Challenge | Target Time | Target Accuracy | Grading Weight |
|--------------|-------------|-----------------|----------------|
| 1. RAG | <10s per query | >90% | 50% |
| 2. Extraction | <15s per well | <5% error | 20% |
| 3. Agent | <30s end-to-end | >95% success | 30% |
| **TOTAL** | **<45s** | **>90% overall** | **100%** |

---

## Risk Mitigation

### Risk 1: Pydantic AI + Ollama Integration Issues
**Mitigation:** Fallback to LangChain PydanticOutputParser if needed
```python
# Fallback code
from langchain_core.output_parsers import PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=WellCompletionData)
```

### Risk 2: LangGraph Tool Calling with Local Models
**Mitigation:** Extensive testing, manual tool routing if needed

### Risk 3: Time Constraints
**Mitigation:**
- Week 1: RAG working (50% secured)
- Week 2: Extraction working (70% secured)
- Week 3: Agent working (100% if time allows)

---

## Success Criteria

### Minimum Viable Product (MVP):
- ✅ Sub-Challenge 1: RAG queries working
- ✅ Sub-Challenge 2: Manual parameter extraction (fallback)
- ⚠️ Sub-Challenge 3: Basic workflow (may not be optimal)

### Target Solution:
- ✅ Sub-Challenge 1: RAG with high accuracy
- ✅ Sub-Challenge 2: Pydantic AI with validation
- ✅ Sub-Challenge 3: LangGraph orchestration (≤3 tool calls)

### Stretch Goals:
- ✅ All above +
- ✅ Vision model for diagrams
- ✅ Multi-modal fusion

---

## Next Steps

1. **Wait for reindex to complete** (currently 43%, ETA ~2 hours)
2. **Install dependencies:**
   ```bash
   pip install langgraph langchain-ollama pydantic-ai
   ```
3. **Implement Phase 1:** Shared Pydantic models
4. **Test Ollama integration** with both frameworks
5. **Begin Sub-Challenge 2** implementation (Pydantic AI)

---

## Summary

**Hybrid Approach Benefits:**
- ✅ Best structured output (Pydantic AI)
- ✅ Best agent orchestration (LangGraph)
- ✅ Type safety + Automatic validation
- ✅ Production-ready patterns
- ✅ Lower risk (proven tools)

**Key Insight:** Use each framework for what it does best rather than forcing one to do everything.
