"""
Strategic Counsel Protocols (v3) - Litigation Analysis & Quality Control

Implements sophisticated protocols for legal analysis, hallucination containment,
and adversarial reasoning without IRAC format.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ProtocolViolation:
    """Represents a protocol violation."""
    protocol: str
    rule: str
    severity: str  # "critical", "warning", "info"
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class ProtocolReport:
    """Comprehensive protocol compliance report."""
    overall_compliance: bool
    violations: List[ProtocolViolation]
    ethical_warnings: List[str]
    quality_score: float  # 0.0 to 1.0
    recommendations: List[str]

class StrategicProtocols:
    """Strategic Counsel Protocols implementation."""
    
    def __init__(self):
        self.protocols = {
            "M.A": {
                "name": "Hallucination Containment & Citation Discipline",
                "rules": {
                    "M.A.1": "No authority may be cited unless (1) uploaded by user, (2) verifiably public, or (3) clearly flagged as [UNVERIFIED].",
                    "M.A.2": "Unverified sources must display a plain-language disclaimer at the point of use.",
                    "M.A.3": "Fictional case names, statutes, or legal doctrines are strictly prohibited unless explicitly simulated and flagged.",
                    "M.A.4": "Reasoning chains containing unverifiable steps must suppress or label those segments and prevent downstream inference.",
                    "M.A.5": "Citations must include court, date, and jurisdiction where known, or mark as incomplete."
                }
            },
            "M.B": {
                "name": "Memory Integrity & Role Inference Safeguards",
                "rules": {
                    "M.B.1": "Prior memory may only be used if explicitly loaded in the current session or reiterated by the user.",
                    "M.B.2": "Role inference (e.g. claimant/respondent) must derive only from documents or user instructions.",
                    "M.B.3": "Avoid pattern-based inference unless explicitly requested.",
                    "M.B.4": "All assumed context must be tagged as [HYPOTHETICAL INFERENCE].",
                    "M.B.5": "Legal roles must be derived from document content, not position in dialogue or prior AI guesswork."
                }
            },
            "M.C": {
                "name": "Export Fidelity & Document Structure",
                "rules": {
                    "M.C.1": "All exportable outputs must maintain full structural integrity.",
                    "M.C.2": "Silent summarisation, truncation, or layout degradation is forbidden.",
                    "M.C.3": "Use legal drafting structure with correct section numbering and formatting.",
                    "M.C.4": "Placeholder content must be clearly marked: [[TO BE DRAFTED]].",
                    "M.C.5": "Outputs not meeting the structure must trigger a warning before export."
                }
            },
            "M.D": {
                "name": "Adversarial Reasoning & Legal Discipline",
                "rules": {
                    "M.D.1": "Prioritise doctrinal logic over persuasive or narrative framing.",
                    "M.D.2": "Flag strategic weaknesses or gaps in authority.",
                    "M.D.3": "Do not simulate judicial neutrality unless instructed; adopt adversarial clarity.",
                    "M.D.4": "Trace every argument to a grounded source (instruction, authority, principle).",
                    "M.D.5": "Ambiguity in procedural roles must prompt clarification, not assumption."
                }
            },
            "M.E": {
                "name": "Protocol Governance & Enforcement Rules",
                "rules": {
                    "M.E.1": "Protocol logic must be re-checked for every AI invocation.",
                    "M.E.2": "Conflicts between protocols and user requests must escalate by priority: M.E > M.A–D > user override.",
                    "M.E.3": "Partial enforcement (e.g. from token loss) must trigger a disclaimer.",
                    "M.E.4": "A sidebar button must run a 'Protocol Compliance Report' listing section-by-section adherence or red flags.",
                    "M.E.5": "Any degraded or disabled rule must be explicitly declared before proceeding."
                }
            },
            "M.F": {
                "name": "Output Presentation & Format Control",
                "rules": {
                    "M.F.1": "No compressed formats (slide, carousel) unless explicitly instructed.",
                    "M.F.2": "Avoid repetition or structural echo of boilerplate content.",
                    "M.F.3": "Litigation arguments must follow: issue → position → authority → rebuttal → conclusion.",
                    "M.F.4": "Default to user's adversarial position unless asked to balance.",
                    "M.F.5": "Output layout must be clean, court-appropriate, and export-safe."
                }
            },
            "M.G": {
                "name": "Jurisdictional and User Alignment",
                "rules": {
                    "M.G.1": "Default legal reasoning to UK commercial and competition litigation.",
                    "M.G.2": "Outputs must assume a senior solicitor or barrister audience.",
                    "M.G.3": "No overly introductory explanation unless instructed."
                }
            },
            "M.H": {
                "name": "Soft Ethics Signal Protocol (Experimental)",
                "rules": {
                    "M.H.1": "Flag results as ⚠️ ETHICAL AMBIGUITY DETECTED if reasoning is circular or incoherent, inferences exceed evidence, or strategic misrepresentation risk is high.",
                    "M.H.2": "This warning is advisory; it does not block export.",
                    "M.H.3": "Must be displayed if triggered, even if protocol compliance passes."
                }
            }
        }
    
    def build_litigation_prompt(self, question: str, context: str = "", user_position: str = "claimant") -> str:
        """Build a litigation-focused prompt without IRAC format."""
        
        base_prompt = f"""You are a senior litigation solicitor providing direct legal analysis. 

CONTEXT: {context if context else "No specific documents provided - general legal analysis"}

USER POSITION: {user_position.upper()}

QUESTION: {question}

ANALYSIS REQUIREMENTS:
- Provide direct, adversarial legal analysis without IRAC format
- Focus on doctrinal logic and strategic positioning
- Identify key legal issues and party positions
- Assess argument strengths and evidentiary gaps
- Consider procedural implications and tactical considerations
- Default to UK commercial and competition litigation context
- Assume senior solicitor/barrister audience

PROTOCOL COMPLIANCE:
- Cite only verifiable authorities or mark as [UNVERIFIED]
- Flag strategic weaknesses and gaps in authority
- Avoid pattern-based inference unless explicitly requested
- Tag hypothetical inferences as [HYPOTHETICAL INFERENCE]
- Prioritize doctrinal logic over narrative framing

RESPONSE FORMAT:
Provide a direct, sophisticated legal analysis that addresses the question with:
1. Key legal issues identified
2. Party positions and strategic considerations  
3. Authority and evidence assessment
4. Procedural and tactical implications
5. Risk assessment and recommendations

Answer:"""
        
        return base_prompt
    
    def analyze_compliance(self, response: str, question: str, context: str = "") -> ProtocolReport:
        """Analyze response for protocol compliance."""
        violations = []
        ethical_warnings = []
        
        # Check for unverified citations
        if "[UNVERIFIED]" not in response and any(cite in response.lower() for cite in ["case", "statute", "regulation", "act"]):
            violations.append(ProtocolViolation(
                protocol="M.A",
                rule="M.A.1",
                severity="warning",
                description="Potential unverified citations detected",
                suggestion="Add [UNVERIFIED] tags to citations not from provided documents"
            ))
        
        # Check for hypothetical inferences
        if any(word in response.lower() for word in ["assume", "presume", "likely", "probably"]) and "[HYPOTHETICAL INFERENCE]" not in response:
            violations.append(ProtocolViolation(
                protocol="M.B",
                rule="M.B.4",
                severity="info",
                description="Hypothetical inferences detected without proper tagging",
                suggestion="Tag assumptions as [HYPOTHETICAL INFERENCE]"
            ))
        
        # Check for IRAC format (should not be present)
        if any(phrase in response.lower() for phrase in ["issue:", "rule:", "analysis:", "conclusion:"]):
            violations.append(ProtocolViolation(
                protocol="M.F",
                rule="M.F.3",
                severity="critical",
                description="IRAC format detected - should be direct analysis",
                suggestion="Remove IRAC structure and provide direct legal analysis"
            ))
        
        # Check for boilerplate content
        boilerplate_phrases = [
            "it is important to note",
            "generally speaking",
            "in conclusion",
            "it should be noted"
        ]
        if any(phrase in response.lower() for phrase in boilerplate_phrases):
            violations.append(ProtocolViolation(
                protocol="M.F",
                rule="M.F.2",
                severity="warning",
                description="Boilerplate content detected",
                suggestion="Remove repetitive or generic phrases"
            ))
        
        # Check for ethical ambiguity
        if any(phrase in response.lower() for phrase in ["circular", "incoherent", "unclear", "ambiguous"]):
            ethical_warnings.append("⚠️ ETHICAL AMBIGUITY DETECTED: Reasoning may be circular or incoherent")
        
        # Calculate quality score
        total_checks = 8
        passed_checks = total_checks - len(violations)
        quality_score = max(0.0, passed_checks / total_checks)
        
        # Generate recommendations
        recommendations = []
        if violations:
            recommendations.append("Review and address protocol violations")
        if ethical_warnings:
            recommendations.append("Consider ethical implications of analysis")
        if quality_score < 0.8:
            recommendations.append("Improve overall protocol compliance")
        
        return ProtocolReport(
            overall_compliance=len([v for v in violations if v.severity == "critical"]) == 0,
            violations=violations,
            ethical_warnings=ethical_warnings,
            quality_score=quality_score,
            recommendations=recommendations
        )
    
    def get_protocols(self) -> Dict[str, Any]:
        """Get all protocols for frontend display."""
        return self.protocols
    
    def update_protocol(self, protocol_id: str, rule_id: str, new_rule: str) -> bool:
        """Update a specific protocol rule."""
        try:
            if protocol_id in self.protocols and rule_id in self.protocols[protocol_id]["rules"]:
                self.protocols[protocol_id]["rules"][rule_id] = new_rule
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update protocol: {e}")
            return False
    
    def save_protocols(self, filepath: str = "strategic_protocols.json") -> bool:
        """Save protocols to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.protocols, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save protocols: {e}")
            return False
    
    def load_protocols(self, filepath: str = "strategic_protocols.json") -> bool:
        """Load protocols from file."""
        try:
            if Path(filepath).exists():
                with open(filepath, 'r') as f:
                    self.protocols = json.load(f)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to load protocols: {e}")
            return False

# Global instance
strategic_protocols = StrategicProtocols() 