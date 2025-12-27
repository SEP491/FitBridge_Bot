import os
import psycopg2
import dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_neo4j import Neo4jGraph, Neo4jVector
import googlemaps
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global variables for embeddings and model
_EMBEDDINGS: Optional[OpenAIEmbeddings] = None
_MODEL: Optional[ChatOpenAI] = None
_GRAPH: Optional[Neo4jGraph] = None
_PtCertificateVectorIndex: Optional[Neo4jVector] = None
_GOOGLE_MAPS_CLIENT: Optional[googlemaps.Client] = None
_GymAssetVectorIndex: Optional[Neo4jVector] = None
_POSTGRES_CONNECTION = None
_ENV_LOADED = False

def load_env():
    """Load environment variables from .env file."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
        
    # Use override=True to ensure .env values take precedence in development
    env_path = dotenv.find_dotenv()
    if env_path:
        print(f"--- Infrastructure: Force Loading .env from {env_path} ---")
        dotenv.load_dotenv(env_path, override=True)
        
        for key in [
            "LANGSMITH_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", 
            "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", 
            "GOOGLE_MAPS_API_KEY", "CHECKPOINTER_DB_URI", "POSTGRES_DB_URI"
        ]:
            val = dotenv.get_key(env_path, key)
            if val:
                os.environ[key] = val
    else:
        print("--- Infrastructure: .env file not found! ---")
    
    # Set defaults for LangSmith if not already set
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", "fitbridge-chatbot")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    _ENV_LOADED = True
    print("--- Infrastructure: Environment variables initialized ---")

def get_embeddings() -> OpenAIEmbeddings:
    """Get the loaded embeddings model (lazy loaded)."""
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        _EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-large")
        logger.info("OpenAI embeddings loaded successfully.")
    return _EMBEDDINGS

def get_model() -> ChatOpenAI:
    """Get the loaded language model (lazy loaded)."""
    global _MODEL
    if _MODEL is None:
        _MODEL = ChatOpenAI(
            model="gpt-5-mini-2025-08-07",
            temperature=0.3,
        )
        logger.info("OpenAI model loaded successfully.")
    return _MODEL

def get_graph() -> Neo4jGraph:
    """Get the loaded graph database (lazy loaded)."""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = Neo4jGraph(
            url=os.environ.get("NEO4J_URI"),
            username=os.environ.get("NEO4J_USERNAME"),
            password=os.environ.get("NEO4J_PASSWORD")
        )
        logger.info("Graph database loaded successfully.")
    return _GRAPH

def get_PtCertificateVectorIndex() -> Neo4jVector:
    """Get the loaded PtCertificate vector index (lazy loaded)."""
    global _PtCertificateVectorIndex
    if _PtCertificateVectorIndex is None:
        graph = get_graph()
        embeddings = get_embeddings()
        _PtCertificateVectorIndex = Neo4jVector.from_existing_graph(
            embedding=embeddings,
            graph=graph,
            index_name="PtCertificateVectorIndex",
            node_label="Certificates",
            text_node_properties=["certName", "description", "certificateType", "providerName", "certCode"],
            embedding_node_property="embedding"
        )
        logger.info("Certificates vector index loaded successfully.")
    return _PtCertificateVectorIndex

def get_GymAssetVectorIndex() -> Neo4jVector:
    """Get the loaded GymAsset vector index (lazy loaded)."""
    global _GymAssetVectorIndex
    if _GymAssetVectorIndex is None:
        graph = get_graph()
        embeddings = get_embeddings()
        _GymAssetVectorIndex = Neo4jVector.from_existing_graph(
            embedding=embeddings,
            graph=graph,
            index_name="GymAssetVectorIndex",
            node_label="GymAsset",
            text_node_properties=["name", "description", "equipmentCategory"],
            embedding_node_property="embedding"
        )
        logger.info("GymAsset vector index loaded successfully.")
    return _GymAssetVectorIndex

def get_google_maps_client() -> googlemaps.Client:
    """Get the loaded Google Maps client (lazy loaded)."""
    global _GOOGLE_MAPS_CLIENT
    if _GOOGLE_MAPS_CLIENT is None:
        _GOOGLE_MAPS_CLIENT = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
        logger.info("Google Maps client loaded successfully.")
    return _GOOGLE_MAPS_CLIENT

def get_postgres_connection():
    """Get the loaded PostgreSQL connection (lazy loaded)."""
    global _POSTGRES_CONNECTION
    if _POSTGRES_CONNECTION is None:
        _POSTGRES_CONNECTION = psycopg2.connect(os.environ.get("POSTGRES_DB_URI"))
        logger.info("Connection to the PostgreSQL established successfully.")
    return _POSTGRES_CONNECTION

__all__ = [
    "load_env",
    "get_embeddings", 
    "get_model", 
    "get_graph", 
    "get_GymAssetVectorIndex", 
    "get_google_maps_client", 
    "get_postgres_connection"
]
