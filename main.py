import logging

from src.rag_creator import RAGCreator
from src.custom_readers import FimioBlogWebReader

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="INFO:     %(message)s")
app = FastAPI()

### --- GLOBAL SETUP --- ###

# List of allowed origins
origins = [
    "http://localhost:3000"
]

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Required parameters for the RAG
REQUIRED_FIMIO_PARAMS = {
    "base_url": "https://fimio.xyz/blog/"
}

# Load the RAG and instantiate it globally
rag = RAGCreator().setup_and_deploy_RAG(
    data_loader=FimioBlogWebReader,
    data_loader_kwargs=REQUIRED_FIMIO_PARAMS
)

### --- ENDPOINTS --- ###
@app.get("/")
async def root():
    rag_info = rag.get_rag_info()

    formatted_rag_info = ""
    if len(rag_info) > 0:
        logging.info("RAG Successfully Loaded")
        formatted_rag_info = "--- RAG SUCCESSFULLY LOADED ---\n\nRAG Configuration:\n"
        for key, value in rag_info.items():
            if isinstance(value, dict):
                nested_str = ", ".join(f"{k}: {v}" for k, v in value.items())
                formatted_rag_info += f"- {key}: {{\n   {nested_str}\n  }}\n"
            else:
                formatted_rag_info += f"- {key}: {value}\n"
    else:
        logging.info("RAG Failed to Load")
        formatted_rag_info = "--- RAG FAILED TO LOAD ---"

    return Response(
        content=formatted_rag_info,
        media_type="text/plain"
    )
    
@app.get("/query")
async def query(query:str):
    try:
        response = rag.query(query)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"An error occurred: {e}"}
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000, timeout_graceful_shutdown=10)