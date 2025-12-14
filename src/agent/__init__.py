import os
import psycopg2
import dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph, Neo4jVector
import googlemaps

# Global variables for embeddings and model
EMBEDDINGS = None
MODEL = None
GRAPH = None
GOOGLE_MAPS_CLIENT = None
GymAssetVectorIndex = None
POSTGRES_CONNECTION = None

def load_env():
    dotenv.load_dotenv()
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = "fitbridge-chatbot"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "LANGSMITH_API_KEY") or ""
    os.environ["OPENAI_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "OPENAI_API_KEY") or ""
    os.environ["GOOGLE_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "GOOGLE_API_KEY") or ""
    os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI") or ""
    os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME") or ""
    os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD") or ""
    os.environ["GOOGLE_MAPS_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "GOOGLE_MAPS_API_KEY") or ""
    os.environ["CHECKPOINTER_DB_URI"] = dotenv.get_key(dotenv.find_dotenv(), "CHECKPOINTER_DB_URI") or ""
    os.environ["POSTGRES_DB_URI"] = dotenv.get_key(dotenv.find_dotenv(), "POSTGRES_DB_URI") or ""

def connect_postgres():
    connection = psycopg2.connect(os.environ.get("POSTGRES_DB_URI"))
    print("Connection to the PostgreSQL established successfully.")
    global POSTGRES_CONNECTION
    POSTGRES_CONNECTION = connection

def load_google_maps_client():
    global GOOGLE_MAPS_CLIENT
    GOOGLE_MAPS_CLIENT = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
    print("Google Maps client loaded successfully.")

def load_models():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    # model = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash-lite",
    #     temperature=0.5,
    #     max_tokens=None,
    #     timeout=None,
    #     max_retries=2,
    # )
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
    )

    print("OpenAI embeddings loaded successfully.")
    print("OpenAI model loaded successfully.")
    global EMBEDDINGS, MODEL
    EMBEDDINGS = embeddings
    MODEL = model

def load_graph():
    """Load the graph database."""
    graph = Neo4jGraph(
        url=os.environ.get("NEO4J_URI"),
        username=os.environ.get("NEO4J_USERNAME"),
        password=os.environ.get("NEO4J_PASSWORD")
    )

    global GymAssetVectorIndex
    GymFacilityVectorIndex = Neo4jVector.from_existing_graph(
        embedding=get_embeddings(),
        graph=graph,
        index_name="GymFacilityVectorIndex",
        node_label="GymFacility",
        text_node_properties=["name", "description"], # text properties from :Document nodes
        embedding_node_property="embedding" # name of the node property that stores the embeddings
    )
    GymAssetVectorIndex = Neo4jVector.from_existing_graph(
        embedding=get_embeddings(),
        graph=graph,
        index_name="GymAssetVectorIndex",
        node_label="GymAsset",
        text_node_properties=["name", "description", "equipmentCategory", "targetMuscularGroups"], # text properties from :Document nodes
        embedding_node_property="embedding" # name of the node property that stores the embeddings
    )
    global GRAPH
    GRAPH = graph
    print("Graph database loaded successfully.")

def get_embeddings():
    """Get the loaded embeddings model."""
    return EMBEDDINGS

def get_model():
    """Get the loaded language model."""
    return MODEL

def get_graph():
    """Get the loaded graph database."""
    return GRAPH

def get_GymAssetVectorIndex():
    """Get the loaded GymAsset vector index."""
    return GymAssetVectorIndex

def get_google_maps_client():
    """Get the loaded Google Maps client."""
    return GOOGLE_MAPS_CLIENT

def get_postgres_connection():
    """Get the loaded PostgreSQL connection."""
    return POSTGRES_CONNECTION

load_env()
load_models()
load_graph()
load_google_maps_client()
connect_postgres()