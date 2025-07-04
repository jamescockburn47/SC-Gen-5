"""
Legal-specific prompting strategies for LexCognito.
Implements IRAC methodology and other legal analysis frameworks.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LegalPromptBuilder:
    """Builds specialized prompts for legal analysis and reasoning."""
    
    @staticmethod
    def build_legal_analysis_prompt(
        question: str,
        context_documents: str,
        matter_type: Optional[str] = None,
        analysis_style: str = "comprehensive"
    ) -> str:
        """
        Build a structured legal analysis prompt using IRAC methodology.
        
        Args:
            question: User's legal question
            context_documents: Retrieved document content
            matter_type: Type of legal matter (contract, tort, criminal, etc.)
            analysis_style: Style of analysis (comprehensive, concise, technical)
            
        Returns:
            Formatted prompt for legal analysis
        """
        
        # Base legal analysis instruction with strict grounding
        base_instruction = """You are an expert legal analyst. You must ONLY analyze information explicitly contained in the provided documents. 

CRITICAL RULES:
- NEVER invent case names, statutes, dollar amounts, dates, or legal citations
- NEVER add details not explicitly stated in the documents
- If information is missing, state "The documents do not specify [missing information]"
- Quote directly from documents when making claims
- Clearly distinguish between document content and general legal principles"""
        
        # IRAC methodology instruction (mandatory structure)
        irac_instruction = """
MANDATORY: Structure your response using IRAC methodology. Begin each section with the exact headings shown:

ISSUE: [Identify the key legal issues presented]

RULE: [State the applicable legal rules - only cite rules explicitly mentioned in the documents or clearly state "General legal principle"]

ANALYSIS: [Apply the legal rules to the specific facts from the documents]

CONCLUSION: [Provide your legal conclusion based solely on the document evidence]

You MUST use these exact section headings in your response.
"""
        
        # Matter-specific guidance
        matter_guidance = ""
        if matter_type:
            matter_specific = {
                "contract": """
Focus on contract formation, terms, performance, breach, and remedies.
Consider: offer, acceptance, consideration, capacity, legality, and enforceability.
""",
                "tort": """
Focus on duty, breach, causation, and damages.
Consider: negligence, intentional torts, strict liability, and defenses.
""",
                "criminal": """
Focus on elements of the offense, defenses, and procedural issues.
Consider: mens rea, actus reus, causation, and constitutional protections.
""",
                "corporate": """
Focus on corporate governance, fiduciary duties, and regulatory compliance.
Consider: board responsibilities, shareholder rights, and statutory requirements.
""",
                "employment": """
Focus on employment relationships, discrimination, and workplace rights.
Consider: statutory protections, common law duties, and regulatory compliance.
""",
                "property": """
Focus on property rights, transfers, and disputes.
Consider: ownership, possession, easements, and regulatory restrictions.
"""
            }
            matter_guidance = matter_specific.get(matter_type.lower(), "")
        
        # Style-specific instructions
        style_instruction = ""
        if analysis_style == "comprehensive":
            style_instruction = """
Provide a detailed analysis with:
- Thorough examination of all relevant legal principles
- Citation to specific document sections where applicable
- Discussion of potential counterarguments
- Practical implications and recommendations
"""
        elif analysis_style == "concise":
            style_instruction = """
Provide a focused analysis with:
- Clear identification of key issues
- Essential legal principles
- Direct application to the facts
- Concise conclusion
"""
        elif analysis_style == "technical":
            style_instruction = """
Provide a technical analysis with:
- Precise legal terminology
- Detailed statutory and case law analysis
- Technical procedural considerations
- Expert-level legal reasoning
"""
        
        # Document context instruction with strict verification
        context_instruction = f"""
Base your analysis EXCLUSIVELY on the following legal documents:

{context_documents}

DOCUMENT ANALYSIS REQUIREMENTS:
1. Quote exact text from documents when making factual claims
2. Use format: "According to Document X: [exact quote]"
3. State "The documents do not contain information about [topic]" when information is missing
4. NEVER assume, infer, or speculate beyond what is explicitly written
5. If you reference legal principles, clearly label them as "General legal principle (not from documents)"

FORBIDDEN ACTIONS:
- Creating case citations not in the documents
- Inventing monetary amounts, dates, or specific legal provisions
- Adding narrative details not present in the source material"""
        
        # Final prompt assembly
        prompt = f"""{base_instruction}

{irac_instruction}

{matter_guidance}

{style_instruction}

{context_instruction}

LEGAL QUESTION: {question}

Please provide your legal analysis:"""
        
        return prompt
    
    @staticmethod
    def build_document_summary_prompt(document_content: str, summary_type: str = "executive") -> str:
        """Build a prompt for legal document summarization."""
        
        if summary_type == "executive":
            instruction = """Provide an executive summary highlighting:
- Key parties and their roles
- Main legal issues or transactions
- Critical dates and deadlines
- Essential terms and conditions
- Significant legal implications"""
        elif summary_type == "technical":
            instruction = """Provide a technical summary including:
- Detailed legal structure and provisions
- Regulatory compliance considerations
- Risk factors and mitigation strategies
- Procedural requirements and deadlines
- Technical legal terminology and definitions"""
        else:  # general
            instruction = """Provide a comprehensive summary covering:
- Document purpose and nature
- Key provisions and terms
- Parties involved
- Important dates and obligations
- Legal significance"""
        
        return f"""You are a legal expert specializing in document analysis. 

{instruction}

Document to analyze:
{document_content}

Please provide your summary:"""
    
    @staticmethod
    def build_contract_analysis_prompt(contract_content: str, focus_area: Optional[str] = None) -> str:
        """Build a specialized prompt for contract analysis."""
        
        base_instruction = """You are a contract law expert. Analyze this contract with focus on:

FORMATION ANALYSIS:
- Offer, acceptance, and consideration
- Capacity of parties
- Legality of subject matter

TERMS ANALYSIS:
- Key obligations of each party
- Performance requirements and deadlines
- Payment terms and conditions
- Risk allocation and liability

ENFORCEABILITY:
- Potential issues with enforceability
- Ambiguous or problematic clauses
- Missing or inadequate provisions

RISK ASSESSMENT:
- Potential areas of dispute
- Compliance requirements
- Termination and breach scenarios"""
        
        focus_instruction = ""
        if focus_area:
            focus_areas = {
                "performance": "Pay special attention to performance obligations, deadlines, and delivery requirements.",
                "liability": "Focus on liability provisions, indemnification clauses, and risk allocation.",
                "termination": "Examine termination clauses, notice requirements, and post-termination obligations.",
                "compliance": "Analyze regulatory compliance requirements and legal obligations.",
                "intellectual_property": "Focus on IP ownership, licensing, and protection provisions."
            }
            focus_instruction = f"\nSPECIAL FOCUS: {focus_areas.get(focus_area, '')}"
        
        return f"""{base_instruction}

{focus_instruction}

Contract to analyze:
{contract_content}

Please provide your analysis:"""
    
    @staticmethod
    def get_recommended_models_for_task(task_type: str) -> Dict[str, Any]:
        """Get recommended models for different legal tasks."""
        
        recommendations = {
            "legal_analysis": {
                "primary": "mistral:latest",
                "alternatives": ["mixtral:latest"],
                "reason": "Best for complex legal reasoning and text generation"
            },
            "document_classification": {
                "primary": "lawma-8b:latest", 
                "alternatives": ["mixtral:latest"],
                "reason": "Specialized for legal document classification tasks"
            },
            "contract_review": {
                "primary": "mistral:latest",
                "alternatives": ["mixtral:latest"],
                "reason": "Excellent for detailed contract analysis and risk assessment"
            },
            "legal_research": {
                "primary": "mistral:latest",
                "alternatives": ["mixtral:latest"],
                "reason": "Strong performance on legal research and citation analysis"
            },
            "case_summary": {
                "primary": "mistral:latest",
                "alternatives": ["mixtral:latest"],
                "reason": "Good at extracting key information and creating summaries"
            }
        }
        
        return recommendations.get(task_type, recommendations["legal_analysis"])


class LegalModelSelector:
    """Selects appropriate models for different legal tasks."""
    
    @staticmethod
    def select_model_for_query(query: str, available_models: list, task_hint: Optional[str] = None) -> str:
        """
        Select the best model for a given legal query.
        
        Args:
            query: User's legal question
            available_models: List of available model names
            task_hint: Hint about the type of task
            
        Returns:
            Recommended model name
        """
        
        # Keywords that indicate classification tasks (where lawma-8b is appropriate)
        classification_keywords = [
            "classify", "categorize", "type of", "kind of", "what category",
            "is this a", "classify this as", "determine the type"
        ]
        
        # Check if this is a classification task
        query_lower = query.lower()
        is_classification = any(keyword in query_lower for keyword in classification_keywords)
        
        # If it's classification and lawma-8b is available, use it
        if is_classification and "lawma-8b:latest" in available_models:
            return "lawma-8b:latest"
        
        # For all other tasks, prefer Mistral for legal analysis (best quality)
        if "mistral:latest" in available_models:
            return "mistral:latest"
        elif "mixtral:latest" in available_models:
            return "mixtral:latest"
        
        # Exclude phi3 completely - poor quality for legal work
        available_models_filtered = [m for m in available_models if "phi3" not in m]
        
        # Fallback to first non-phi3 model
        return available_models_filtered[0] if available_models_filtered else "mistral:latest"