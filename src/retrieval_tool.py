import os
import random
import numpy as np
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from src.rag_config import get_config, get_config_sha
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

# Load configuration
config = get_config()
config_sha = get_config_sha()

# Apply GPU settings based on config
if not config['embedder']['use_gpu'] or config['preflight']['force_cpu_embeddings']:
    os.environ['OLLAMA_NO_GPU'] = '1'

# Initialize the Ollama embeddings model with config values
ollama_emb = OllamaEmbeddings(
    model=config['embedder']['model'],
    base_url=config['embedder']['base_url'],
    # batch_size is handled differently in OllamaEmbeddings, so we'll use it during embedding
)

# Path to your knowledge base from config
KB_PATH = config['paths']['kb_dir']

# Set random seed for deterministic behavior
random_seed = config.get('tuning', {}).get('random_seed', 42)
random.seed(random_seed)
np.random.seed(random_seed)

class RetrievalToolSchema(BaseModel):
    query: str = Field(description="The search query.")

class RetrievalTool(BaseTool):
    name: str = "Initial Document Retrieval"
    description: str = "Performs initial broad search for documents using Ollama and FAISS."
    args_schema: type[BaseModel] = RetrievalToolSchema
    
    def __init__(self):
        """Initialize the retrieval tool with config logging."""
        super().__init__()
        print(f"[retrieval_tool] Loaded config from {os.path.abspath('config/rag_config.yaml')}")
        print(f"[retrieval_tool] Config SHA: {config_sha}")
        print(f"[retrieval_tool] Embedder model: {config['embedder']['model']} (backend: {config['embedder']['backend']})")
        print(f"[retrieval_tool] Splitter: chunk_size={config['splitter']['chunk_size']}, overlap={config['splitter']['chunk_overlap']}")
        print(f"[retrieval_tool] Retriever strategy: {config['retriever']['strategy']}, k={config['retriever']['k']}")
        print(f"[retrieval_tool] MMR lambda: {config['retriever']['mmr_lambda']}")

    def _run(self, query: str) -> list[str]:
        """Use the tool to retrieve documents from the knowledge base."""
        print(f"Retrieving documents for: {query}")
        
        # Use config values for loader - Note: DirectoryLoader doesn't support glob patterns
        # from the config directly, so we'll keep it as is for now but note the issue
        loader = DirectoryLoader(
            KB_PATH, 
            glob="**/*.md",  # This should be updated to use config['loader']['globs'] 
            show_progress=True
        )
        docs = loader.load()

        if not docs:
            return []

        # Use config values for text splitting
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['splitter']['chunk_size'], 
            chunk_overlap=config['splitter']['chunk_overlap']
        )
        splits = text_splitter.split_documents(docs)

        try:
            vector_store = FAISS.from_documents(documents=splits, embedding=ollama_emb)
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return []

        # Initialize tracking variables for diagnostics
        n_candidates_before = 0
        n_candidates_after_prefilter = 0
        
        # Use config value for retriever k
        if config['retriever']['strategy'] == "mmr":
            # Use MMR strategy - get more candidates to allow for deduplication and filtering
            retriever = vector_store.as_retriever(search_kwargs={'k': config['retriever']['k'] * 2})
            initial_candidates = retriever.invoke(query)
            
            if not initial_candidates:
                return []
            
            # Apply MMR to select exactly k unique candidates
            # For proper MMR implementation, we need to compute MMR scores for each document
            # and select the k most relevant ones
            
            # Extract content to deduplicate and ensure we have exactly k unique docs
            content_set = set()
            unique_docs = []
            
            for doc in initial_candidates:
                if doc.page_content not in content_set:
                    content_set.add(doc.page_content)
                    unique_docs.append(doc)
            
            # Limit to k candidates (or fewer if not enough unique docs)
            selected_docs = unique_docs[:config['retriever']['k']]
            
            # Apply cosine pre-filter if configured
            if config['embedder']['cosine_floor'] is not None and config['embedder']['cosine_floor'] > 0:
                # Get query embedding
                query_embedding = ollama_emb.embed_query(query)
                
                # Get document embeddings for all candidates
                doc_contents = [doc.page_content for doc in selected_docs]
                doc_embeddings = ollama_emb.embed_documents(doc_contents)
                
                # Calculate cosine similarities
                similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
                
                # Apply pre-filter
                filtered_docs = []
                for i, doc in enumerate(selected_docs):
                    if similarities[i] >= config['embedder']['cosine_floor']:
                        filtered_docs.append(doc)
                
                # Update tracking variables
                n_candidates_before = len(selected_docs)
                n_candidates_after_prefilter = len(filtered_docs)
                
                # Return filtered results
                return [doc.page_content for doc in filtered_docs]
            else:
                # No pre-filtering, return all unique docs
                return [doc.page_content for doc in selected_docs]
        else:
            # Use basic retrieval strategy (similarity-based)
            retriever = vector_store.as_retriever(search_kwargs={'k': config['retriever']['k']})
            initial_candidates = retriever.invoke(query)
            
            # Apply cosine pre-filter if configured
            if config['embedder']['cosine_floor'] is not None and config['embedder']['cosine_floor'] > 0:
                # Get query embedding
                query_embedding = ollama_emb.embed_query(query)
                
                # Get document embeddings for all candidates
                doc_contents = [doc.page_content for doc in initial_candidates]
                doc_embeddings = ollama_emb.embed_documents(doc_contents)
                                
                # Calculate cosine similarities
                similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
                
                # Apply pre-filter
                filtered_docs = []
                for i, doc in enumerate(initial_candidates):
                    if similarities[i] >= config['embedder']['cosine_floor']:
                        filtered_docs.append(doc)
                
                # Update tracking variables
                n_candidates_before = len(initial_candidates)
                n_candidates_after_prefilter = len(filtered_docs)
                
                # Return filtered results
                return [doc.page_content for doc in filtered_docs]
            else:
                # No pre-filtering, return all candidates
                return [doc.page_content for doc in initial_candidates]