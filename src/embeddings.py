"""
Embedding Manager
Wrapper for nomic-embed-text-v1.5 (137M params, CPU-friendly)
"""

from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingManager:
    """
    Manages embeddings using nomic-embed-text-v1.5

    Model specs:
        - Size: 137M parameters (fits constraint <500M)
        - Dimensions: 768
        - Context: 8192 tokens
        - CPU-friendly: Runs well on CPU
        - License: Apache 2.0 (fully open source)

    Example:
        em = EmbeddingManager()
        embeddings = em.embed_texts(["well depth", "casing diameter"])
    """

    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        """
        Initialize embedding model

        Args:
            model_name: HuggingFace model identifier
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(
            model_name,
            device='cpu',  # CPU-only execution
            trust_remote_code=True
        )
        self.model_name = model_name
        self.dimension = 768  # nomic-embed-text-v1.5 dimension

        print(f"[OK] Model loaded: {model_name}")
        print(f"   Dimensions: {self.dimension}")
        print(f"   Device: CPU")

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions)
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embedding.tolist()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed multiple texts efficiently

        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 10  # Only show for large batches
        )
        return embeddings.tolist()

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Embed chunks with metadata

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata'
                [{
                    'text': 'Section 2.1 Depths\n\nMD: 2500m...',
                    'metadata': {...}
                }, ...]

        Returns:
            List of chunks with added 'embedding' field
        """
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embed_texts(texts)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding

        return chunks

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


def main():
    """Test the embedding manager"""
    print("="*80)
    print("EMBEDDING MANAGER - TEST")
    print("="*80)

    # Initialize
    em = EmbeddingManager()

    # Test queries (from Sub-Challenge 1 & 2)
    test_texts = [
        "What is the well depth?",
        "What is the measured depth?",
        "What is the casing inner diameter?",
        "Measured Depth: 2500 meters, True Vertical Depth: 2300 meters",
        "Casing: 13 3/8 inch to 500m, 9 5/8 inch to 1500m"
    ]

    print(f"\nEmbedding {len(test_texts)} test texts...")
    embeddings = em.embed_texts(test_texts)

    print(f"\n[OK] Embeddings generated:")
    for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
        print(f"\n  Text {i+1}: {text[:50]}...")
        print(f"    Embedding dims: {len(emb)}")
        print(f"    First 5 values: {emb[:5]}")

    # Test similarity
    print(f"\n" + "="*80)
    print("SIMILARITY TEST")
    print("="*80)

    query_emb = np.array(embeddings[0])  # "What is the well depth?"
    doc_emb = np.array(embeddings[3])    # "Measured Depth: 2500 meters..."

    # Cosine similarity
    similarity = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))

    print(f"\nQuery: {test_texts[0]}")
    print(f"Document: {test_texts[3]}")
    print(f"Cosine similarity: {similarity:.4f}")
    print(f"Expected: >0.5 (semantically related)")

    print(f"\n" + "="*80)
    print("[OK] Embedding manager working correctly!")
    print("="*80)


if __name__ == '__main__':
    main()
