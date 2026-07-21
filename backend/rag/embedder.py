import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from sentence_transformers import SentenceTransformer
from core.config import CHROMA_DIR, EMBEDDING_MODEL


# Initialize embedding model
# This downloads the model first time (~90MB), then caches it
print("Loading embedding model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
print("[OK] Embedding model loaded")


def get_chroma_client():
    """
    Create and return a ChromaDB client.
    PersistentClient saves data to disk so it 
    survives between restarts.
    """
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client


def get_or_create_collection(client, collection_name: str = "samarth_docs"):
    """
    Get existing collection or create new one.
    A collection is like a table in ChromaDB.
    """
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def get_chunks_by_source(source_filename: str, n_results: int = 5) -> list:
    """
    Directly fetch chunks from a specific source document, bypassing
    semantic search entirely. Use this when you need guaranteed inclusion
    of a known-relevant document (e.g., an OEM manual), regardless of
    how well the query wording happens to match it semantically.
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    results = collection.get(
        where={"source": source_filename},
        limit=n_results
    )

    chunks = []
    if results and results.get("documents"):
        for doc, meta in zip(results["documents"], results["metadatas"]):
            chunks.append({
                "text": doc,
                "metadata": meta,
                "distance": 0.0  # not applicable for direct fetch
            })
    return chunks

def embed_chunks(chunks: list) -> list:
    """
    Convert text chunks to vectors using sentence-transformers.
    Returns list of embedding vectors.
    """
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32
    )
    return embeddings.tolist()


def store_chunks(chunks: list, collection_name: str = "samarth_docs"):
    """
    Store chunks in ChromaDB with their embeddings and metadata.
    
    ChromaDB needs:
    - ids: unique identifier for each chunk
    - embeddings: vector representation
    - documents: the actual text
    - metadatas: additional info about each chunk
    """
    if not chunks:
        print("No chunks to store")
        return
    
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    
    # Check existing count
    existing = collection.count()
    print(f"Existing documents in collection: {existing}")
    
    # Prepare data for ChromaDB
    ids = [chunk['metadata']['chunk_id'] for chunk in chunks]
    documents = [chunk['text'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    # Generate embeddings
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = embed_chunks(chunks)
    
    # Store in ChromaDB
    # upsert = insert if not exists, update if exists
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    new_count = collection.count()
    print(f"✅ Collection now has {new_count} documents")


def search_similar(query: str, n_results: int = 5, 
                   filter_metadata: dict = None,
                   collection_name: str = "samarth_docs") -> list:
    """
    Search for chunks similar to the query.
    This is the core of RAG — finding relevant context.
    
    filter_metadata allows filtering by doc_type, regulatory_body etc.
    Example: filter_metadata={"doc_type": "regulatory"}
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    
    # Convert query to vector
    query_embedding = embedding_model.encode([query]).tolist()
    
    # Search
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=filter_metadata
    )
    
    # Format results
    formatted = []
    for i in range(len(results['documents'][0])):
        formatted.append({
            "text": results['documents'][0][i],
            "metadata": results['metadatas'][0][i],
            "distance": results['distances'][0][i]
        })
    
    return formatted


if __name__ == "__main__":
    from core.config import REGULATORY_DIR, GENERATED_DIR
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from ingestion.pdf_parser import process_pdf
    from ingestion.json_parser import process_all_json_files
    from ingestion.spreadsheet_parser import extract_rows_from_spreadsheet
    from ingestion.pid_parser import drawing_labels_to_chunk

    print("=" * 50)
    print("SAMARTH Embedder Test")
    print("=" * 50)
    
    all_chunks = []
    
    # Process regulatory PDFs
    print("\nProcessing regulatory documents...")
    for filename in os.listdir(REGULATORY_DIR):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(REGULATORY_DIR, filename)
            chunks = process_pdf(pdf_path)
            all_chunks.extend(chunks)

    # Process spreadsheet files (CSV/XLSX) in the regulatory folder
    print("\nProcessing spreadsheet documents...")
    for filename in os.listdir(REGULATORY_DIR):
        if filename.endswith('.csv') or filename.endswith('.xlsx'):
            file_path = os.path.join(REGULATORY_DIR, filename)
            sheet_chunks = extract_rows_from_spreadsheet(file_path)
            all_chunks.extend(sheet_chunks)

    # Process engineering drawings (SVG) in the regulatory folder
    print("\nProcessing engineering drawings...")
    for filename in os.listdir(REGULATORY_DIR):
        if filename.endswith('.svg'):
            file_path = os.path.join(REGULATORY_DIR, filename)
            drawing_chunk = drawing_labels_to_chunk(file_path)
            if drawing_chunk:
                all_chunks.append(drawing_chunk)        

    # Process JSON operational data
    print("\nProcessing operational data...")
    json_chunks = process_all_json_files(GENERATED_DIR)
    all_chunks.extend(json_chunks)
    
    print(f"\nTotal chunks to embed: {len(all_chunks)}")
    
    # Store everything
    store_chunks(all_chunks)
    
    # Test search
    print("\nTesting search...")
    results = search_similar("pump seal failure maintenance")
    print(f"\nTop 3 results for 'pump seal failure maintenance':")
    for i, r in enumerate(results[:3]):
        print(f"\n{i+1}. Source: {r['metadata']['source']}")
        print(f"   Text: {r['text'][:150]}...")
        print(f"   Distance: {r['distance']:.4f}")
        