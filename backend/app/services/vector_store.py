"""
Unified Vector Store Abstraction.
Provides a consistent interface for vector storage with dual-write capability.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import json
import logging
from datetime import datetime

from app.database import Database

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector storage implementations."""
    
    @abstractmethod
    async def store(
        self,
        agent_id: str,
        vectors: np.ndarray,
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Store vectors with associated IDs and optional metadata."""
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        agent_id: str,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Retrieve top-k similar vectors. Returns list of (id, score, metadata)."""
        pass
    
    @abstractmethod
    async def delete(self, agent_id: str, ids: Optional[List[str]] = None) -> int:
        """Delete vectors by ID. If ids is None, delete all for agent."""
        pass
    
    @abstractmethod
    async def count(self, agent_id: str) -> int:
        """Count vectors for an agent."""
        pass


class MongoDBVectorStore(VectorStore):
    """MongoDB-based vector storage using document embeddings."""
    
    def __init__(self, collection_name: str = "vectors"):
        self.collection_name = collection_name
    
    async def _get_collection(self):
        db = Database.get_db()
        return db[self.collection_name]
    
    async def store(
        self,
        agent_id: str,
        vectors: np.ndarray,
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        collection = await self._get_collection()
        metadata = metadata or [{} for _ in ids]
        
        documents = []
        for i, (vec_id, vector) in enumerate(zip(ids, vectors)):
            documents.append({
                "agent_id": agent_id,
                "vector_id": vec_id,
                "embedding": vector.tolist(),
                "metadata": metadata[i] if i < len(metadata) else {},
                "created_at": datetime.utcnow()
            })
        
        # Upsert to handle re-training
        from pymongo import UpdateOne
        ops = [
            UpdateOne(
                {"agent_id": agent_id, "vector_id": doc["vector_id"]},
                {"$set": doc},
                upsert=True
            )
            for doc in documents
        ]
        
        if ops:
            result = await collection.bulk_write(ops, ordered=False)
            logger.info(f"💾 Stored {len(ops)} vectors for agent '{agent_id}' in MongoDB")
            return {
                "stored": len(ops),
                "upserted": result.upserted_count,
                "modified": result.modified_count
            }
        return {"stored": 0}
    
    async def retrieve(
        self,
        agent_id: str,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        collection = await self._get_collection()
        
        cursor = collection.find({"agent_id": agent_id})
        docs = await cursor.to_list(length=None)
        
        if not docs:
            return []
        
        # Calculate similarities
        query_vec = np.array(query_vector).flatten()
        results = []
        
        for doc in docs:
            doc_vec = np.array(doc["embedding"])
            # Cosine similarity (assuming normalized vectors)
            similarity = float(np.dot(query_vec, doc_vec))
            results.append((
                doc["vector_id"],
                similarity,
                doc.get("metadata", {})
            ))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    async def delete(self, agent_id: str, ids: Optional[List[str]] = None) -> int:
        collection = await self._get_collection()
        
        if ids is None:
            result = await collection.delete_many({"agent_id": agent_id})
        else:
            result = await collection.delete_many({
                "agent_id": agent_id,
                "vector_id": {"$in": ids}
            })
        
        logger.info(f"🗑️ Deleted {result.deleted_count} vectors for agent '{agent_id}'")
        return result.deleted_count
    
    async def count(self, agent_id: str) -> int:
        collection = await self._get_collection()
        return await collection.count_documents({"agent_id": agent_id})


class FileVectorStore(VectorStore):
    """File-based vector storage for persistence and versioning."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_agent_dir(self, agent_id: str) -> Path:
        agent_dir = self.base_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir
    
    async def store(
        self,
        agent_id: str,
        vectors: np.ndarray,
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        agent_dir = self._get_agent_dir(agent_id)
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save embeddings
        embeddings_path = agent_dir / f"embeddings_{version}.npy"
        np.save(embeddings_path, vectors)
        
        # Save IDs and metadata
        ids_path = agent_dir / f"ids_{version}.json"
        data = {
            "ids": ids,
            "metadata": metadata or [{} for _ in ids],
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "count": len(ids),
            "embedding_dim": vectors.shape[1] if len(vectors.shape) > 1 else 0
        }
        with open(ids_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update latest pointer
        latest_path = agent_dir / "latest.json"
        with open(latest_path, 'w') as f:
            json.dump({
                "version": version,
                "embeddings_file": f"embeddings_{version}.npy",
                "ids_file": f"ids_{version}.json",
                **data
            }, f, indent=2)
        
        logger.info(f"💾 Stored {len(ids)} vectors for agent '{agent_id}' to files (v{version})")
        return {"stored": len(ids), "version": version, "path": str(embeddings_path)}
    
    async def retrieve(
        self,
        agent_id: str,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        agent_dir = self._get_agent_dir(agent_id)
        latest_path = agent_dir / "latest.json"
        
        if not latest_path.exists():
            return []
        
        with open(latest_path, 'r') as f:
            latest = json.load(f)
        
        embeddings_path = agent_dir / latest["embeddings_file"]
        ids_path = agent_dir / latest["ids_file"]
        
        if not embeddings_path.exists() or not ids_path.exists():
            return []
        
        vectors = np.load(embeddings_path)
        with open(ids_path, 'r') as f:
            data = json.load(f)
        
        ids = data["ids"]
        metadata_list = data.get("metadata", [{} for _ in ids])
        
        # Calculate similarities
        query_vec = np.array(query_vector).flatten()
        similarities = np.dot(vectors, query_vec)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append((
                ids[idx],
                float(similarities[idx]),
                metadata_list[idx] if idx < len(metadata_list) else {}
            ))
        
        return results
    
    async def delete(self, agent_id: str, ids: Optional[List[str]] = None) -> int:
        agent_dir = self._get_agent_dir(agent_id)
        
        if ids is None:
            # Delete all files for agent
            import shutil
            if agent_dir.exists():
                count = len(list(agent_dir.glob("*.npy")))
                shutil.rmtree(agent_dir)
                logger.info(f"🗑️ Deleted all vectors for agent '{agent_id}'")
                return count
        
        # Partial deletion not supported for file store - would need to reload and rewrite
        logger.warning("Partial deletion not supported for FileVectorStore")
        return 0
    
    async def count(self, agent_id: str) -> int:
        agent_dir = self._get_agent_dir(agent_id)
        latest_path = agent_dir / "latest.json"
        
        if not latest_path.exists():
            return 0
        
        with open(latest_path, 'r') as f:
            latest = json.load(f)
        
        return latest.get("count", 0)
    
    def list_versions(self, agent_id: str) -> List[Dict[str, Any]]:
        """List all stored versions for an agent."""
        agent_dir = self._get_agent_dir(agent_id)
        versions = []
        
        for f in sorted(agent_dir.glob("ids_*.json"), reverse=True):
            with open(f, 'r') as file:
                data = json.load(file)
                versions.append({
                    "version": data.get("version"),
                    "count": data.get("count"),
                    "created_at": data.get("created_at")
                })
        
        return versions
    
    async def rollback(self, agent_id: str, version: str) -> bool:
        """Rollback to a specific version."""
        agent_dir = self._get_agent_dir(agent_id)
        
        embeddings_path = agent_dir / f"embeddings_{version}.npy"
        ids_path = agent_dir / f"ids_{version}.json"
        
        if not embeddings_path.exists() or not ids_path.exists():
            return False
        
        with open(ids_path, 'r') as f:
            data = json.load(f)
        
        # Update latest pointer
        latest_path = agent_dir / "latest.json"
        with open(latest_path, 'w') as f:
            json.dump({
                "version": version,
                "embeddings_file": f"embeddings_{version}.npy",
                "ids_file": f"ids_{version}.json",
                **data
            }, f, indent=2)
        
        logger.info(f"⏪ Rolled back agent '{agent_id}' to version {version}")
        return True


class DualWriteVectorStore(VectorStore):
    """
    Dual-write vector store that writes to both MongoDB and files.
    Provides redundancy and enables versioning while maintaining query performance.
    """
    
    def __init__(self, mongo_store: MongoDBVectorStore, file_store: FileVectorStore):
        self.mongo = mongo_store
        self.file = file_store
    
    async def store(
        self,
        agent_id: str,
        vectors: np.ndarray,
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        # Write to both stores
        mongo_result = await self.mongo.store(agent_id, vectors, ids, metadata)
        file_result = await self.file.store(agent_id, vectors, ids, metadata)
        
        return {
            "mongo": mongo_result,
            "file": file_result,
            "total_stored": len(ids)
        }
    
    async def retrieve(
        self,
        agent_id: str,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        # Prefer MongoDB for faster retrieval
        results = await self.mongo.retrieve(agent_id, query_vector, top_k)
        
        # Fallback to file if MongoDB empty
        if not results:
            results = await self.file.retrieve(agent_id, query_vector, top_k)
        
        return results
    
    async def delete(self, agent_id: str, ids: Optional[List[str]] = None) -> int:
        mongo_count = await self.mongo.delete(agent_id, ids)
        file_count = await self.file.delete(agent_id, ids)
        return max(mongo_count, file_count)
    
    async def count(self, agent_id: str) -> int:
        return await self.mongo.count(agent_id)
    
    def list_versions(self, agent_id: str) -> List[Dict[str, Any]]:
        """List versions from file store."""
        return self.file.list_versions(agent_id)
    
    async def rollback(self, agent_id: str, version: str) -> bool:
        """Rollback to a specific version, reloading into MongoDB."""
        success = await self.file.rollback(agent_id, version)
        
        if success:
            # Reload into MongoDB from file
            agent_dir = self.file._get_agent_dir(agent_id)
            latest_path = agent_dir / "latest.json"
            
            with open(latest_path, 'r') as f:
                latest = json.load(f)
            
            embeddings = np.load(agent_dir / latest["embeddings_file"])
            with open(agent_dir / latest["ids_file"], 'r') as f:
                data = json.load(f)
            
            # Clear and reload MongoDB
            await self.mongo.delete(agent_id)
            await self.mongo.store(agent_id, embeddings, data["ids"], data.get("metadata"))
        
        return success


# Factory functions
_mongo_store: Optional[MongoDBVectorStore] = None
_file_store: Optional[FileVectorStore] = None
_dual_store: Optional[DualWriteVectorStore] = None


def get_vector_store(store_type: str = "dual") -> VectorStore:
    """
    Get vector store instance.
    
    Args:
        store_type: 'mongo', 'file', or 'dual' (default)
    """
    global _mongo_store, _file_store, _dual_store
    
    if _mongo_store is None:
        _mongo_store = MongoDBVectorStore("agent_vectors")
    
    if _file_store is None:
        from pathlib import Path
        base_dir = Path(__file__).parent.parent / "models_data"
        _file_store = FileVectorStore(base_dir)
    
    if store_type == "mongo":
        return _mongo_store
    elif store_type == "file":
        return _file_store
    else:
        if _dual_store is None:
            _dual_store = DualWriteVectorStore(_mongo_store, _file_store)
        return _dual_store
