"""
LangGraph plan-execute agent for RAG v2.
Implements IRAC (Issue, Rule, Application, Conclusion) legal reasoning workflow.
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass

import torch
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor  # Not needed for current implementation

from .models import utility_llm, generator_llm
from .enhanced_retrievers import retrieve_context, EnhancedRetrievalConfig
from .hardware import set_inference_mode

log = logging.getLogger("lexcognito.rag.v2.graphs")

class RAGState(TypedDict):
    """State for the RAG agent workflow."""
    question: str
    context: str
    answer: str
    aggregated_context: str
    past_steps: List[str]
    tool: str
    issue: str
    rule: str
    application: str
    conclusion: str
    confidence: float
    needs_more_context: bool

@dataclass 
class LegalPrompts:
    """Legal reasoning prompts for different workflow stages - optimized for litigation."""
    
    # Issue identification prompt (utility LLM) - litigation focused
    issue_prompt = """You are a legal assistant analyzing a question to identify the core litigation issues.

Question: {question}

Identify the main legal issues, party positions, and key disputes involved. Be concise and specific.

Core Litigation Issues:"""

    # Context filtering prompt (utility LLM) - litigation focused
    filter_prompt = """You are filtering legal context for relevance to a litigation question.

Question: {question}

Context: {context}

Filter and summarize only the most relevant parts of the context that directly address party positions, legal arguments, and evidence. Remove irrelevant information.

Relevant Litigation Context:"""

    # Query rewriting prompt (utility LLM) - litigation focused
    rewrite_prompt = """You are improving a legal search query for better retrieval in litigation research.

Original Question: {question}
Past Steps: {past_steps}

Rewrite the question to be more specific and likely to retrieve relevant litigation information. Include legal terminology, party positions, and key legal concepts.

Improved Litigation Query:"""

    # IRAC reasoning prompt (reasoning LLM) - litigation optimized
    irac_prompt = """You are a litigation expert providing detailed analysis using the IRAC method.

Question: {question}

Relevant Legal Context:
{context}

Previous Analysis Steps:
{past_steps}

Provide a comprehensive litigation analysis using the IRAC framework:

**ISSUE**: What are the key legal issues and disputes between parties?

**RULE**: What are the applicable legal rules, statutes, cases, or principles?

**APPLICATION**: How do the legal rules apply to the specific facts and circumstances? Analyze party positions and argument strengths.

**CONCLUSION**: What is your legal conclusion and assessment of party positions and argument strengths?

Ensure your analysis is thorough, well-reasoned, and focuses on litigation strategy and party positions.

LITIGATION ANALYSIS:"""

    # Final answer prompt (generator LLM) - litigation optimized
    answer_prompt = """You are providing a comprehensive litigation answer based on IRAC analysis.

Question: {question}

IRAC Analysis:
Issue: {issue}
Rule: {rule}  
Application: {application}
Conclusion: {conclusion}

Context: {context}

Provide a detailed, professional litigation analysis that:
1. Directly answers the question with specific legal analysis of party positions
2. Includes direct quotes from the source documents with proper citation
3. Analyzes the strength of each party's arguments and evidence
4. Explains the legal reasoning with specific litigation strategy insights
5. Provides practical implications for case strategy and settlement considerations
6. Notes any limitations, caveats, or areas of uncertainty in the legal positions
7. Uses formal legal language and precise litigation terminology
8. Aims for 400+ words with comprehensive coverage of party positions and argument strengths

Your response should be thorough, well-structured, and provide detailed litigation analysis with specific citations, party position analysis, and argument strength assessment.

FINAL LITIGATION ANALYSIS:"""

class RAGAgent:
    """Plan-execute agent for legal RAG using LangGraph."""
    
    def __init__(self):
        self.prompts = LegalPrompts()
        self.utility_tokenizer = None
        self.utility_model = None
        self.reasoning_tokenizer = None
        self.reasoning_model = None
        self.graph = None
        self._build_graph()
    
    def _load_models(self):
        """Lazy load models when needed."""
        if self.utility_tokenizer is None:
            log.info("Loading utility model for agent...")
            self.utility_tokenizer, self.utility_model = utility_llm()
            set_inference_mode()
        
        if self.reasoning_tokenizer is None:
            log.info("Loading reasoning model for agent...")  
            self.generator_tokenizer, self.generator_model = generator_llm()
    
    def _generate_with_utility_llm(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate text using the utility LLM (Phi-3-mini)."""
        self._load_models()
        
        try:
            inputs = self.utility_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            # Keep on CPU since utility model is loaded on CPU
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.utility_model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.utility_tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            response = self.utility_tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True
            )
            
            return response.strip()
            
        except Exception as e:
            log.error(f"Utility LLM generation failed: {e}")
            return "Error in utility model generation"
    
    def _generate_with_generator_llm(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate text using the generator LLM (Mistral-7B) optimized for litigation workflows."""
        self._load_models()
        
        try:
            inputs = self.generator_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=3072)
            
            # Keep on CPU since generator model is loaded on CPU
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.generator_model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.3,        # Lower temperature for consistent legal analysis
                    do_sample=True,
                    top_p=0.9,             # Nucleus sampling for quality
                    pad_token_id=self.generator_tokenizer.eos_token_id,
                    repetition_penalty=1.1, # Prevent repetition in legal arguments
                    stop=["[INST]", "[/INST]", "</s>"]  # Stop at instruction markers
                )
            
            response = self.generator_tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True
            )
            
            return response.strip()
            
        except Exception as e:
            log.error(f"Generator LLM generation failed: {e}")
            return "Error in generator model generation"
    
    def identify_issue(self, state: RAGState) -> RAGState:
        """Identify the core legal issue using utility LLM."""
        log.info("Identifying legal issue...")
        
        prompt = self.prompts.issue_prompt.format(question=state["question"])
        issue = self._generate_with_utility_llm(prompt, max_tokens=200)
        
        state["issue"] = issue
        state["past_steps"].append(f"Issue Identified: {issue[:100]}...")
        
        log.debug(f"Issue identified: {issue[:100]}...")
        return state
    
    def retrieve_context(self, state: RAGState) -> RAGState:
        """Retrieve relevant context using multi-granularity retrieval."""
        log.info("Retrieving legal context...")
        
        # Use original question for retrieval
        query = state["question"]
        
        # If we have issue analysis, use it to enhance the query
        if state.get("issue"):
            enhanced_query = f"{query} {state['issue']}"
        else:
            enhanced_query = query
        
        try:
            context = retrieve_context(enhanced_query)
            state["context"] = context
            state["aggregated_context"] = context  # For compatibility
            state["past_steps"].append(f"Retrieved context: {len(context)} characters")
            
            log.info(f"Retrieved context: {len(context)} characters")
            
        except Exception as e:
            log.error(f"Context retrieval failed: {e}")
            state["context"] = "Error retrieving context"
            state["aggregated_context"] = "Error retrieving context"
        
        return state
    
    def filter_context(self, state: RAGState) -> RAGState:
        """Filter and summarize context using utility LLM."""
        log.info("Filtering context for relevance...")
        
        if not state.get("context") or state["context"] == "Error retrieving context":
            state["needs_more_context"] = True
            return state
        
        # If context is short enough, skip filtering
        if len(state["context"]) < 2000:
            state["needs_more_context"] = False
            return state
        
        prompt = self.prompts.filter_prompt.format(
            question=state["question"],
            context=state["context"][:3000]  # Limit input size
        )
        
        filtered_context = self._generate_with_utility_llm(prompt, max_tokens=512)
        
        # Update context with filtered version
        state["context"] = filtered_context
        state["aggregated_context"] = filtered_context
        state["past_steps"].append("Context filtered for relevance")
        state["needs_more_context"] = len(filtered_context) < 200  # Need more if too little context
        
        log.debug(f"Context filtered: {len(filtered_context)} characters")
        return state
    
    def rewrite_query(self, state: RAGState) -> RAGState:
        """Rewrite query for better retrieval using utility LLM."""
        log.info("Rewriting query for improved retrieval...")
        
        past_steps_str = " | ".join(state["past_steps"][-3:])  # Last 3 steps
        
        prompt = self.prompts.rewrite_prompt.format(
            question=state["question"],
            past_steps=past_steps_str
        )
        
        rewritten_query = self._generate_with_utility_llm(prompt, max_tokens=128)
        
        # Use rewritten query for new retrieval
        try:
            new_context = retrieve_context(rewritten_query)
            # Combine with existing context
            combined_context = f"{state.get('context', '')}\n\n--- Additional Context ---\n{new_context}"
            state["context"] = combined_context
            state["aggregated_context"] = combined_context
            state["past_steps"].append(f"Query rewritten and re-retrieved: {rewritten_query[:50]}...")
            
        except Exception as e:
            log.error(f"Query rewrite retrieval failed: {e}")
            state["past_steps"].append("Query rewrite failed")
        
        return state
    
    def analyze_irac(self, state: RAGState) -> RAGState:
        """Perform IRAC analysis using reasoning LLM."""
        log.info("Performing IRAC legal analysis...")
        
        past_steps_str = "\n".join(state["past_steps"])
        
        prompt = self.prompts.irac_prompt.format(
            question=state["question"],
            context=state.get("context", "No context available"),
            past_steps=past_steps_str
        )
        
        irac_analysis = self._generate_with_generator_llm(prompt, max_tokens=1500)
        
        # Parse IRAC components (simple parsing)
        analysis_parts = irac_analysis.split("**")
        
        issue_part = ""
        rule_part = ""
        application_part = ""
        conclusion_part = ""
        
        for i, part in enumerate(analysis_parts):
            if "ISSUE" in part.upper():
                issue_part = analysis_parts[i+1] if i+1 < len(analysis_parts) else ""
            elif "RULE" in part.upper():
                rule_part = analysis_parts[i+1] if i+1 < len(analysis_parts) else ""
            elif "APPLICATION" in part.upper():
                application_part = analysis_parts[i+1] if i+1 < len(analysis_parts) else ""
            elif "CONCLUSION" in part.upper():
                conclusion_part = analysis_parts[i+1] if i+1 < len(analysis_parts) else ""
        
        state["issue"] = issue_part.strip()
        state["rule"] = rule_part.strip()
        state["application"] = application_part.strip()
        state["conclusion"] = conclusion_part.strip()
        state["past_steps"].append("IRAC analysis completed")
        
        log.debug("IRAC analysis completed")
        return state
    
    def generate_answer(self, state: RAGState) -> RAGState:
        """Generate final answer using reasoning LLM."""
        log.info("Generating final legal answer...")
        
        prompt = self.prompts.answer_prompt.format(
            question=state["question"],
            issue=state.get("issue", "Not identified"),
            rule=state.get("rule", "Not identified"),
            application=state.get("application", "Not analyzed"),
            conclusion=state.get("conclusion", "Not concluded"),
            context=state.get("context", "No context")
        )
        
        final_answer = self._generate_with_generator_llm(prompt, max_tokens=1500)
        
        # Calculate confidence based on context quality and completeness
        confidence = 0.7  # Base confidence
        if state.get("context") and len(state["context"]) > 500:
            confidence += 0.1
        if state.get("issue") and state.get("rule"):
            confidence += 0.1
        if state.get("application") and state.get("conclusion"):
            confidence += 0.1
        
        state["answer"] = final_answer
        state["confidence"] = min(confidence, 0.95)  # Cap at 95%
        state["past_steps"].append("Final answer generated")
        
        log.info("Final answer generated successfully")
        return state
    
    def should_continue(self, state: RAGState) -> str:
        """Decide whether to continue processing or end."""
        # If we need more context and haven't tried rewriting yet
        if (state.get("needs_more_context", False) and 
            not any("rewritten" in step.lower() for step in state["past_steps"])):
            return "rewrite"
        
        # If we have context but no IRAC analysis yet
        if (state.get("context") and 
            not state.get("issue") and 
            not any("IRAC" in step for step in state["past_steps"])):
            return "analyze"
        
        # If we have IRAC but no final answer
        if (state.get("issue") and 
            not state.get("answer")):
            return "answer"
        
        # Otherwise, we're done
        return "end"
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("identify_issue", self.identify_issue)
        workflow.add_node("retrieve", self.retrieve_context)
        workflow.add_node("filter", self.filter_context)
        workflow.add_node("rewrite", self.rewrite_query)
        workflow.add_node("analyze", self.analyze_irac)
        workflow.add_node("answer", self.generate_answer)
        
        # Set entry point
        workflow.set_entry_point("identify_issue")
        
        # Add edges
        workflow.add_edge("identify_issue", "retrieve")
        workflow.add_edge("retrieve", "filter")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "filter",
            self.should_continue,
            {
                "rewrite": "rewrite",
                "analyze": "analyze",
                "answer": "answer",
                "end": END
            }
        )
        
        workflow.add_edge("rewrite", "filter")
        workflow.add_edge("analyze", "answer")
        workflow.add_edge("answer", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        log.info("LangGraph workflow compiled successfully")
    
    def invoke(self, question: str, callbacks: Optional[List] = None) -> Dict[str, Any]:
        """Execute the RAG workflow for a given question."""
        log.info(f"Starting RAG workflow for question: {question[:100]}...")
        
        # Initialize state
        initial_state: RAGState = {
            "question": question,
            "context": "",
            "answer": "",
            "aggregated_context": "",
            "past_steps": [],
            "tool": "",
            "issue": "",
            "rule": "",
            "application": "",
            "conclusion": "",
            "confidence": 0.0,
            "needs_more_context": False
        }
        
        try:
            # Execute the workflow
            final_state = self.graph.invoke(initial_state, {"callbacks": callbacks or []})
            
            log.info("RAG workflow completed successfully")
            return dict(final_state)
            
        except Exception as e:
            log.error(f"RAG workflow failed: {e}")
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "confidence": 0.0,
                "past_steps": ["Workflow failed"],
                "context": ""
            }

# Global agent instance
plan_execute_agent = RAGAgent()

def get_agent() -> RAGAgent:
    """Get the global RAG agent instance."""
    return plan_execute_agent