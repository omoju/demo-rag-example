from dotenv import load_dotenv
import os
from typing import List

from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response.notebook_utils import display_source_node

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class RAGCreator():
    def __init__(self):
        self.documents = []
        self.nodes = None
        self.retriever = None
        self.query_engine = None

        self.rag_info = {}

    def _update_rag_info(self, params:dict):
        params.__delitem__("self")
        callable_obj_keys = [k for k,v in params.items() if callable(v)]
        for k in callable_obj_keys:
            params[k] = params[k].__name__
        self.rag_info.update(params)

    def load_documents(self, data_loader, data_loader_kwargs:dict):
        self._update_rag_info(locals())
        
        try:
            docs = data_loader().load_data(**data_loader_kwargs)
        except Exception as e:
            raise TypeError(f"Error loading documents: {e}.")
        self.documents = docs

    def parse_docs_to_nodes(self, node_parser=SimpleNodeParser, chunk_size=1024):
        self._update_rag_info(locals())

        node_parser = node_parser.from_defaults(chunk_size=chunk_size)
        nodes = node_parser.get_nodes_from_documents(self.documents)

        for idx, node in enumerate(nodes):
            node.id_ = f"node-{idx}"
        self.nodes = nodes
        
    def set_model_settings(self, open_ai_model="gpt-3.5-turbo", embed_model="local:BAAI/bge-small-en"):
        self._update_rag_info(locals())
        load_dotenv()
        
        Settings.llm = OpenAI(model=open_ai_model)
        Settings.embed_model = resolve_embed_model(embed_model)

    def create_retriever(self, vector_store_impl=VectorStoreIndex, similarity_top_k=2):
        self._update_rag_info(locals())
        index = vector_store_impl(self.nodes)
        self.retriever = index.as_retriever(similarity_top_k=similarity_top_k)

    def create_query_engine(self, query_engine=RetrieverQueryEngine):
        self._update_rag_info(locals())
        self.query_engine = query_engine.from_args(self.retriever)
    
    def setup_and_deploy_RAG(self, data_loader, data_loader_kwargs, 
                             node_parser=SimpleNodeParser, chunk_size=1024, 
                             open_ai_model="gpt-3.5-turbo", embed_model="local:BAAI/bge-small-en", 
                             vector_store_impl=VectorStoreIndex, similarity_top_k=2, 
                             query_engine=RetrieverQueryEngine):
        self.load_documents(data_loader, data_loader_kwargs)
        self.parse_docs_to_nodes(node_parser, chunk_size)
        self.set_model_settings(open_ai_model, embed_model)
        self.create_retriever(vector_store_impl, similarity_top_k)
        self.create_query_engine(query_engine)
        return self

    def query(self, query:str) -> str:
        if self.query_engine is not None:
            response =  self.query_engine.query(query)
            return str(response)
        else:
            raise ValueError("You must set up your RAG and its query engine before submitting queries.")
        
    def query_multiple(self, queries:List[str]) -> List[str]:
        if self.query_engine is not None:
            responses = []
            for query in queries:
                response =  self.query_engine.query(query)
                responses.append(str(response))
            return responses
        else:
            raise ValueError("You must set up your RAG and its query engine before submitting queries.")
    
    def fetch_relevant_info(self, query:str) -> List[str]:
        if self.retriever is not None:
            retrievals = self.retriever.retrieve(query)
            return retrievals
        else:
            raise ValueError("You must set up your RAG and its retriever before fetching relevant information.")
        
    def display_relevant_info(self, query:str, source_length=1500):
        retrievals = self.fetch_relevant_info(query=query)
        for retrieval in retrievals:
            display_source_node(retrieval, source_length=source_length)

    def get_rag_info(self):
        return self.rag_info