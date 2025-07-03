"""Strategic legal protocols and prompts for SC Gen 5."""

import textwrap
from typing import Dict, List


class StrategicProtocols:
    """Strategic legal protocols and prompts for enhanced legal reasoning."""

    SYSTEM_PROMPT = textwrap.dedent("""
        You are a strategic legal counsel assistant with deep expertise in corporate law, 
        contract analysis, regulatory compliance, and litigation strategy. You provide 
        precise, actionable legal analysis based on the documents and context provided.

        Core Principles:
        1. ACCURACY: Base responses strictly on provided documents and legal precedent
        2. PRECISION: Be specific about legal risks, obligations, and opportunities  
        3. PRACTICALITY: Provide actionable recommendations and next steps
        4. CLARITY: Explain complex legal concepts in accessible language
        5. COMPLETENESS: Address all aspects of the query comprehensively

        When analyzing documents:
        - Identify key legal issues, risks, and obligations
        - Note any unusual or problematic clauses
        - Highlight missing standard protections
        - Consider commercial and strategic implications
        - Reference specific sections and provisions
        
        Always cite your sources and indicate confidence levels in your analysis.
    """).strip()

    CONTRACT_ANALYSIS_PROMPT = textwrap.dedent("""
        Analyze this contract focusing on:
        
        1. KEY TERMS & OBLIGATIONS
           - Primary obligations of each party
           - Performance standards and deadlines
           - Payment terms and conditions
           
        2. RISK ASSESSMENT
           - Liability exposure and limitations
           - Indemnification provisions
           - Force majeure and termination rights
           
        3. COMMERCIAL TERMS
           - Pricing structure and adjustments
           - Intellectual property rights
           - Confidentiality and non-compete clauses
           
        4. COMPLIANCE & REGULATORY
           - Regulatory compliance requirements
           - Data protection and privacy obligations
           - Industry-specific regulations
           
        5. DISPUTE RESOLUTION
           - Governing law and jurisdiction
           - Dispute resolution mechanisms
           - Escalation procedures
    """).strip()

    REGULATORY_ANALYSIS_PROMPT = textwrap.dedent("""
        Conduct regulatory analysis focusing on:
        
        1. COMPLIANCE REQUIREMENTS
           - Applicable laws and regulations
           - Licensing and registration requirements
           - Reporting and disclosure obligations
           
        2. RISK AREAS
           - Potential compliance gaps
           - Enforcement risks and penalties
           - Recent regulatory changes
           
        3. MITIGATION STRATEGIES
           - Recommended compliance measures
           - Policy and procedure updates
           - Training and awareness programs
    """).strip()

    LITIGATION_STRATEGY_PROMPT = textwrap.dedent("""
        Develop litigation strategy considering:
        
        1. LEGAL MERIT
           - Strength of legal claims/defenses
           - Burden of proof analysis
           - Procedural considerations
           
        2. EVIDENCE ASSESSMENT  
           - Key documentary evidence
           - Witness availability and credibility
           - Expert testimony requirements
           
        3. STRATEGIC CONSIDERATIONS
           - Cost-benefit analysis
           - Timeline and resource requirements
           - Settlement opportunities
           
        4. RISK MANAGEMENT
           - Potential adverse outcomes
           - Reputational implications
           - Business continuity impact
    """).strip()

    DUE_DILIGENCE_PROMPT = textwrap.dedent("""
        Perform due diligence review focusing on:
        
        1. CORPORATE STRUCTURE
           - Entity formation and ownership
           - Board composition and governance
           - Subsidiary and affiliate relationships
           
        2. FINANCIAL ANALYSIS
           - Financial statements and audits
           - Debt obligations and guarantees
           - Material contracts and commitments
           
        3. LEGAL COMPLIANCE
           - Litigation history and pending matters
           - Regulatory compliance status
           - Intellectual property portfolio
           
        4. OPERATIONAL RISKS
           - Key personnel and employment matters
           - Environmental liabilities
           - Insurance coverage and claims
    """).strip()

    @classmethod
    def get_prompt_for_matter_type(cls, matter_type: str) -> str:
        """Get specialized prompt based on matter type."""
        prompts = {
            "contract": cls.CONTRACT_ANALYSIS_PROMPT,
            "regulatory": cls.REGULATORY_ANALYSIS_PROMPT,
            "litigation": cls.LITIGATION_STRATEGY_PROMPT,
            "due_diligence": cls.DUE_DILIGENCE_PROMPT,
        }
        return prompts.get(matter_type.lower(), cls.SYSTEM_PROMPT)

    @classmethod
    def build_rag_prompt(
        cls,
        question: str,
        context: str,
        matter_type: str | None = None,
        matter_id: str | None = None,
    ) -> str:
        """Build complete RAG prompt with context and protocols."""
        
        # Get appropriate prompt template
        if matter_type:
            specific_prompt = cls.get_prompt_for_matter_type(matter_type)
        else:
            specific_prompt = cls.SYSTEM_PROMPT

        prompt = f"""
{cls.SYSTEM_PROMPT}

{specific_prompt if matter_type else ""}

CONTEXT DOCUMENTS:
{context}

QUESTION: {question}

ANALYSIS:
Please provide a comprehensive analysis addressing the question based on the context documents provided.

IMPORTANT GUIDELINES:
1. If the document content appears garbled, unclear, or contains OCR artifacts, clearly state this limitation
2. Only analyze content that is clearly readable and makes logical sense
3. If the documents don't contain sufficient clear information to answer the question, state this explicitly
4. Do not fabricate or hallucinate content that isn't clearly present in the documents
5. Acknowledge any uncertainty about document content quality

Structure your response clearly with headings and bullet points where appropriate.
Cite specific document sections only when the content is clearly readable.

""".strip()

        return prompt

    @classmethod
    def build_standalone_prompt(
        cls,
        question: str,
        matter_type: str | None = None,
        matter_id: str | None = None,
    ) -> str:
        """Build standalone legal prompt without document context."""
        
        # Get appropriate prompt template
        if matter_type:
            specific_prompt = cls.get_prompt_for_matter_type(matter_type)
        else:
            specific_prompt = cls.SYSTEM_PROMPT

        prompt = f"""
{cls.SYSTEM_PROMPT}

{specific_prompt if matter_type else ""}

QUESTION: {question}

ANALYSIS:
Please provide a comprehensive legal analysis addressing this question based on your knowledge of law and legal principles.
Focus on providing practical, actionable advice while noting any areas where specific document review or further research may be needed.
Structure your response clearly with headings and bullet points where appropriate.

""".strip()

        return prompt

    @classmethod
    def get_matter_types(cls) -> List[str]:
        """Get list of supported matter types."""
        return ["contract", "regulatory", "litigation", "due_diligence"]

    @classmethod
    def get_legal_keywords(cls) -> Dict[str, List[str]]:
        """Get legal keywords for enhanced document processing."""
        return {
            "contract_terms": [
                "agreement", "contract", "terms", "conditions", "obligations",
                "warranties", "representations", "indemnification", "liability",
                "termination", "breach", "default", "cure", "notice"
            ],
            "financial_terms": [
                "payment", "fees", "costs", "expenses", "price", "consideration",
                "invoice", "billing", "refund", "penalty", "interest", "damages"
            ],
            "intellectual_property": [
                "copyright", "trademark", "patent", "trade secret", "confidential",
                "proprietary", "license", "assignment", "ownership", "infringement"
            ],
            "regulatory": [
                "compliance", "regulation", "statute", "law", "requirement",
                "prohibition", "permit", "license", "approval", "filing", "disclosure"
            ],
            "litigation": [
                "claim", "lawsuit", "court", "judgment", "settlement", "discovery",
                "evidence", "witness", "testimony", "appeal", "arbitration", "mediation"
            ],
            "corporate": [
                "board", "director", "officer", "shareholder", "equity", "governance",
                "fiduciary", "merger", "acquisition", "subsidiary", "affiliate"
            ]
        } 