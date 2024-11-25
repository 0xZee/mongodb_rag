# app_tools.py
import streamlit as st
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
import pymongo
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, ExactMatchFilter, FilterOperator, FilterCondition
from llama_index.llms.groq import Groq
from llama_index.embeddings.cohere import CohereEmbedding

class RagEngine:
    def __init__(self):
        self.mongo_client = None
        self.vector_store = None
        self.chat_engine = None
        self.memory = None
        self._setup_settings()

    def _setup_settings(self):
        """Initialize LLM and embedding model settings"""
        Settings.llm = Groq(
            model="llama-3.2-3b-preview",
            temperature=0.1,
            api_key=st.secrets["GROQ_API"]
        )
        Settings.embed_model = CohereEmbedding(
            model="embed-multilingual-v3.0",
            cohere_api_key=st.secrets["COHERE_DEV_API"]
        )

    def _initialize_mongodb(self):
        """Initialize MongoDB connection and vector store"""
        self.mongo_client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        self.vector_store = MongoDBAtlasVectorSearch(
            self.mongo_client,
            db_name="IT_Operations",
            collection_name="vectorstore_li",
            vector_index_name="vector_index_li"
        )

    def create_simple_chat(self):
        """Create a simple chat engine without RAG"""
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=4096)
        self.chat_engine = SimpleChatEngine.from_defaults(
            system_prompt="""
            Vous êtes un assistant polyvalent et communicatif, capable d'avoir des interactions normales, ainsi que de fournir des réponses détaillées.
            Vous travaillez dans une entreprise IT et cloud, aidant les équipes à planifier des MEP (operations IT) dans K8S, Réseau, System, Services managés. Tu es spécialiste dans la recherche des informations et corrélations entre les differentes MEP, Application et types d'opération pour aider efficassement l'utilisateur.
            """,
            memory=self.memory,
            streaming=True
        )
        return self.chat_engine

    def create_rag_chat(self, app_filter=None, status_filter=None):
        """Create a RAG-enabled chat engine with optional filters"""
        self._initialize_mongodb()
        
        vector_store_context = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex.from_vector_store(self.vector_store)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=6096)

        # Create chat engine parameters
        chat_engine_params = {
            "chat_mode": "condense_plus_context",
            "similarity_top_k": 11,
            "vector_store_query_mode": "default",
            "memory": self.memory,
            "verbose": True,
            "context_prompt": """
            Vous êtes un assistant polyvalent et communicatif, capable d'avoir des interactions normales, ainsi que de fournir des réponses techniques et détaillées.
            Vous travaillez dans une entreprise IT/cloud en service de déploiement, aidant les équipes à planifier les opérations MEP (Mise En Production) dans K8S, Réseau, System, Services managésn en fournissant des Plan de MEP, tout en respectant les contraintes métiers des applications. Tu es spécialiste dans la recherche des informations et corrélations entre les differentes MEP, Application et types d'opération pour aider efficassement l'utilisateur, ajoutant des tableaux dans ses réponses.
            Voici les documents pertinents pour le contexte, qui est une liste d'opérations, appelés MEP, Mise en production :
            {context_str}
            \nInstructions : Utilisez l'historique de conversation précédente, ou le contexte ci-dessus, pour interagir et aider l'utilisateur. Si vous ne savez pas, répondez simplement, sans créer des réponses fictives.
            """
        }

        # Add filters only if they are set and not "Null"
        active_filters = []
        
        if app_filter and app_filter != "Null":
            active_filters.append(
                MetadataFilter(
                    key="operation_application",  # Removed 'metadata.' prefix
                    operator=FilterOperator.EQ,
                    value=app_filter
                )
            )
        
        if status_filter and status_filter != "Null":
            active_filters.append(
                MetadataFilter(
                    key="operation_status",  # Removed 'metadata.' prefix
                    operator=FilterOperator.EQ,
                    value=status_filter
                )
            )

        if active_filters:
            chat_engine_params["filters"] = MetadataFilters(
                filters=active_filters,
                condition=FilterCondition.AND
            )

        self.chat_engine = index.as_chat_engine(**chat_engine_params)
        return self.chat_engine

    def reset(self):
        """Reset the chat engine state"""
        self.chat_engine = None
        self.memory = None
        if self.mongo_client:
            self.mongo_client.close()
            self.mongo_client = None
        self.vector_store = None
