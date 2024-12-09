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
from prompts import PROMPT_STX

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
            temperature=0.0,
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

    def _initialize_mongodb_stx(self):
        """Initialize MongoDB connection and vector store"""
        self.mongo_client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        self.vector_store = MongoDBAtlasVectorSearch(
            self.mongo_client,
            db_name="stock_db",
            collection_name="stocks",
            vector_index_name="vector_index_stx"
        )

    def create_simple_chat(self):
        """Create a simple chat engine without RAG"""
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=4096)
        self.chat_engine = SimpleChatEngine.from_defaults(
            system_prompt="""
            Vous êtes un assistant polyvalent et communicatif, capable d'avoir des interactions normales, ainsi que de fournir des réponses détaillées.
            Vous travaillez dans une entreprise IT et cloud, aidant les équipes à planifier des MEP (operations IT) dans K8S, Réseau, System, Services managés. Tu es spécialiste dans la recherche des informations et corrélations entre les differentes MEP, Application et types d'opération pour aider efficassement l'utilisateur.
            <INFO>
            # les instances et serveurs sont de dans le format (eg. db01-MyApplication-prod)
            # La procèdure d'Arrêt/Relance (appelés PARPRE) sont dans ce format table : exp. Opération de upgrade mongodb sur db01-MyApplication-prod :
            étape : étape 0, serveur : db01-MyApplication-prod, action inhibition supervision : inhibition de supervision sur la db01 et l'application MyApplication, commande : NA, Résultat attentdu : inhibition supervision effectuée
            étape : étape 1, serveur : db01-MyApplication-prod, action d'arrêt : commande arrêt process via systemctl, commande: sudo systemctl stop mongod et sudo systemctl stop mongod , résultat attentdu : commande ps avec 0 process 
            étape : étape 2, serveur : db01-MyApplication-prod, action technique : comamndes pour upgrade de mongodb, commande: sudo apt-get install mongodb-org, résultat attentdu : commande pour valider la nouvelle version mongodb
            étape : étape 3, serveur : db01-MyApplication-prod, action de relance : commande relance du process via systemctl, commande : sudo systemctl start mongod et sudo systemctl status mongod  , résultat attentdu : commande ps avec les process présents
            étape : étape 4, serveur : db01-MyApplication-prod, action de vérification : statut ok sur la db01 ainsi que l'application MyApplication, commande : NA, résultat attentdu : vérification OK
            étape : étape 5, serveur : db01-MyApplication-prod, action réactivation supervision : réactivation de supervision sur la db01 et l'application MyApplication, commande : NA, résultat attentdu : réactivation supervision effectuée
            </INFO>
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
            "similarity_top_k": 9,
            "vector_store_query_mode": "default",
            "memory": self.memory,
            "verbose": True,
            "context_prompt": """
            Vous êtes un assistant polyvalent et communicatif, capable d'avoir des interactions normales, ainsi que de fournir des réponses techniques et détaillées.
            Vous travaillez dans une entreprise IT/cloud en service de déploiement, aidant les équipes à planifier les opérations MEP (Mise En Production) dans K8S, Réseau, System, Services managésn en fournissant des Plan de MEP, tout en respectant les contraintes métiers des applications. Tu es spécialiste dans la recherche des informations et corrélations entre les differentes MEP, Application et types d'opération pour aider efficassement l'utilisateur, ajoutant des tableaux dans ses réponses.
            Voici les documents pertinents pour le contexte, qui est une liste d'opérations, appelés MEP, Mise en production :
            {context_str}
            \nInstructions : Utilisez l'historique de conversation précédente, ou le contexte ci-dessus, pour interagir et aider l'utilisateur. Si vous ne savez pas, répondez simplement, sans créer des réponses fictives. réponse concise.
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

    def create_stx_rag_chat(self):
        """Create a RAG-enabled chat engine with optional filters"""
        self._initialize_mongodb_stx()
        
        vector_store_stx = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex.from_vector_store(self.vector_store)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=6096)

        # Create chat engine parameters
        chat_engine_params = {
            "chat_mode": "condense_plus_context",
            "similarity_top_k": 11,
            "vector_store_query_mode": "hybrid",
            "memory": self.memory,
            "verbose": True,
            "context_prompt": PROMPT_STX
        }

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
