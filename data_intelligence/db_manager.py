import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import logging

logger = logging.getLogger("VectorDBManager")

class VectorDBManager:
    def __init__(self, db_path="data_intelligence/vector_db"):
        """
        Initializes the Vector DB in the designated folder.
        This folder acts as the 'Hard Drive' for indexed consumer intelligence.
        """
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Using a standard embedding function for B2C verbatims and pain language
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # 'research_data' is the canonical collection for all 7 goals
        self.collection = self.client.get_or_create_collection(
            name="research_data", 
            embedding_function=self.emb_fn
        )

    def ingest_csv(self, df, file_path, active_goal):
        """
        Automatically detects text columns and embeds them into ChromaDB.
        """
        text_cols = [c for c in df.columns if c.lower() in ["feedback_text", "verbatim", "review", "comment"]]
        if not text_cols:
            return

        # Clear old data for this file
        self.delete_research_collection()

        docs = []
        metadatas = []
        ids = []

        for col in text_cols:
            for idx, row in df.iterrows():
                text = str(row[col])
                if pd.isna(row[col]) or not text.strip():
                    continue
                
                docs.append(text)
                
                meta = {
                    "goal": active_goal,
                    "source_file": file_path,
                    "row_id": str(idx),
                    "column": col
                }
                
                # Optional: Capture segment if available
                if "segment" in df.columns:
                    meta["segment"] = str(row["segment"])
                    
                metadatas.append(meta)
                ids.append(f"{file_path}_{col}_{idx}")

        if docs:
            logger.info(f"Ingesting {len(docs)} text snippets into VectorDB...")
            self.collection.add(documents=docs, metadatas=metadatas, ids=ids)

    def query_evidence(self, user_query, n_results=3):
        """
        Retrieves grounded evidence based on semantic similarity.
        Used to find quotes that explain problems clearly for the Synthesis Engine.
        """
        if self.collection.count() == 0:
            return {"documents": [[]]}
            
        results = self.collection.query(
            query_texts=[user_query],
            n_results=n_results
        )
        return results

    def query_by_segment(self, user_query, segment_name, n_results=3):
        """
        Filters evidence by specific user segments.
        Ensures research is journey-aware and platform-aware.
        """
        if self.collection.count() == 0:
            return {"documents": [[]]}

        results = self.collection.query(
            query_texts=[user_query],
            where={"segment": segment_name},
            n_results=n_results
        )
        return results

    def delete_research_collection(self):
        """
        Utility for demo safety and resetting research data between goals.
        """
        try:
            self.client.delete_collection(name="research_data")
        except Exception:
            pass # Collection might not exist yet
        self.collection = self.client.get_or_create_collection(
            name="research_data", 
            embedding_function=self.emb_fn
        )