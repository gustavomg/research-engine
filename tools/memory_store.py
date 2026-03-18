import chromadb
import os
import hashlib
from datetime import datetime

MEMORY_DIR = "/home/oracle/research-engine-api-llm/.memory"
COLLECTION_NAME = "research_findings"

def get_client():
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=MEMORY_DIR)

def get_collection():
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

def save_finding(query, content, metadata=None):
    """Guarda un finding en la memoria semántica."""
    collection = get_collection()
    doc_id = hashlib.md5(f"{query}{datetime.now().isoformat()}".encode()).hexdigest()
    meta = {
        "query": query[:200],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "research-engine"
    }
    if metadata:
        meta.update(metadata)
    collection.add(
        documents=[content[:2000]],
        metadatas=[meta],
        ids=[doc_id]
    )
    print(f"💾 Guardado en memoria: {query[:50]}")
    return doc_id

def search_memory(query, top_k=3, min_relevance=0.4):
    """Busca findings relevantes por similitud semántica."""
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, count)
    )
    findings = []
    if results and results["documents"]:
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            relevance = 1 - distance
            if relevance >= min_relevance:
                findings.append({
                    "content": doc,
                    "query": meta.get("query", ""),
                    "date": meta.get("date", ""),
                    "relevance": round(relevance, 2)
                })
    return findings

def format_memory(findings):
    """Formatea los findings para incluir en el prompt."""
    if not findings:
        return ""
    formatted = "\n=== CONTEXTO DE INVESTIGACIONES PREVIAS ===\n"
    for i, f in enumerate(findings, 1):
        formatted += f"\n--- Investigación previa {i} "
        formatted += f"(relevancia: {f['relevance']}, fecha: {f['date']}) ---\n"
        formatted += f"Tema original: {f['query']}\n"
        formatted += f"{f['content'][:500]}\n"
    formatted += "\n=== FIN DEL CONTEXTO PREVIO ===\n"
    return formatted

def memory_stats():
    """Muestra estadísticas de la memoria."""
    collection = get_collection()
    count = collection.count()
    print(f"Memoria semántica: {count} findings almacenados")
    return count

if __name__ == "__main__":
    print("Probando Memory Store...")
    save_finding(
        "AI agents architecture",
        "Multi-agent systems consist of autonomous agents that perceive their environment and act to achieve goals.",
        {"test": "true"}
    )
    results = search_memory("autonomous systems coordination")
    print(f"Resultados encontrados: {len(results)}")
    for r in results:
        print(f"  Relevancia {r['relevance']}: {r['content'][:80]}")
