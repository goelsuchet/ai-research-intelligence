from textblob import TextBlob
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np
import logging

# Configure logger
logger = logging.getLogger("QualEngine")

class QualEvidenceEngine:
    def __init__(self):
        """
        Initializes NLP model for semantic clustering and evidence extraction.
        """
        self.model = None
        try:
            # We use a lightweight model for speed
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ NLP Model Loaded: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"⚠️ Warning: SentenceTransformer model failed to load: {e}")

    # =========================================================================
    # 🗣️ GOAL 1: CONSUMER PROBLEM & DEMAND VALIDATION
    # =========================================================================
    
    def extract_core_problems(self, verbatims):
        """Clusters feedback semantically to identify dominant problem statements."""
        if not verbatims or len(verbatims) == 0:
            return [{"problem": "No text data provided", "frequency": 0.0}]

        if not self.model:
            return [{"problem": "NLP Model Unavailable", "frequency": 0.0}]
            
        try:
            embeddings = self.model.encode(verbatims)
            num_clusters = min(len(verbatims), 3)
            if num_clusters < 1:
                return []

            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10).fit(embeddings)
            
            problems = []
            for i in range(num_clusters):
                freq = np.mean(kmeans.labels_ == i)
                problems.append({"problem": f"Problem Theme {i+1}", "frequency": float(freq)})
            
            return problems
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            return [{"problem": "Error during clustering", "frequency": 0.0}]

    def score_pain_intensity(self, text):
        """Uses sentiment and markers to separate minor annoyances from critical pain."""
        if not text:
            return {"pain_severity_signal": "Unknown", "demand_authenticity": "Weak"}

        analysis = TextBlob(str(text))
        intensity = "High" if analysis.sentiment.polarity < -0.3 else "Low"
        
        return {
            "pain_severity_signal": intensity, 
            "demand_authenticity": "Strong" if intensity == "High" else "Weak",
            "sentiment_score": round(analysis.sentiment.polarity, 2)
        }
