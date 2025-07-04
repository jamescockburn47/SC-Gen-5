"""Simple interface to Official Gemini CLI for Strategic Counsel Gen 5."""

import os
import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OfficialGeminiCLI:
    """Simple interface to Google's official Gemini CLI."""
    
    def __init__(self):
        """Initialize simple Gemini CLI interface."""
        pass
    
    def check_availability(self) -> Dict[str, Any]:
        """Check if Gemini CLI is available."""
        try:
            # Check if node is available
            node_result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            node_available = node_result.returncode == 0
            
            # Check if npm is available
            try:
                npm_result = subprocess.run(
                    ["npm", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                npm_available = npm_result.returncode == 0
            except Exception:
                npm_available = False
            
            return {
                "available": node_available and npm_available,
                "node_version": node_result.stdout.strip() if node_available else None,
                "npm_available": npm_available
            }
            
        except Exception as e:
            logger.error(f"Error checking Gemini CLI availability: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def run_command(self, command: str, timeout: int = 30) -> str:
        """Run a command with the official Gemini CLI."""
        try:
            # Use npx to run the official Gemini CLI
            full_command = ["npx", "--yes", "https://github.com/google-gemini/gemini-cli"]
            
            # Add the user's command as input
            process = subprocess.run(
                full_command,
                input=command,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            if process.returncode == 0:
                return process.stdout or "Command completed successfully"
            else:
                return f"Error: {process.stderr or 'Unknown error'}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            logger.error(f"Error running Gemini CLI command: {e}")
            return f"Error: {str(e)}"
    
    def get_help(self) -> str:
        """Get help for the Gemini CLI."""
        try:
            result = subprocess.run(
                ["npx", "--yes", "https://github.com/google-gemini/gemini-cli", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return "Help not available"
                
        except Exception as e:
            return f"Error getting help: {e}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for the Gemini CLI."""
        availability = self.check_availability()
        
        return {
            "type": "official_gemini_cli",
            "cli_available": availability["available"],
            "node_version": availability.get("node_version"),
            "npm_available": availability.get("npm_available", False),
            "capabilities": [
                "Repository analysis",
                "Code generation", 
                "File editing",
                "Terminal commands",
                "Web search"
            ] if availability["available"] else []
        } 