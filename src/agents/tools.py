import logging
import math
import os
import re
import time
from functools import lru_cache
from pathlib import Path

import numexpr
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.tools import BaseTool, tool

load_dotenv()  # Make EMBEDDING_MODEL_PATH available no matter how the process is started

logger = logging.getLogger(__name__)


def calculator_func(expression: str) -> str:
    """Calculates a math expression using numexpr.

    Useful for when you need to answer questions about math using numexpr.
    This tool is only for math questions and nothing else. Only input
    math expressions.

    Args:
        expression (str): A valid numexpr formatted math expression.

    Returns:
        str: The result of the math expression.
    """

    try:
        local_dict = {"pi": math.pi, "e": math.e}
        output = str(
            numexpr.evaluate(
                expression.strip(),
                global_dict={},  # restrict access to globals
                local_dict=local_dict,  # add common mathematical functions
            )
        )
        return re.sub(r"^\[|\]$", "", output)
    except Exception as e:
        raise ValueError(
            f'calculator("{expression}") raised error: {e}.'
            " Please try again with a valid numerical expression"
        )


calculator: BaseTool = tool(calculator_func)
calculator.name = "Calculator"


# Format retrieved documents
def format_contexts(docs):
    return "\n\n".join(doc.page_content for doc in docs)


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Local BGE-M3 embeddings, no API key required.

    Model path comes from the EMBEDDING_MODEL_PATH env var so the same model
    is used by both the agent service and the Chroma seeding script.
    """
    default_model_path = str(Path(__file__).resolve().parents[2] / "models" / "bge-m3")
    model_path = os.getenv("EMBEDDING_MODEL_PATH", default_model_path)
    return HuggingFaceEmbeddings(
        model_name=model_path,
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_chroma_retriever():
    """Create the Chroma client once per process and reuse it across tool calls.

    Recreating a PersistentClient on every tool call is both slow (model + client
    init) and triggers an intermittent lifecycle bug in chromadb's shared client
    manager, so we cache the retriever like the embeddings object. First-time
    creation can also flake in chromadb 1.5.x, so we retry a few times.
    """
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            embeddings = get_embeddings()
            chroma_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
            return chroma_db.as_retriever(search_kwargs={"k": 5})
        except Exception as e:
            last_exc = e
            logger.warning("Chroma client creation failed (attempt %d/3): %s", attempt, e)
            time.sleep(1)
    assert last_exc is not None
    raise last_exc


def load_chroma_db():
    # Get the cached chroma retriever
    return get_chroma_retriever()


def database_search_func(query: str) -> str:
    """Searches chroma_db for information in the company's handbook."""
    # Get the chroma retriever
    retriever = load_chroma_db()

    # Search the database for relevant documents
    documents = retriever.invoke(query)

    # Format the documents into a string
    context_str = format_contexts(documents)

    return context_str


database_search: BaseTool = tool(database_search_func)
database_search.name = "Database_Search"  # Update name with the purpose of your database
