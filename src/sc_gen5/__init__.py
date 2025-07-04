"""Strategic Counsel Gen 5 - Local-first legal research assistant."""

__version__ = "5.0.0"
__author__ = "Strategic Counsel"
__email__ = "contact@strategiccounsel.ai"

from .core.doc_store import DocStore
from .core.rag_pipeline import RAGPipeline
from .core.local_llm import LocalLLMGenerator
from .core.cloud_llm import CloudLLMGenerator, CloudProvider

__all__ = [
    "DocStore",
    "RAGPipeline", 
    "LocalLLMGenerator",
    "CloudLLMGenerator",
    "CloudProvider",
] 