import os
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer

class MemoryManager:
    """
    Manages storing and querying paper summaries in a local vector database
    using ChromaDB and SentenceTransformers.
    """
    def __init__(self, db_path: str = "data/chroma_db", collection_name: str = "research_memories"):
        # Ensure database directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
        # Load local SentenceTransformer embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def _parse_summary_sections(self, summary_text: str) -> Dict[str, str]:
        """
        Parses structured summary text and splits it by markdown headers.
        """
        sections = {}
        current_section = None
        lines = summary_text.split("\n")
        for line in lines:
            if line.startswith("## "):
                sec_name = line.replace("## ", "").strip().lower()
                # Match standard sections
                for standard in ["objective", "method", "dataset", "results", "limitations"]:
                    if standard in sec_name:
                        current_section = standard
                        sections[current_section] = []
                        break
            elif current_section is not None:
                sections[current_section].append(line)
                
        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def add_paper(self, paper_id: str, title: str, summary: str, filename: str = "") -> None:
        """
        Embed the summary and store it in ChromaDB along with metadata.
        Also parses and stores individual sub-sections for granular semantic search.
        """
        # Embed the full summary text
        embedding = self.model.encode(summary).tolist()
        
        metadata_full = {
            "title": title,
            "filename": filename,
            "type": "full"
        }
        
        # Upsert full summary into ChromaDB
        self.collection.upsert(
            ids=[paper_id],
            embeddings=[embedding],
            metadatas=[metadata_full],
            documents=[summary]
        )
        print(f"MemoryManager: Stored paper '{title}' (ID: {paper_id}) as full record.")
        
        # Parse and upsert individual sections as granular chunks
        sections = self._parse_summary_sections(summary)
        for sec_name, sec_text in sections.items():
            if sec_text:
                sec_id = f"{paper_id}_{sec_name}"
                sec_embedding = self.model.encode(sec_text).tolist()
                metadata_sec = {
                    "title": title,
                    "filename": filename,
                    "type": "chunk",
                    "section": sec_name
                }
                self.collection.upsert(
                    ids=[sec_id],
                    embeddings=[sec_embedding],
                    metadatas=[metadata_sec],
                    documents=[sec_text]
                )
                print(f"MemoryManager: Stored sub-chunk '{sec_id}' for section '{sec_name}'.")

    def get_all_papers(self) -> List[Dict[str, Any]]:
        """
        Retrieve all stored papers (full summaries only) in the collection.
        """
        results = self.collection.get(where={"type": "full"})
        papers = []
        if results and "ids" in results:
            for idx, paper_id in enumerate(results["ids"]):
                papers.append({
                    "id": paper_id,
                    "title": results["metadatas"][idx].get("title", "Unknown"),
                    "filename": results["metadatas"][idx].get("filename", ""),
                    "summary": results["documents"][idx]
                })
        return papers

    def search_similar_papers(self, query_summary: str, exclude_id: str = "", limit: int = 3) -> List[Dict[str, Any]]:
        """
        Query ChromaDB for similar summaries and return metadata and text.
        Restricted to full summary records to preserve comparative analysis mapping.
        """
        # Embed the query summary
        query_embedding = self.model.encode(query_summary).tolist()
        
        # Query database with metadata filter for full summaries
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit + 2,  # Fetch extra to accommodate exclusions
            where={"type": "full"}
        )
        
        similar_papers = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]
            
            for doc, meta, paper_id in zip(docs, metas, ids):
                if paper_id == exclude_id or paper_id.startswith(f"{exclude_id}_"):
                    continue
                similar_papers.append({
                    "id": paper_id,
                    "title": meta.get("title", "Unknown Title"),
                    "filename": meta.get("filename", ""),
                    "summary": doc
                })
                
        # Limit to the requested size
        return similar_papers[:limit]

    def search_chunks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query ChromaDB for similar section chunks and return metadata and text.
        Restricted to records of type='chunk'.
        """
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"type": "chunk"}
        )
        similar_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]
            for doc, meta, chunk_id in zip(docs, metas, ids):
                similar_chunks.append({
                    "id": chunk_id,
                    "title": meta.get("title", "Unknown Title"),
                    "filename": meta.get("filename", ""),
                    "section": meta.get("section", ""),
                    "content": doc
                })
        return similar_chunks
