"""
WebSocket streaming callback handlers for RAG v2.
Provides real-time streaming of LLM responses via WebSocket connections.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID

from fastapi import WebSocket
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult

log = logging.getLogger("lexcognito.rag.v2.callbacks")

class WSCallbackHandler(AsyncCallbackHandler):
    """
    WebSocket callback handler for streaming LLM responses.
    Streams tokens, workflow steps, and status updates in real-time.
    """
    
    def __init__(self, websocket: WebSocket, session_id: str = "default"):
        super().__init__()
        self.websocket = websocket
        self.session_id = session_id
        self.is_connected = True
        self.current_step = ""
        self.step_count = 0
    
    async def _send_safe(self, data: Dict[str, Any]) -> bool:
        """Send data via WebSocket with error handling."""
        if not self.is_connected:
            return False
        
        try:
            message = json.dumps(data, ensure_ascii=False)
            await self.websocket.send_text(message)
            return True
        except Exception as e:
            log.warning(f"WebSocket send failed for session {self.session_id}: {e}")
            self.is_connected = False
            return False
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts generating."""
        model_name = serialized.get("name", "unknown")
        
        await self._send_safe({
            "type": "llm_start",
            "session_id": self.session_id,
            "model": model_name,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token."""
        await self._send_safe({
            "type": "token",
            "session_id": self.session_id,
            "content": token,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes generating."""
        await self._send_safe({
            "type": "llm_end",
            "session_id": self.session_id,
            "step": self.current_step,
            "token_usage": response.llm_output.get("token_usage", {}) if response.llm_output else {},
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when LLM encounters an error."""
        await self._send_safe({
            "type": "error",
            "session_id": self.session_id,
            "error": str(error),
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when a chain starts."""
        chain_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        self.current_step = chain_name
        self.step_count += 1
        
        await self._send_safe({
            "type": "step_start",
            "session_id": self.session_id,
            "step": chain_name,
            "step_number": self.step_count,
            "inputs": {k: str(v)[:200] + "..." if len(str(v)) > 200 else str(v) 
                      for k, v in inputs.items()},  # Truncate long inputs
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain ends."""
        await self._send_safe({
            "type": "step_end",
            "session_id": self.session_id,
            "step": self.current_step,
            "step_number": self.step_count,
            "outputs": {k: str(v)[:200] + "..." if len(str(v)) > 200 else str(v) 
                       for k, v in outputs.items()},  # Truncate long outputs
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when a chain encounters an error."""
        await self._send_safe({
            "type": "error",
            "session_id": self.session_id,
            "error": str(error),
            "step": self.current_step,
            "step_number": self.step_count,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts."""
        tool_name = serialized.get("name", "unknown_tool")
        
        await self._send_safe({
            "type": "tool_start",
            "session_id": self.session_id,
            "tool": tool_name,
            "input": input_str[:200] + "..." if len(input_str) > 200 else input_str,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool ends."""
        await self._send_safe({
            "type": "tool_end",
            "session_id": self.session_id,
            "output": output[:200] + "..." if len(output) > 200 else output,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when a tool encounters an error."""
        await self._send_safe({
            "type": "error",
            "session_id": self.session_id,
            "error": str(error),
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when an agent takes an action."""
        await self._send_safe({
            "type": "agent_action",
            "session_id": self.session_id,
            "tool": action.tool,
            "tool_input": str(action.tool_input)[:200] + "..." if len(str(action.tool_input)) > 200 else str(action.tool_input),
            "log": action.log[:200] + "..." if len(action.log) > 200 else action.log,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when an agent finishes."""
        await self._send_safe({
            "type": "agent_finish",
            "session_id": self.session_id,
            "output": str(finish.return_values)[:200] + "..." if len(str(finish.return_values)) > 200 else str(finish.return_values),
            "log": finish.log[:200] + "..." if len(finish.log) > 200 else finish.log,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_text(self, text: str, **kwargs: Any) -> None:
        """Called when arbitrary text is generated."""
        await self._send_safe({
            "type": "text",
            "session_id": self.session_id,
            "content": text,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def send_status(self, status: str, message: str = ""):
        """Send a custom status update."""
        await self._send_safe({
            "type": "status",
            "session_id": self.session_id,
            "status": status,
            "message": message,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def send_progress(self, current: int, total: int, message: str = ""):
        """Send progress update."""
        await self._send_safe({
            "type": "progress",
            "session_id": self.session_id,
            "current": current,
            "total": total,
            "percentage": (current / total * 100) if total > 0 else 0,
            "message": message,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def send_context_update(self, context_type: str, content: str, source: str = ""):
        """Send context retrieval update."""
        await self._send_safe({
            "type": "context_update",
            "session_id": self.session_id,
            "context_type": context_type,  # "chapters", "quotes", "chunks"
            "content": content[:300] + "..." if len(content) > 300 else content,
            "source": source,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def send_irac_update(self, component: str, content: str):
        """Send IRAC analysis component update."""
        await self._send_safe({
            "type": "irac_update",
            "session_id": self.session_id,
            "component": component,  # "issue", "rule", "application", "conclusion"
            "content": content[:500] + "..." if len(content) > 500 else content,
            "step": self.current_step,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def disconnect(self):
        """Mark the callback as disconnected."""
        self.is_connected = False
        log.info(f"WebSocket callback disconnected for session {self.session_id}")

class MultiWSCallbackHandler(AsyncCallbackHandler):
    """
    Manages multiple WebSocket connections for broadcasting.
    Useful for scenarios where multiple clients need to see the same workflow.
    """
    
    def __init__(self):
        super().__init__()
        self.handlers: Dict[str, WSCallbackHandler] = {}
    
    def add_handler(self, session_id: str, websocket: WebSocket) -> WSCallbackHandler:
        """Add a new WebSocket handler."""
        handler = WSCallbackHandler(websocket, session_id)
        self.handlers[session_id] = handler
        log.info(f"Added WebSocket handler for session {session_id}")
        return handler
    
    def remove_handler(self, session_id: str):
        """Remove a WebSocket handler."""
        if session_id in self.handlers:
            self.handlers[session_id].disconnect()
            del self.handlers[session_id]
            log.info(f"Removed WebSocket handler for session {session_id}")
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected handlers."""
        disconnected = []
        
        for session_id, handler in self.handlers.items():
            if handler.is_connected:
                success = await handler._send_safe(data)
                if not success:
                    disconnected.append(session_id)
            else:
                disconnected.append(session_id)
        
        # Clean up disconnected handlers
        for session_id in disconnected:
            self.remove_handler(session_id)
    
    # Implement all callback methods to broadcast to all handlers
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        await self.broadcast({
            "type": "llm_start",
            "model": serialized.get("name", "unknown"),
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        await self.broadcast({
            "type": "token",
            "content": token,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        await self.broadcast({
            "type": "llm_end",
            "token_usage": response.llm_output.get("token_usage", {}) if response.llm_output else {},
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        await self.broadcast({
            "type": "error",
            "error": str(error),
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return [sid for sid, handler in self.handlers.items() if handler.is_connected]
    
    def get_session_count(self) -> int:
        """Get count of active sessions."""
        return len([h for h in self.handlers.values() if h.is_connected])

# Global multi-handler instance for broadcasting
multi_ws_handler = MultiWSCallbackHandler()

class RAGWorkflowCallbacks:
    """
    Specialized callbacks for RAG workflow steps.
    Provides domain-specific updates for legal research workflow.
    """
    
    def __init__(self, ws_handler: WSCallbackHandler):
        self.ws_handler = ws_handler
    
    async def on_issue_identification(self, issue: str):
        """Called when legal issue is identified."""
        await self.ws_handler.send_status("issue_identified", f"Legal issue: {issue[:100]}...")
    
    async def on_context_retrieval(self, granularity: str, doc_count: int):
        """Called when context is retrieved."""
        await self.ws_handler.send_status("context_retrieved", 
                                         f"Retrieved {doc_count} {granularity} documents")
    
    async def on_context_filtering(self, original_length: int, filtered_length: int):
        """Called when context is filtered."""
        await self.ws_handler.send_status("context_filtered", 
                                         f"Context reduced from {original_length} to {filtered_length} chars")
    
    async def on_irac_analysis_start(self):
        """Called when IRAC analysis begins."""
        await self.ws_handler.send_status("irac_analysis", "Starting legal analysis using IRAC framework")
    
    async def on_irac_component(self, component: str, content: str):
        """Called when IRAC component is completed."""
        await self.ws_handler.send_irac_update(component, content)
    
    async def on_final_answer_generation(self):
        """Called when final answer generation begins."""
        await self.ws_handler.send_status("answer_generation", "Generating comprehensive legal answer")
    
    async def on_workflow_complete(self, confidence: float):
        """Called when workflow is complete."""
        await self.ws_handler.send_status("complete", f"Legal analysis complete (confidence: {confidence:.1%})")

def create_rag_callbacks(websocket: WebSocket, session_id: str) -> Tuple[WSCallbackHandler, RAGWorkflowCallbacks]:
    """Create callback handlers for RAG workflow."""
    ws_handler = WSCallbackHandler(websocket, session_id)
    rag_callbacks = RAGWorkflowCallbacks(ws_handler)
    return ws_handler, rag_callbacks