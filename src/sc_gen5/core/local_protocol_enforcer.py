"""
Local Protocol Enforcer using Mistral-7B-Instruct

Provides real-time protocol compliance analysis and enforcement
using the local Mistral model for cost-effective, private validation.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import local model components
from ..rag.v2.models import ModelManager
from .strategic_protocols import StrategicProtocols, ProtocolViolation, ProtocolReport

logger = logging.getLogger(__name__)

@dataclass
class EnforcementResult:
    """Result of local protocol enforcement."""
    is_compliant: bool
    violations: List[ProtocolViolation]
    suggestions: List[str]
    confidence: float  # 0.0 to 1.0
    processing_time: float
    model_used: str

class LocalProtocolEnforcer:
    """Local protocol enforcement using Mistral-7B-Instruct."""
    
    def __init__(self):
        self.strategic_protocols = StrategicProtocols()
        self.local_model = None
        self.model_loaded = False
        
    def load_model(self) -> bool:
        """Load the local Mistral model for protocol enforcement."""
        try:
            logger.info("Loading local Mistral model for protocol enforcement...")
            model_manager = ModelManager()
            tokenizer, model = model_manager.load_generator_model()
            self.local_model = model
            self.model_loaded = True
            logger.info("✓ Local protocol enforcement model loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            return False
    
    def enforce_protocols(self, 
                         cloud_response: str, 
                         original_question: str,
                         context: str = "",
                         user_position: str = "claimant") -> EnforcementResult:
        """
        Enforce protocols on cloud response using local Mistral.
        
        This provides real-time, cost-effective protocol validation without
        sending the full response back to cloud APIs.
        """
        if not self.model_loaded:
            if not self.load_model():
                return self._fallback_enforcement(cloud_response, original_question, context, user_position)
        
        start_time = time.time()
        
        try:
            # Create enforcement prompt
            enforcement_prompt = self._build_enforcement_prompt(
                cloud_response, original_question, context, user_position
            )
            
            # Check if model is loaded
            if self.local_model is None:
                raise ValueError("Local model not loaded")
            
            # Generate enforcement analysis using llama.cpp interface
            enforcement_analysis = self.local_model(
                enforcement_prompt,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent analysis
                stop=["\n\n", "---", "END"]
            )
            
            # Extract text from llama.cpp response
            if isinstance(enforcement_analysis, dict) and 'choices' in enforcement_analysis:
                enforcement_analysis = enforcement_analysis['choices'][0]['text']
            else:
                enforcement_analysis = str(enforcement_analysis)
            
            # Parse enforcement results
            result = self._parse_enforcement_result(enforcement_analysis)
            result.processing_time = time.time() - start_time
            result.model_used = "mistral-7b-instruct-local"
            
            logger.info(f"Protocol enforcement completed in {result.processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Local enforcement failed: {e}")
            return self._fallback_enforcement(cloud_response, original_question, context, user_position)
    
    def _build_enforcement_prompt(self, 
                                 cloud_response: str, 
                                 original_question: str,
                                 context: str,
                                 user_position: str) -> str:
        """Build prompt for local protocol enforcement."""
        
        protocols = self.strategic_protocols.get_protocols()
        
        prompt = f"""You are a legal protocol compliance expert. Analyze the following legal response for protocol violations.

ORIGINAL QUESTION: {original_question}
USER POSITION: {user_position}
CONTEXT: {context if context else "No specific context provided"}

CLOUD RESPONSE TO ANALYZE:
{cloud_response}

PROTOCOLS TO ENFORCE:
"""
        
        # Add key protocols for enforcement
        key_protocols = ["M.A", "M.B", "M.D", "M.F", "M.H"]  # Most critical protocols
        for protocol_id in key_protocols:
            if protocol_id in protocols:
                protocol = protocols[protocol_id]
                prompt += f"\n{protocol_id}: {protocol['name']}\n"
                for rule_id, rule in protocol['rules'].items():
                    prompt += f"  {rule_id}: {rule}\n"
        
        prompt += """
ANALYSIS REQUIREMENTS:
1. Check for unverified citations (should be marked [UNVERIFIED])
2. Identify hypothetical inferences (should be marked [HYPOTHETICAL INFERENCE])
3. Detect IRAC format usage (should be direct analysis)
4. Find boilerplate or repetitive content
5. Assess ethical ambiguity (circular reasoning, incoherent logic)
6. Check for strategic weaknesses or gaps in authority

OUTPUT FORMAT:
Provide a JSON response with the following structure:
{
  "is_compliant": boolean,
  "violations": [
    {
      "protocol": "M.A",
      "rule": "M.A.1", 
      "severity": "critical|warning|info",
      "description": "specific violation description",
      "suggestion": "how to fix"
    }
  ],
  "suggestions": ["list of improvement suggestions"],
  "confidence": 0.85,
  "ethical_warnings": ["any ethical concerns"]
}

Focus on the most critical violations that affect legal accuracy and professional standards.
"""
        
        return prompt
    
    def _parse_enforcement_result(self, analysis: str) -> EnforcementResult:
        """Parse the local model's enforcement analysis."""
        try:
            # Extract JSON from analysis
            json_start = analysis.find('{')
            json_end = analysis.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in analysis")
            
            json_str = analysis[json_start:json_end]
            result_data = json.loads(json_str)
            
            # Convert to EnforcementResult
            violations = []
            for v in result_data.get('violations', []):
                violations.append(ProtocolViolation(
                    protocol=v.get('protocol', ''),
                    rule=v.get('rule', ''),
                    severity=v.get('severity', 'warning'),
                    description=v.get('description', ''),
                    suggestion=v.get('suggestion', '')
                ))
            
            return EnforcementResult(
                is_compliant=result_data.get('is_compliant', False),
                violations=violations,
                suggestions=result_data.get('suggestions', []),
                confidence=result_data.get('confidence', 0.5),
                processing_time=0.0,  # Will be set by caller
                model_used=""
            )
            
        except Exception as e:
            logger.error(f"Failed to parse enforcement result: {e}")
            return self._create_fallback_result()
    
    def _fallback_enforcement(self, 
                             cloud_response: str, 
                             original_question: str,
                             context: str,
                             user_position: str) -> EnforcementResult:
        """Fallback enforcement using basic rule checking."""
        logger.warning("Using fallback protocol enforcement")
        
        violations = []
        suggestions = []
        
        # Basic rule checking
        if "[UNVERIFIED]" not in cloud_response and any(cite in cloud_response.lower() for cite in ["case", "statute", "regulation"]):
            violations.append(ProtocolViolation(
                protocol="M.A",
                rule="M.A.1",
                severity="warning",
                description="Potential unverified citations detected",
                suggestion="Add [UNVERIFIED] tags to citations not from provided documents"
            ))
        
        if any(phrase in cloud_response.lower() for phrase in ["issue:", "rule:", "analysis:", "conclusion:"]):
            violations.append(ProtocolViolation(
                protocol="M.F",
                rule="M.F.3",
                severity="critical",
                description="IRAC format detected - should be direct analysis",
                suggestion="Remove IRAC structure and provide direct legal analysis"
            ))
        
        return EnforcementResult(
            is_compliant=len([v for v in violations if v.severity == "critical"]) == 0,
            violations=violations,
            suggestions=suggestions,
            confidence=0.6,  # Lower confidence for fallback
            processing_time=0.1,
            model_used="fallback-rules"
        )
    
    def _create_fallback_result(self) -> EnforcementResult:
        """Create a basic fallback result."""
        return EnforcementResult(
            is_compliant=True,
            violations=[],
            suggestions=["Consider manual review of response"],
            confidence=0.5,
            processing_time=0.0,
            model_used="fallback"
        )
    
    def enhance_cloud_prompt(self, 
                           original_question: str,
                           context: str = "",
                           user_position: str = "claimant") -> str:
        """
        Enhance cloud prompts using local Mistral to improve protocol compliance.
        
        This pre-processes questions to encourage better protocol adherence
        before sending to cloud APIs.
        """
        if not self.model_loaded:
            if not self.load_model():
                return original_question  # Return original if model not available
        
        try:
            # Check if model is loaded
            if self.local_model is None:
                return original_question
            
            enhancement_prompt = f"""You are a legal prompt enhancement expert. Improve the following legal question to encourage better protocol compliance.

ORIGINAL QUESTION: {original_question}
USER POSITION: {user_position}
CONTEXT: {context if context else "No specific context provided"}

ENHANCEMENT REQUIREMENTS:
1. Encourage direct legal analysis without IRAC format
2. Request specific citations with verification status
3. Ask for strategic positioning and tactical considerations
4. Emphasize doctrinal logic over narrative framing
5. Request identification of gaps in authority
6. Encourage adversarial clarity and precision

IMPROVED QUESTION:
"""
            
            enhanced_response = self.local_model(
                enhancement_prompt,
                max_tokens=300,
                temperature=0.3,
                stop=["\n\n", "---", "END"]
            )
            
            # Extract text from llama.cpp response
            if isinstance(enhanced_response, dict) and 'choices' in enhanced_response:
                enhanced_question = enhanced_response['choices'][0]['text']
            elif isinstance(enhanced_response, dict) and 'generated_text' in enhanced_response:
                enhanced_question = enhanced_response['generated_text']
            else:
                enhanced_question = str(enhanced_response)
            
            # Clean up the enhanced question
            enhanced_question = enhanced_question.strip()
            
            # Only return enhanced question if it's actually an enhancement
            if enhanced_question and len(enhanced_question) > len(original_question) * 0.8:
                logger.info("Question enhanced for better protocol compliance")
                return enhanced_question
            else:
                logger.info("Question enhancement failed or produced invalid result, using original")
                return original_question
                
        except Exception as e:
            logger.error(f"Prompt enhancement failed: {e}")
            return original_question
    
    def get_enforcement_stats(self) -> Dict[str, Any]:
        """Get statistics about protocol enforcement."""
        return {
            "model_loaded": self.model_loaded,
            "model_name": "mistral-7b-instruct-local" if self.model_loaded else "none",
            "strategic_protocols": len(self.strategic_protocols.get_protocols()),
            "enforcement_capabilities": [
                "Real-time protocol validation",
                "Citation verification checking",
                "IRAC format detection",
                "Boilerplate content identification",
                "Ethical ambiguity detection",
                "Strategic weakness assessment"
            ]
        }

# Global instance
local_enforcer = LocalProtocolEnforcer() 