# Scanned Document Processing Strategy

**Date:** 2025-11-12
**Status:** Approved Implementation Plan

---

## Overview

Definitive approach for processing scanned well reports (image-based PDFs) with optimal extraction quality and LangChain integration.

---

## Architecture Components

### 1. Granite VLM for Picture Descriptions

**Decision:** Use Granite-Docling-258M VLM instead of SmolVLM-256M for all visual content.

**Rationale:**
- **Consistency:** Granite already proven in TOC extraction (scripts/build_structure_only_database_parallel.py)
- **Memory efficiency:** Single model for both TOC and pictures (258M params)
- **Document-specific:** Granite fine-tuned specifically for document understanding
- **Performance:** Already optimized and validated in parallel processing pipeline

**Implementation:**
- Current: SmolVLM via `smolvlm_picture_description` (scripts/enhanced_well7_parser.py:98)
- Future: Custom Granite VLM configuration for picture descriptions
- Reference: `src/granite_toc_extractor.py` for VlmPipeline usage pattern

**Custom Configuration Required:**
```python
# Create custom Granite picture description provider
from docling.datamodel.pipeline_options import VlmPictureDescriptionOptions
from docling.backend.vlm_backend import GraniteVlmBackend

granite_picture_description = VlmPictureDescriptionOptions(
    backend=GraniteVlmBackend(model_id="granite-vision-3.0-2b-preview"),
    prompt=(
        "Describe this diagram or figure in detail. "
        "Include all visible text, labels, measurements, annotations, and handwritten notes. "
        "Mention axes, legends, and any technical information shown."
    )
)

pipeline_options.do_picture_description = True
pipeline_options.picture_description_options = granite_picture_description
```

---

### 2. HierarchicalChunker for Structure Detection

**Decision:** Use Docling's `HierarchicalChunker` for automatic structure-aware chunking.

**Key Advantage:** Automatically detects document structure WITHOUT requiring page numbers!

**How It Works:**
```python
from docling_core.transforms.chunker import HierarchicalChunker

# Initialize
chunker = HierarchicalChunker(
    tokenizer=tokenizer,
    serializer_provider=MDTableSerializerProvider(),
)

# Chunk document (automatic structure detection)
chunks = list(chunker.chunk(dl_doc=doc))

# Each chunk contains:
chunk.text                    # Text content
chunk.meta.headings          # ['1. General Data', '1.2 Casing Design'] <-- KEY!
chunk.meta.doc_items         # Document items (paragraphs, tables, pictures)
```

**Automatic Features:**
- ✅ Detects section headings hierarchically
- ✅ Respects document structure (parent-child relationships)
- ✅ Preserves table and picture context
- ✅ No page numbers required
- ✅ Works seamlessly with structure-only TOC

**Reference Implementation:**
- `scripts/enhanced_well7_parser.py:124-128` - Chunker setup
- `scripts/enhanced_well7_parser.py:380-395` - Chunk creation with metadata

---

### 3. Structure-Only TOC Integration

**Decision:** Enrich HierarchicalChunker output with structure-only TOC metadata.

**Synergy:**

| Component | Provides |
|-----------|----------|
| **HierarchicalChunker** | Automatic heading detection: `['1.2 Casing Design']` |
| **Structure-Only TOC** | Semantic categorization: `{'number': '1.2', 'title': 'Casing Design', 'type': 'casing'}` |
| **Combined** | Chunk with full context: section number + title + type (13 categories) |

**Integration Flow:**
```python
# STEP 1: Parse scanned PDF with Docling + Granite VLM
pipeline_options.do_ocr = True
pipeline_options.do_picture_description = True  # Granite VLM
result = converter.convert(pdf_path)
doc = result.document

# STEP 2: Create hierarchical chunks (automatic structure)
chunker = HierarchicalChunker(tokenizer=tokenizer)
chunks = list(chunker.chunk(dl_doc=doc))

# STEP 3: Load structure-only TOC database
with open('outputs/exploration/toc_database_structure_only.json') as f:
    toc_database = json.load(f)

# STEP 4: Enrich chunks with TOC metadata
for chunk in chunks:
    # Match chunk headings to TOC entries
    for heading in chunk.meta.headings:
        matched_entry = match_heading_to_toc(heading, toc_database, well_name, filename)

        if matched_entry:
            # Add semantic metadata
            chunk.metadata['section_number'] = matched_entry['number']
            chunk.metadata['section_title'] = matched_entry['title']
            chunk.metadata['section_type'] = matched_entry['type']  # 13 categories!
            break

# STEP 5: Index to vector store with enriched metadata
vector_store.add_documents(chunks)
```

**13-Category Mapping:**
1. appendices
2. borehole
3. casing
4. completion
5. directional
6. drilling_operations
7. geology
8. hse
9. intervention
10. project_admin
11. technical_summary
12. well_identification
13. well_testing

**Metadata Enrichment:**
```python
# Before (HierarchicalChunker only)
chunk.metadata = {
    'headings': ['1.2 Casing Design']
}

# After (+ Structure-Only TOC)
chunk.metadata = {
    'headings': ['1.2 Casing Design'],
    'section_number': '1.2',
    'section_title': 'Casing Design',
    'section_type': 'casing',           # 13-category semantic type
    'well_name': 'Well 7',
    'filename': 'EOWR_Well7.pdf',
    'filepath': '/path/to/pdf',
    'pub_date': '2018-11-14T00:00:00',
    'has_tables': True,
    'has_pictures': True
}
```

---

## Processing Pipeline for Scanned PDFs

### Phase 1: Document Parsing (Docling + Granite)

```python
# Configure pipeline with all advanced features
pipeline_options = PdfPipelineOptions()

# 1. Enhanced OCR for scanned content
pipeline_options.do_ocr = True

# 2. TableFormer ACCURATE mode
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# 3. Picture extraction with Granite VLM descriptions
pipeline_options.generate_picture_images = True
pipeline_options.do_picture_description = True
pipeline_options.picture_description_options = granite_picture_description  # Custom Granite

# 4. Picture classification
pipeline_options.do_picture_classification = True

# Parse
result = converter.convert(str(pdf_path))
doc = result.document
```

### Phase 2: Hierarchical Chunking

```python
# Setup chunker with custom table serializer
class MDTableSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),  # Better table format
        )

chunker = HierarchicalChunker(
    tokenizer=tokenizer,
    serializer_provider=MDTableSerializerProvider(),
    max_tokens=512,      # Optimal for nomic-embed-text-v1.5
    overlap_tokens=50    # Context overlap
)

# Create chunks (automatic structure detection)
chunks = list(chunker.chunk(dl_doc=doc))
```

### Phase 3: TOC Metadata Enrichment

```python
# Load structure-only TOC database
toc_database = load_toc_database()

# Match chunks to TOC structure
for chunk in chunks:
    # Get chunk headings from HierarchicalChunker
    headings = chunk.meta.headings  # e.g., ['1.2 Casing Design']

    # Find matching TOC entry
    toc_match = find_best_match(headings, toc_database[well_name])

    if toc_match:
        # Enrich with semantic metadata
        chunk.metadata.update({
            'section_number': toc_match['number'],
            'section_title': toc_match['title'],
            'section_type': toc_match['type'],  # 13 categories
        })
```

### Phase 4: Picture-Specific Chunks

```python
# Create dedicated chunks for pictures with Granite VLM descriptions
picture_chunks = []
for item in doc.iterate_items():
    if isinstance(item, PictureItem):
        # Extract Granite VLM description
        description = extract_picture_description(item)  # From Granite VLM

        # Detect handwriting and text labels
        has_handwriting = detect_handwriting(description)
        has_text_labels = detect_text_labels(description)

        # Create picture chunk
        picture_chunk = {
            'text': f"Picture: {item.caption_text(doc)}\n\nDescription: {description}",
            'metadata': {
                'chunk_type': 'picture',
                'picture_ref': str(item.self_ref),
                'description': description,
                'has_handwriting': has_handwriting,
                'has_text_labels': has_text_labels,
                'section_type': 'visual',
                'well_name': well_name,
                'filename': filename
            }
        }
        picture_chunks.append(picture_chunk)
```

### Phase 5: Table Chunking

```python
# Create table-specific chunks
table_chunks = []
for item in doc.iterate_items():
    if isinstance(item, TableItem):
        # Export to markdown via HierarchicalChunker's serializer
        table_md = MarkdownTableSerializer().serialize(item, doc)

        # Extract structured data
        df = item.export_to_dataframe()

        table_chunk = {
            'text': table_md.text,
            'metadata': {
                'chunk_type': 'table',
                'table_ref': str(item.self_ref),
                'num_rows': len(df),
                'num_cols': len(df.columns),
                'column_headers': list(df.columns),
                'caption': item.caption_text(doc),
                'well_name': well_name,
                'filename': filename
            }
        }
        table_chunks.append(table_chunk)
```

### Phase 6: Embedding & Indexing

```python
# Combine all chunks
all_chunks = chunks + picture_chunks + table_chunks

# Generate embeddings (nomic-embed-text-v1.5, 137M params)
texts = [chunk['text'] for chunk in all_chunks]
embeddings = embedding_manager.embed_texts(texts)

# Add embeddings to chunks
for chunk, embedding in zip(all_chunks, embeddings):
    chunk['embedding'] = embedding

# Index to ChromaDB vector store
vector_store.add_documents(
    chunks=all_chunks,
    well_name=well_name
)
```

---

## LangChain Integration Benefits

### 1. Query Routing by Section Type

```python
# Route query to relevant section types
if "casing" in query.lower():
    # Filter to casing sections only
    filter = {"section_type": "casing"}
    results = vector_store.similarity_search(query, filter=filter)
```

### 2. Hierarchical Context Retrieval

```python
# Retrieve chunk + parent/child sections
chunk = vector_store.get_chunk(chunk_id)
section_number = chunk.metadata['section_number']  # e.g., '1.2.3'

# Get parent context (1.2)
parent_number = '.'.join(section_number.split('.')[:-1])
parent_chunks = vector_store.query(filter={'section_number': parent_number})

# Get sibling chunks (1.2.x)
sibling_chunks = vector_store.query(filter={'section_number': f"{parent_number}.*"})
```

### 3. Cross-Document Consistency

```python
# Find all "casing design" sections across wells
all_casing_sections = vector_store.query(
    filter={'section_type': 'casing'},
    n_results=100
)

# Group by well for comparison
casing_by_well = {}
for chunk in all_casing_sections:
    well = chunk.metadata['well_name']
    if well not in casing_by_well:
        casing_by_well[well] = []
    casing_by_well[well].append(chunk)
```

### 4. Metadata-Enhanced RAG

```python
# Query with rich context
prompt = f"""
Based on the following context from {chunk.metadata['section_title']}
(Section {chunk.metadata['section_number']}) in {chunk.metadata['well_name']}:

{chunk.text}

Question: {user_question}
"""
```

---

## Performance Characteristics

### Scanned PDF Processing Time

**Based on parallel builder results (scripts/build_structure_only_database_parallel.py):**

| Component | Time per PDF |
|-----------|--------------|
| Docling OCR (5 pages) | 8-25 seconds |
| Granite VLM (TOC page) | 15-30 seconds |
| Total per scanned PDF | 23-55 seconds |

**Parallel Processing:**
- 6 workers on 8-core CPU
- ~6x speedup vs sequential
- 16 PDFs processed in ~8-12 minutes (parallel)

### Chunking Performance

| Component | Speed |
|-----------|-------|
| HierarchicalChunker | Fast (structure-aware, no LLM) |
| TOC matching | O(n) per chunk, negligible |
| Embedding (nomic-embed-text-v1.5) | ~10-20 chunks/sec on CPU |

---

## Implementation Priority

### Phase 1: Structure-Only TOC Database (COMPLETED)
- ✅ Parallel builder with Granite VLM for scanned PDFs
- ✅ 16 PDFs across 8 wells
- ✅ Structure-only extraction (number + title, no page)
- ✅ Output: `outputs/exploration/toc_database_structure_only.json`

### Phase 2: Post-Processing (NEXT)
- ⏳ Add 13-category type mapping to TOC entries
- ⏳ Add key_sections grouping
- ⏳ Convert pub_date to ISO format
- ⏳ Add file_size metadata

### Phase 3: Granite Picture Descriptions (FUTURE)
- ⏳ Create custom Granite VLM configuration for pictures
- ⏳ Replace SmolVLM with Granite in pipeline
- ⏳ Test on scanned PDFs with diagrams

### Phase 4: HierarchicalChunker Integration (FUTURE)
- ⏳ Implement chunking with TOC enrichment
- ⏳ Create picture-specific chunks
- ⏳ Create table-specific chunks
- ⏳ Generate embeddings with nomic-embed-text-v1.5

### Phase 5: LangChain RAG System (FUTURE)
- ⏳ ChromaDB vector store with metadata filtering
- ⏳ Query routing by section type
- ⏳ Hierarchical context retrieval
- ⏳ Cross-document search

---

## Key Design Principles

1. **No Page Numbers Required**
   - HierarchicalChunker detects structure via headings
   - Structure-only TOC provides semantic categorization
   - More reliable than page-number based chunking

2. **Semantic Enrichment**
   - 13-category type system for standardization
   - Cross-document consistency
   - Enables intelligent query routing

3. **Granite VLM Consistency**
   - Single model for TOC and pictures (258M params)
   - Document-specific fine-tuning
   - Memory efficient

4. **Hierarchical Structure Preservation**
   - Parent-child relationships via section numbering
   - Sibling sections easily retrieved
   - Context-aware chunking

5. **Multi-Modal Integration**
   - Text chunks via HierarchicalChunker
   - Picture chunks via Granite VLM
   - Table chunks via TableFormer ACCURATE
   - All indexed with consistent metadata

---

## Success Criteria

### Technical Metrics
- ✅ 100% TOC extraction success (14/14 PDFs achieved)
- ⏳ <30s per scanned PDF processing (Granite + chunking)
- ⏳ >90% heading-to-TOC matching accuracy
- ⏳ <10s RAG query response time

### Quality Metrics
- ⏳ Semantic type accuracy >95% (13 categories)
- ⏳ Picture description relevance >90%
- ⏳ Table extraction completeness >95%
- ⏳ Cross-document retrieval precision >85%

---

## References

### Scripts
- `scripts/build_structure_only_database_parallel.py` - Parallel TOC extraction
- `scripts/enhanced_well7_parser.py` - HierarchicalChunker implementation
- `scripts/reindex_all_wells_with_toc.py` - TOC-enhanced indexing
- `src/granite_toc_extractor.py` - Granite VLM integration

### Databases
- `outputs/exploration/toc_database_structure_only.json` - Structure-only TOC database
- `outputs/exploration/toc_database_multi_doc_full.json` - Full TOC database (with pages)
- `outputs/final_section_categorization_v2.json` - 13-category mapping

### Documentation
- `.claude/tasks/multi-doc-toc-database-implementation.md` - TOC database design
- Docling docs: https://docling-project.github.io/docling/
- HierarchicalChunker: Advanced chunking and serialization

---

## Notes

- **Model Size Constraint:** All models <500M params (Granite 258M ✅, nomic-embed 137M ✅)
- **CPU-Only:** No GPU required, optimized for CPU execution
- **Open Source:** All components MIT/Apache licensed
- **Data Security:** Fully local execution, no external APIs
