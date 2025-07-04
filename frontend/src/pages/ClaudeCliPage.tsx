import React, { useState, useRef, useEffect } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  Chip,
  Alert,
  Grid,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Terminal as TerminalIcon,
  Send as SendIcon,
  Clear as ClearIcon,
  History as HistoryIcon,
  Code as CodeIcon,
  BugReport as BugIcon,
  Description as DocsIcon,
  Architecture as ArchIcon,
  TestTube as TestIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  FileCopy as CopyIcon
} from '@mui/icons-material';
import axios from 'axios';

interface ClaudeSession {
  id: string;
  query: string;
  response: string;
  timestamp: Date;
  duration?: number;
}

const ClaudeCliPage: React.FC = () => {
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<ClaudeSession[]>([]);
  const [claudeStatus, setClaudeStatus] = useState<'checking' | 'available' | 'unavailable'>('checking');
  
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new sessions arrive
  useEffect(() => {
    sessionsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions]);

  // Check Claude CLI status on mount
  useEffect(() => {
    checkClaudeStatus();
  }, []);

  const checkClaudeStatus = async () => {
    try {
      const response = await axios.post('/api/claude-cli/status');
      setClaudeStatus(response.data.available ? 'available' : 'unavailable');
    } catch (error) {
      console.error('Failed to check Claude CLI status:', error);
      setClaudeStatus('unavailable');
    }
  };

  const executeClaudeQuery = async (query: string) => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    const startTime = Date.now();

    try {
      const response = await axios.post('/api/claude-cli/execute', {
        query: query,
        cwd: '.'  // Frontend doesn't have process.cwd, backend will use its working directory
      });

      const duration = Date.now() - startTime;
      const newSession: ClaudeSession = {
        id: Date.now().toString(),
        query: query,
        response: response.data.output || 'No output received',
        timestamp: new Date(),
        duration: duration
      };

      setSessions(prev => [...prev, newSession]);
      setCurrentQuery('');

    } catch (error) {
      const duration = Date.now() - startTime;
      const errorSession: ClaudeSession = {
        id: Date.now().toString(),
        query: query,
        response: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
        duration: duration
      };
      setSessions(prev => [...prev, errorSession]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeClaudeQuery(currentQuery);
    }
  };

  const clearSessions = () => {
    setSessions([]);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const quickCommands = [
    {
      icon: <ArchIcon />,
      label: 'Analyze Architecture',
      query: 'Analyze this codebase architecture, identify patterns, and suggest improvements'
    },
    {
      icon: <BugIcon />,
      label: 'Find Issues',
      query: 'Review this code for bugs, security issues, and performance problems'
    },
    {
      icon: <TestIcon />,
      label: 'Suggest Tests',
      query: 'Suggest unit tests for the main components of this codebase'
    },
    {
      icon: <DocsIcon />,
      label: 'Generate README',
      query: 'Generate a comprehensive README.md for this project'
    },
    {
      icon: <CodeIcon />,
      label: 'Explain Code',
      query: 'Explain the overall architecture and how this system works'
    },
    {
      icon: <RefreshIcon />,
      label: 'Refactor Tips',
      query: 'Suggest refactoring opportunities to improve code quality'
    }
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <TerminalIcon sx={{ fontSize: 40 }} />
        Claude Code CLI Interface
      </Typography>

      {/* Status Alert */}
      {claudeStatus === 'unavailable' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Claude Code CLI is not available. Please ensure it's installed and accessible.
        </Alert>
      )}

      {claudeStatus === 'checking' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Checking Claude Code CLI status...
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Main Interface */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <CardContent sx={{ borderBottom: 1, borderColor: 'divider', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip
                    icon={<TerminalIcon />}
                    label={`${sessions.length} queries executed`}
                    color="primary"
                    variant="outlined"
                  />
                  {claudeStatus === 'available' && (
                    <Chip label="Claude CLI Ready" color="success" variant="outlined" />
                  )}
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Clear History">
                    <IconButton onClick={clearSessions} disabled={sessions.length === 0}>
                      <ClearIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Refresh Status">
                    <IconButton onClick={checkClaudeStatus}>
                      <RefreshIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            </CardContent>

            {/* Sessions Area */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
              {sessions.length === 0 ? (
                <Box sx={{ textAlign: 'center', mt: 4 }}>
                  <TerminalIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Welcome to Claude Code CLI
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Interact directly with Claude Code CLI for advanced code analysis and assistance.
                  </Typography>
                </Box>
              ) : (
                <List>
                  {sessions.map((session) => (
                    <ListItem key={session.id} sx={{ flexDirection: 'column', alignItems: 'stretch', mb: 2 }}>
                      {/* Query */}
                      <Paper
                        sx={{
                          p: 2,
                          bgcolor: 'primary.light',
                          color: 'primary.contrastText',
                          alignSelf: 'flex-end',
                          maxWidth: '80%',
                          mb: 1
                        }}
                      >
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                          {session.query}
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                          <Typography variant="caption" color="inherit">
                            {session.timestamp.toLocaleTimeString()}
                          </Typography>
                          <IconButton size="small" onClick={() => copyToClipboard(session.query)}>
                            <CopyIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Paper>

                      {/* Response */}
                      <Paper
                        sx={{
                          p: 2,
                          bgcolor: 'background.paper',
                          alignSelf: 'flex-start',
                          maxWidth: '95%',
                          border: 1,
                          borderColor: 'divider'
                        }}
                      >
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                          {session.response}
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {session.duration && `Completed in ${session.duration}ms`}
                          </Typography>
                          <IconButton size="small" onClick={() => copyToClipboard(session.response)}>
                            <CopyIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Paper>
                    </ListItem>
                  ))}
                  
                  {isLoading && (
                    <ListItem>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                          Executing Claude Code CLI query...
                        </Typography>
                      </Box>
                    </ListItem>
                  )}
                </List>
              )}
              <div ref={sessionsEndRef} />
            </Box>

            {/* Input Area */}
            <CardContent sx={{ borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  placeholder="Enter your Claude Code CLI query..."
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading || claudeStatus !== 'available'}
                  inputRef={inputRef}
                />
                <Button
                  variant="contained"
                  endIcon={<SendIcon />}
                  onClick={() => executeClaudeQuery(currentQuery)}
                  disabled={isLoading || !currentQuery.trim() || claudeStatus !== 'available'}
                  sx={{ minWidth: 100 }}
                >
                  Execute
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Quick Commands */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Commands
                </Typography>
                
                <Grid container spacing={1}>
                  {quickCommands.map((cmd, index) => (
                    <Grid item xs={12} key={index}>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={cmd.icon}
                        onClick={() => setCurrentQuery(cmd.query)}
                        disabled={claudeStatus !== 'available'}
                        sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                      >
                        {cmd.label}
                      </Button>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>

            {/* Usage Tips */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Usage Tips
                </Typography>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Effective Commands</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">
                      • Be specific about what you want analyzed<br/>
                      • Ask for concrete suggestions and improvements<br/>
                      • Request explanations of complex code sections
                    </Typography>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Advanced Usage</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">
                      • "Analyze [filename] and suggest optimizations"<br/>
                      • "Generate tests for the RAG pipeline functionality"<br/>
                      • "Review security practices in the authentication code"<br/>
                      • "Suggest database optimization strategies"
                    </Typography>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Claude Code CLI Features</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">
                      • Direct connection to Anthropic's Claude<br/>
                      • Full repository context awareness<br/>
                      • Advanced code analysis capabilities<br/>
                      • Real-time interaction with your codebase
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>

            {/* Session History */}
            {sessions.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <HistoryIcon />
                    Recent Sessions
                  </Typography>
                  
                  <List dense>
                    {sessions.slice(-5).reverse().map((session) => (
                      <ListItem 
                        key={session.id}
                        button
                        onClick={() => setCurrentQuery(session.query)}
                      >
                        <Box sx={{ width: '100%' }}>
                          <Typography variant="body2" noWrap>
                            {session.query.substring(0, 50)}...
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {session.timestamp.toLocaleTimeString()}
                            {session.duration && ` • ${session.duration}ms`}
                          </Typography>
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            )}
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ClaudeCliPage;