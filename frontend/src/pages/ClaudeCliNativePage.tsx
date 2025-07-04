import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  Paper,
  Divider
} from '@mui/material';
import {
  Terminal as TerminalIcon,
  PlayArrow as ConnectIcon,
  Stop as DisconnectIcon,
  Clear as ClearIcon,
  Send as SendIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import axios from 'axios';

interface ClaudeSession {
  session_id: string;
  websocket_url: string;
  status: string;
}

interface ClaudeMessage {
  type: 'connected' | 'output' | 'error' | 'input';
  content: string;
  timestamp?: Date;
  working_directory?: string;
}

const ClaudeCliNativePage: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentSession, setCurrentSession] = useState<ClaudeSession | null>(null);
  const [messages, setMessages] = useState<ClaudeMessage[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [claudeStatus, setClaudeStatus] = useState<'checking' | 'available' | 'unavailable'>('checking');
  const [claudeInfo, setClaudeInfo] = useState<any>(null);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check Claude CLI status on mount
  useEffect(() => {
    checkClaudeStatus();
  }, []);

  // Auto-scroll terminal to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input when connected
  useEffect(() => {
    if (isConnected && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isConnected]);

  const checkClaudeStatus = async () => {
    try {
      const response = await axios.get('/api/claude-cli/status');
      setClaudeInfo(response.data);
      setClaudeStatus(response.data.available ? 'available' : 'unavailable');
    } catch (error) {
      console.error('Failed to check Claude CLI status:', error);
      setClaudeStatus('unavailable');
    }
  };

  const createSession = async () => {
    try {
      const response = await axios.post('/api/claude-cli/sessions');
      setCurrentSession(response.data);
      connectWebSocket(response.data);
    } catch (error) {
      console.error('Failed to create session:', error);
      addMessage({
        type: 'error',
        content: `Failed to create session: ${error}`,
        timestamp: new Date()
      });
    }
  };

  const connectWebSocket = (session: ClaudeSession) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/claude-cli/${session.session_id}`;
    
    websocketRef.current = new WebSocket(wsUrl);
    
    websocketRef.current.onopen = () => {
      setIsConnected(true);
      addMessage({
        type: 'connected',
        content: 'Connected to Claude CLI',
        timestamp: new Date()
      });
    };
    
    websocketRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        addMessage({
          ...message,
          timestamp: new Date()
        });
      } catch (error) {
        addMessage({
          type: 'error',
          content: `Message parse error: ${error}`,
          timestamp: new Date()
        });
      }
    };
    
    websocketRef.current.onclose = () => {
      setIsConnected(false);
      addMessage({
        type: 'error',
        content: 'Disconnected from Claude CLI',
        timestamp: new Date()
      });
    };
    
    websocketRef.current.onerror = (error) => {
      addMessage({
        type: 'error',
        content: `WebSocket error: ${error}`,
        timestamp: new Date()
      });
    };
  };

  const disconnect = async () => {
    if (websocketRef.current) {
      websocketRef.current.send(JSON.stringify({
        type: 'close'
      }));
      websocketRef.current.close();
    }
    
    if (currentSession) {
      try {
        await axios.delete(`/api/claude-cli/sessions/${currentSession.session_id}`);
      } catch (error) {
        console.error('Failed to terminate session:', error);
      }
    }
    
    setIsConnected(false);
    setCurrentSession(null);
  };

  const sendInput = () => {
    if (!currentInput.trim() || !websocketRef.current || !isConnected) return;

    // Add input to terminal display
    addMessage({
      type: 'input',
      content: `> ${currentInput}`,
      timestamp: new Date()
    });

    // Send to Claude CLI
    websocketRef.current.send(JSON.stringify({
      type: 'input',
      content: currentInput
    }));

    setCurrentInput('');
  };

  const sendInterrupt = () => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({
        type: 'interrupt'
      }));
      addMessage({
        type: 'input',
        content: '^C (Interrupt)',
        timestamp: new Date()
      });
    }
  };

  const addMessage = useCallback((message: ClaudeMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const clearTerminal = () => {
    setMessages([]);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      sendInput();
    } else if (event.ctrlKey && event.key === 'c') {
      event.preventDefault();
      sendInterrupt();
    }
  };

  const getMessageColor = (type: string) => {
    switch (type) {
      case 'connected': return '#4caf50';
      case 'output': return '#ffffff';
      case 'error': return '#f44336';
      case 'input': return '#2196f3';
      default: return '#ffffff';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <TerminalIcon sx={{ fontSize: 40 }} />
        Claude Code CLI - LexCognito Integration
      </Typography>

      {claudeStatus === 'unavailable' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Claude CLI is not available. Please ensure Claude Code is installed and accessible.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Status Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Claude CLI Status</Typography>
              <Box sx={{ mb: 2 }}>
                <Chip 
                  label={claudeStatus} 
                  color={claudeStatus === 'available' ? 'success' : 'error'}
                  variant="outlined"
                />
              </Box>
              
              {claudeInfo && (
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Version: {claudeInfo.version || 'Unknown'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Working Dir: {claudeInfo.working_directory || 'Unknown'}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {!isConnected ? (
                  <Button
                    variant="contained"
                    startIcon={<ConnectIcon />}
                    onClick={createSession}
                    disabled={claudeStatus !== 'available'}
                    size="small"
                  >
                    Connect
                  </Button>
                ) : (
                  <Button
                    variant="outlined"
                    startIcon={<DisconnectIcon />}
                    onClick={disconnect}
                    color="error"
                    size="small"
                  >
                    Disconnect
                  </Button>
                )}
                
                <Tooltip title="Refresh Status">
                  <IconButton onClick={checkClaudeStatus} size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Clear Terminal">
                  <IconButton onClick={clearTerminal} size="small">
                    <ClearIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Terminal Interface */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 1 }}>
              <Typography variant="h6" gutterBottom sx={{ px: 2, py: 1 }}>
                Terminal Output
              </Typography>
              <Divider />
              
              {/* Terminal Output */}
              <Paper
                ref={terminalRef}
                sx={{
                  flexGrow: 1,
                  backgroundColor: '#1e1e1e',
                  color: '#ffffff',
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                  fontSize: '14px',
                  p: 2,
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}
              >
                {messages.length === 0 ? (
                  <Typography sx={{ color: '#888', fontStyle: 'italic' }}>
                    Connect to Claude CLI to start your session...
                  </Typography>
                ) : (
                  messages.map((message, index) => (
                    <Box key={index} sx={{ color: getMessageColor(message.type), mb: 0.5 }}>
                      {message.type === 'input' ? (
                        <span style={{ color: '#2196f3' }}>{message.content}</span>
                      ) : (
                        message.content
                      )}
                    </Box>
                  ))
                )}
              </Paper>
              
              {/* Input Area */}
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <TextField
                  ref={inputRef}
                  fullWidth
                  size="small"
                  variant="outlined"
                  placeholder={isConnected ? "Type your message to Claude..." : "Connect first to enable input"}
                  value={currentInput}
                  onChange={(e) => setCurrentInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={!isConnected}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      fontFamily: 'Monaco, Consolas, "Courier New", monospace'
                    }
                  }}
                />
                <Button
                  variant="contained"
                  onClick={sendInput}
                  disabled={!isConnected || !currentInput.trim()}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  <SendIcon />
                </Button>
              </Box>
              
              <Typography variant="caption" sx={{ mt: 1, color: 'text.secondary' }}>
                Press Enter to send, Ctrl+C to interrupt
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Session Info */}
      {currentSession && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Session Information</Typography>
            <Typography variant="body2" color="textSecondary">
              Session ID: {currentSession.session_id}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Status: {isConnected ? 'Connected' : 'Disconnected'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Messages: {messages.length}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ClaudeCliNativePage;