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
        Build an optimized legal analysis prompt using IRAC methodology for litigation workflows.
        
        Args:
            question: User's legal question
            context_documents: Retrieved document content
            matter_type: Type of legal matter (litigation, tort, criminal, etc.)
            analysis_style: Style of analysis (comprehensive, concise, technical)
            
        Returns:
            Formatted prompt for legal analysis
        """
        
        # Optimized base instruction - reduced redundancy
        base_instruction = """You are a litigation analyst. Analyze ONLY information explicitly stated in the documents.

RULES:
- Quote directly from documents for factual claims
- State "Documents do not specify [X]" for missing information
- Distinguish document content from general legal principles
- Focus on party positions and argument strengths"""

        # Streamlined IRAC instruction
        irac_instruction = """Structure response using IRAC:

ISSUE: [Key legal issues and disputes between parties]
RULE: [Applicable legal rules - only cite if explicitly mentioned]
ANALYSIS: [Apply rules to facts, analyze party positions and argument strengths]
CONCLUSION: [Legal conclusion and assessment of party positions]"""

        # Condensed matter-specific guidance
        matter_focus = {
            "litigation": "Focus: plaintiff claims, defendant defenses, burden of proof, evidence analysis",
            "tort": "Focus: duty, breach, causation, damages assessment",
            "criminal": "Focus: elements, defenses, procedural issues",
            "civil_procedure": "Focus: procedural rules, jurisdiction, venue, evidence",
            "evidence": "Focus: admissibility, relevance, probative value",
            "constitutional": "Focus: constitutional rights, due process, equal protection"
        }
        
        matter_guidance = matter_focus.get(matter_type.lower(), "") if matter_type else ""
        
        # Streamlined style instructions
        style_focus = {
            "comprehensive": "Provide detailed analysis with citations, evidence assessment, and case strategy implications",
            "concise": "Provide focused analysis with key issues, essential positions, and direct application",
            "technical": "Provide technical analysis with precise terminology, statutory analysis, and expert reasoning"
        }
        
        style_instruction = style_focus.get(analysis_style, style_focus["comprehensive"])
        
        # Optimized context instruction
        context_instruction = f"""Documents: {context_documents}

REQUIREMENTS:
- Quote exact text: "According to Document X: [quote]"
- State "Documents do not contain [topic]" for missing info
- Label general principles as "General legal principle (not from documents)"
- Assess argument strengths and evidence quality"""

        # Efficient prompt assembly
        prompt = f"""{base_instruction}

{irac_instruction}

{matter_guidance}

{style_instruction}

{context_instruction}

QUESTION: {question}

ANALYSIS:"""
        
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
    def build_litigation_analysis_prompt(litigation_content: str, focus_area: Optional[str] = None) -> str:
        """Build a specialized prompt for litigation analysis."""
        
        base_instruction = """You are a litigation expert. Analyze this litigation case with focus on:

PARTY POSITIONS:
- Plaintiff's claims and legal arguments
- Defendant's defenses and counterarguments
- Burden of proof and evidentiary requirements
- Key factual disputes between parties

LEGAL ARGUMENTS:
- Strength of each party's legal position
- Applicable legal standards and precedents
- Procedural issues and jurisdictional questions
- Potential legal defenses and counterclaims

EVIDENCE ANALYSIS:
- Strength and admissibility of evidence
- Witness credibility and testimony analysis
- Documentary evidence and exhibits
- Expert testimony and technical evidence

CASE STRATEGY:
- Assessment of party argument strengths
- Potential settlement considerations
- Trial strategy implications
- Risk factors and outcome predictions"""
        
        focus_instruction = ""
        if focus_area:
            focus_areas = {
                "liability": "Focus on liability analysis, causation, and damages assessment.",
                "procedural": "Examine procedural issues, jurisdiction, venue, and discovery matters.",
                "evidence": "Analyze evidence strength, admissibility, and witness credibility.",
                "damages": "Focus on damages calculation, causation, and mitigation issues.",
                "defenses": "Examine available defenses, counterclaims, and affirmative defenses.",
                "settlement": "Analyze settlement prospects, risk assessment, and negotiation factors."
            }
            focus_instruction = f"\nSPECIAL FOCUS: {focus_areas.get(focus_area, '')}"
        
        return f"""{base_instruction}

{focus_instruction}

Litigation case to analyze:
{litigation_content}

Please provide your litigation analysis:"""
    
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