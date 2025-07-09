#!/usr/bin/env python3
"""
Backend Monitor Script
Continuously monitors the RAG backend server and provides diagnostics
"""

import time
import requests
import psutil
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend_monitor.log'),
        logging.StreamHandler()
    ]
)

class BackendMonitor:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.check_interval = 5  # seconds
        self.running = True
        self.crash_count = 0
        self.last_crash_time = None
        self.health_history = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info("Received shutdown signal, stopping monitor...")
        self.running = False
    
    def check_backend_health(self) -> Dict:
        """Check backend health and return status"""
        start_time = time.time()
        status = {
            'timestamp': datetime.now().isoformat(),
            'online': False,
            'response_time': 0,
            'error': None,
            'models': {},
            'documents': {},
            'system': {}
        }
        
        try:
            # Check basic connectivity
            response = requests.get(f"{self.base_url}/api/rag/status", timeout=10)
            status['response_time'] = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status['online'] = True
                data = response.json()
                status['models'] = data.get('models', {})
                status['system'] = {
                    'gpu_memory': data.get('gpu_memory', 0),
                    'cpu_usage': data.get('cpu_usage', 0)
                }
                
                # Check documents
                try:
                    docs_response = requests.get(f"{self.base_url}/api/rag/documents", timeout=5)
                    if docs_response.status_code == 200:
                        docs_data = docs_response.json()
                        status['documents'] = {
                            'count': len(docs_data.get('documents', [])),
                            'chunks': docs_data.get('total_chunks', 0)
                        }
                except Exception as e:
                    status['documents'] = {'error': str(e)}
                    
            else:
                status['error'] = f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            status['error'] = "Request timeout"
        except requests.exceptions.ConnectionError:
            status['error'] = "Connection refused - server may be down"
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def get_system_info(self) -> Dict:
        """Get system resource information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get Python processes
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available / (1024**3),  # GB
                'disk_percent': disk.percent,
                'disk_free': disk.free / (1024**3),  # GB
                'python_processes': python_processes
            }
        except Exception as e:
            return {'error': str(e)}
    
    def test_question_answering(self) -> Dict:
        """Test question answering functionality"""
        test_question = "What are the key points about document processing?"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/rag/answer",
                json={
                    'question': test_question,
                    'max_chunks': 5,
                    'min_relevance': 0.3,
                    'include_sources': True,
                    'response_style': 'detailed'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'confidence': data.get('confidence', 'N/A'),
                    'sources_count': len(data.get('sources', [])),
                    'answer_length': len(data.get('answer', ''))
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_crash(self, current_status: Dict, previous_status: Optional[Dict]) -> bool:
        """Detect if backend has crashed"""
        if not previous_status:
            return False
        
        # Check if server went from online to offline
        if previous_status.get('online', False) and not current_status.get('online', False):
            return True
        
        # Check for repeated errors
        if current_status.get('error') and previous_status.get('error') == current_status.get('error'):
            return True
        
        return False
    
    def generate_crash_report(self, status: Dict, system_info: Dict) -> str:
        """Generate detailed crash report"""
        report = f"""
=== BACKEND CRASH REPORT ===
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Crash Count: {self.crash_count}

LAST STATUS:
{json.dumps(status, indent=2)}

SYSTEM INFO:
{json.dumps(system_info, indent=2)}

RECOMMENDED ACTIONS:
1. Check server logs: tail -f app.log
2. Restart backend: python3 app.py
3. Check GPU memory: nvidia-smi
4. Monitor system resources: htop
5. Check port conflicts: netstat -tulpn | grep 8001

=== END REPORT ===
"""
        return report
    
    def restart_backend(self):
        """Attempt to restart the backend"""
        logging.info("Attempting to restart backend...")
        try:
            # Kill existing Python processes on port 8001
            subprocess.run(['pkill', '-f', 'python.*app.py'], check=False)
            time.sleep(2)
            
            # Start new backend process
            subprocess.Popen(['python3', 'app.py'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            logging.info("Backend restart initiated")
            
        except Exception as e:
            logging.error(f"Failed to restart backend: {e}")
    
    def run(self):
        """Main monitoring loop"""
        logging.info("Starting backend monitor...")
        previous_status = None
        
        while self.running:
            try:
                # Check backend health
                current_status = self.check_backend_health()
                system_info = self.get_system_info()
                
                # Store in history (keep last 100 entries)
                self.health_history.append(current_status)
                if len(self.health_history) > 100:
                    self.health_history.pop(0)
                
                # Log status
                if current_status['online']:
                    logging.info(f"✅ Backend online - {current_status['response_time']:.1f}ms")
                else:
                    logging.warning(f"❌ Backend offline - {current_status.get('error', 'Unknown error')}")
                
                # Detect crash
                if self.detect_crash(current_status, previous_status):
                    self.crash_count += 1
                    self.last_crash_time = datetime.now()
                    
                    logging.error("🚨 BACKEND CRASH DETECTED!")
                    crash_report = self.generate_crash_report(current_status, system_info)
                    logging.error(crash_report)
                    
                    # Save crash report to file
                    with open(f'crash_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'w') as f:
                        f.write(crash_report)
                    
                    # Optional: auto-restart (uncomment if desired)
                    # self.restart_backend()
                
                previous_status = current_status
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logging.info("Monitor stopped by user")
                break
            except Exception as e:
                logging.error(f"Monitor error: {e}")
                time.sleep(self.check_interval)
    
    def get_summary(self) -> Dict:
        """Get monitoring summary"""
        if not self.health_history:
            return {}
        
        online_count = sum(1 for status in self.health_history if status.get('online', False))
        total_checks = len(self.health_history)
        uptime_percentage = (online_count / total_checks) * 100 if total_checks > 0 else 0
        
        avg_response_time = sum(
            status.get('response_time', 0) for status in self.health_history 
            if status.get('online', False)
        ) / online_count if online_count > 0 else 0
        
        return {
            'total_checks': total_checks,
            'online_checks': online_count,
            'uptime_percentage': uptime_percentage,
            'avg_response_time': avg_response_time,
            'crash_count': self.crash_count,
            'last_crash': self.last_crash_time.isoformat() if self.last_crash_time else None
        }

def main():
    """Main entry point"""
    print("🔍 Backend Monitor Starting...")
    print("Monitoring http://localhost:8001")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    monitor = BackendMonitor()
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n📊 Monitoring Summary:")
        summary = monitor.get_summary()
        print(json.dumps(summary, indent=2))
        print("\n👋 Monitor stopped")

if __name__ == "__main__":
    main() 