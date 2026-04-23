import logging
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager 

from api.routes import router 
from utils.logging_config import setup_logging
from graph.builder import build_graph

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Travel AI started")
    app.state.graph = build_graph()
    logger.info("State Graph Initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Travel AI",
    description="Plan your travel with Travel AI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
