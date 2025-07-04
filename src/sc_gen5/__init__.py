"""Strategic Counsel Gen 5 - Local-first legal research assistant."""

__version__ = "5.0.0"
__author__ = "Strategic Counsel"
__email__ = "contact@strategiccounsel.ai"

from sc_gen5.core.doc_store import DocStore
from sc_gen5.core.rag_pipeline import RAGPipeline
from sc_gen5.core.local_llm import LocalLLMGenerator
from sc_gen5.core.cloud_llm import CloudLLMGenerator, CloudProvider

__all__ = [
    "DocStore",
    "RAGPipeline", 
    "LocalLLMGenerator",
    "CloudLLMGenerator",
    "CloudProvider",
] 