import React, { useState, useEffect, useRef } from 'react';
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
  ListItemText,
  Divider,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  CircularProgress,
  Tooltip,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  ListItemButton
} from '@mui/material';
import {
  Psychology as ConsultIcon,
  Send as SendIcon,
  Clear as ClearIcon,
  History as HistoryIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Description as DocumentIcon,
  Search as SearchIcon,
  Lightbulb as SuggestionIcon,
  ExpandMore as ExpandMoreIcon,
  AutoAwesome as AiIcon,
  School as LegalIcon
} from '@mui/icons-material';
import axios from 'axios';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: DocumentSource[];
  model?: string;
  confidence?: number;
}

interface DocumentSource {
  document_id: string;
  filename: string;
  relevance_score: number;
  text_excerpt: string;
  page_number?: number;
}

interface ConsultationSession {
  id: string;
  title: string;
  created_at: Date;
  message_count: number;
  legal_area?: string;
}

interface ConsultationSettings {
  use_cloud: boolean;
  local_model: 'mistral:latest' | 'mixtral:latest';
  cloud_provider: 'anthropic' | 'openai' | 'gemini';
  include_sources: boolean;
  max_context_documents: number;
  response_style: 'detailed' | 'concise' | 'technical';
  legal_area: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`consultation-tabpanel-${index}`}
      aria-labelledby={`consultation-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

const ConsultationPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<ConsultationSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [settings, setSettings] = useState<ConsultationSettings>({
    use_cloud: false,
    local_model: 'mistral:latest',
    cloud_provider: 'anthropic',
    include_sources: true,
    max_context_documents: 5,
    response_style: 'detailed',
    legal_area: 'general'
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [availableDocuments, setAvailableDocuments] = useState<number>(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load consultation sessions on mount
  useEffect(() => {
    loadSessions();
    loadAvailableDocuments();
    loadSuggestions();
  }, []);

  const loadSessions = async () => {
    try {
      // Use localStorage for session persistence since backend sessions may not be available
      const savedSessions = localStorage.getItem('consultation_sessions');
      if (savedSessions) {
        setSessions(JSON.parse(savedSessions));
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadAvailableDocuments = async () => {
    try {
      // Use unified RAG status endpoint
      const response = await axios.get('/api/rag/status');
      const documentCount = response.data.documents?.count || 0;
      setAvailableDocuments(documentCount);
    } catch (error) {
      console.error('Failed to load document stats:', error);
      setAvailableDocuments(0);
    }
  };

  const loadSuggestions = () => {
    const legalSuggestions = [
      "What are the key elements of a valid contract?",
      "Explain the difference between copyright and trademark",
      "What are the liability implications of this clause?",
      "Analyze the compliance requirements for data protection",
      "What are the employment law considerations here?",
      "Review this contract for potential risks",
      "What intellectual property protections apply?",
      "Explain the regulatory framework for this industry"
    ];
    setSuggestions(legalSuggestions.slice(0, 4));
  };

  const createNewSession = async () => {
    try {
      const newSession: ConsultationSession = {
        id: `session_${Date.now()}`,
        title: `Consultation ${new Date().toLocaleDateString()}`,
        created_at: new Date(),
        message_count: 0,
        legal_area: settings.legal_area
      };
      
      const updatedSessions = [newSession, ...sessions];
      setSessions(updatedSessions);
      localStorage.setItem('consultation_sessions', JSON.stringify(updatedSessions));
      setCurrentSessionId(newSession.id);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const savedMessages = localStorage.getItem(`session_messages_${sessionId}`);
      if (savedMessages) {
        const messages = JSON.parse(savedMessages);
        setMessages(messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })));
      } else {
        setMessages([]);
      }
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: currentMessage,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      // Use unified RAG endpoint
      const response = await axios.post('/api/rag/answer', {
        question: currentMessage,
        session_id: currentSessionId,
        max_tokens: settings.response_style === 'concise' ? 100 : 
                   settings.response_style === 'detailed' ? 300 : 200,
        include_sources: settings.include_sources,
        response_style: settings.response_style,
        legal_area: settings.legal_area
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.answer,
        role: 'assistant',
        timestamp: new Date(),
        sources: response.data.sources || [],
        model: response.data.model_used || 'RAG (Unified)',
        confidence: response.data.confidence
      };

      setMessages(prev => {
        const newMessages = [...prev, assistantMessage];
        
        // Auto-save messages to localStorage
        if (currentSessionId) {
          localStorage.setItem(`session_messages_${currentSessionId}`, JSON.stringify(newMessages));
          
          // Update session message count
          const updatedSessions = sessions.map(session => 
            session.id === currentSessionId 
              ? { ...session, message_count: newMessages.length }
              : session
          );
          setSessions(updatedSessions);
          localStorage.setItem('consultation_sessions', JSON.stringify(updatedSessions));
        }
        
        return newMessages;
      });

    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  const saveSession = async () => {
    if (!messages.length || !currentSessionId) return;

    try {
      // Save messages to localStorage (already done in auto-save)
      localStorage.setItem(`session_messages_${currentSessionId}`, JSON.stringify(messages));
      
      // Update session metadata
      const updatedSessions = sessions.map(session => 
        session.id === currentSessionId 
          ? { ...session, message_count: messages.length, legal_area: settings.legal_area }
          : session
      );
      setSessions(updatedSessions);
      localStorage.setItem('consultation_sessions', JSON.stringify(updatedSessions));
      
      console.log('Session saved locally');
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  };

  const exportSession = () => {
    if (!messages.length) return;

    const exportData = {
      session_id: currentSessionId,
      exported_at: new Date().toISOString(),
      settings: settings,
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
        sources: msg.sources
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `consultation-${currentSessionId || 'session'}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setCurrentMessage(suggestion);
    inputRef.current?.focus();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <ConsultIcon sx={{ fontSize: 40 }} />
        Legal Consultation
      </Typography>

      <Grid container spacing={3}>
        {/* Main Chat Interface */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
            {/* Chat Header */}
            <CardContent sx={{ borderBottom: 1, borderColor: 'divider', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip
                    icon={<AiIcon />}
                    label={`${messages.length} messages`}
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<DocumentIcon />}
                    label={`${availableDocuments} documents available`}
                    color="secondary"
                    variant="outlined"
                  />
                  <Chip
                    label={settings.use_cloud ? `Cloud (${settings.cloud_provider})` : `Local (${settings.local_model.split(':')[0]})`}
                    color={settings.use_cloud ? "warning" : "success"}
                    variant="filled"
                  />
                  {currentSessionId && (
                    <Chip label="Session Active" color="info" variant="outlined" />
                  )}
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="New Session">
                    <IconButton onClick={createNewSession}>
                      <LegalIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Save Session">
                    <IconButton onClick={saveSession} disabled={!messages.length}>
                      <SaveIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Export Session">
                    <IconButton onClick={exportSession} disabled={!messages.length}>
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Clear Chat">
                    <IconButton onClick={clearMessages}>
                      <ClearIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Settings">
                    <IconButton onClick={() => setSettingsOpen(true)}>
                      <SettingsIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            </CardContent>

            {/* Messages Area */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
              {messages.length === 0 ? (
                <Box sx={{ textAlign: 'center', mt: 4 }}>
                  <AiIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Welcome to Legal Consultation
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Ask me anything about legal matters. I can analyze documents, explain laws, and provide guidance.
                  </Typography>
                  
                  {/* Suggestions */}
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Suggested Questions:
                    </Typography>
                    <Grid container spacing={1} justifyContent="center">
                      {suggestions.map((suggestion, index) => (
                        <Grid item key={index}>
                          <Chip
                            label={suggestion}
                            onClick={() => handleSuggestionClick(suggestion)}
                            clickable
                            variant="outlined"
                            icon={<SuggestionIcon />}
                            sx={{ m: 0.5 }}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                </Box>
              ) : (
                <List>
                  {messages.map((message) => (
                    <ListItem key={message.id} sx={{ flexDirection: 'column', alignItems: 'stretch' }}>
                      <Paper
                        sx={{
                          p: 2,
                          bgcolor: message.role === 'user' ? 'primary.light' : 'background.paper',
                          color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                          alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                          maxWidth: '80%',
                          mb: 1
                        }}
                      >
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                          {message.content}
                        </Typography>
                        
                        {message.sources && message.sources.length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="caption" color="text.secondary">
                              Sources:
                            </Typography>
                            {message.sources.map((source, index) => (
                              <Accordion key={index} sx={{ mt: 1 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                  <Typography variant="body2">
                                    {source.filename} (Relevance: {(source.relevance_score * 100).toFixed(1)}%)
                                  </Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                  <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                                    "{source.text_excerpt}"
                                  </Typography>
                                  {source.page_number && (
                                    <Typography variant="caption" color="text.secondary">
                                      Page {source.page_number}
                                    </Typography>
                                  )}
                                </AccordionDetails>
                              </Accordion>
                            ))}
                          </Box>
                        )}
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {message.timestamp.toLocaleTimeString()}
                          </Typography>
                          {message.model && (
                            <Chip label={message.model} size="small" variant="outlined" />
                          )}
                        </Box>
                      </Paper>
                    </ListItem>
                  ))}
                  
                  {isLoading && (
                    <ListItem>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                          Analyzing your query and searching documents...
                        </Typography>
                      </Box>
                    </ListItem>
                  )}
                </List>
              )}
              <div ref={messagesEndRef} />
            </Box>

            {/* Input Area */}
            <CardContent sx={{ borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  placeholder="Ask a legal question..."
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                  inputRef={inputRef}
                />
                <Button
                  variant="contained"
                  endIcon={<SendIcon />}
                  onClick={sendMessage}
                  disabled={isLoading || !currentMessage.trim()}
                  sx={{ minWidth: 100 }}
                >
                  Send
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Session History */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HistoryIcon />
                  Session History
                </Typography>
                
                <List dense>
                  {sessions.slice(0, 5).map((session) => (
                    <ListItem key={session.id} disablePadding>
                      <ListItemButton onClick={() => loadSession(session.id)} selected={currentSessionId === session.id}>
                        <ListItemText
                          primary={session.title}
                          secondary={`${session.message_count} messages • ${new Date(session.created_at).toLocaleDateString()}`}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
                
                {sessions.length === 0 && (
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    No saved sessions
                  </Typography>
                )}
              </CardContent>
            </Card>

            {/* Model Selection */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AiIcon />
                  AI Model Selection
                </Typography>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.use_cloud}
                      onChange={(e) => setSettings(prev => ({ ...prev, use_cloud: e.target.checked }))}
                      color="warning"
                    />
                  }
                  label={settings.use_cloud ? "Cloud AI (Faster, Requires Internet)" : "Local AI (Private, No Internet)"}
                  sx={{ mb: 2 }}
                />
                
                {!settings.use_cloud ? (
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Local Model</InputLabel>
                    <Select
                      value={settings.local_model}
                      onChange={(e) => setSettings(prev => ({ ...prev, local_model: e.target.value as any }))}
                    >
                      <MenuItem value="mistral:latest">Mistral (7B) - Best Quality Legal Analysis</MenuItem>
                      <MenuItem value="mixtral:latest">Mixtral (46B) - Most Powerful (High Memory)</MenuItem>
                    </Select>
                  </FormControl>
                ) : (
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Cloud Provider</InputLabel>
                    <Select
                      value={settings.cloud_provider}
                      onChange={(e) => setSettings(prev => ({ ...prev, cloud_provider: e.target.value as any }))}
                    >
                      <MenuItem value="anthropic">Claude (Anthropic)</MenuItem>
                      <MenuItem value="openai">GPT (OpenAI)</MenuItem>
                      <MenuItem value="gemini">Gemini (Google)</MenuItem>
                    </Select>
                  </FormControl>
                )}
              </CardContent>
            </Card>

            {/* Quick Settings */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Legal Settings
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Legal Area</InputLabel>
                  <Select
                    value={settings.legal_area}
                    onChange={(e) => setSettings(prev => ({ ...prev, legal_area: e.target.value }))}
                  >
                    <MenuItem value="general">General Law</MenuItem>
                    <MenuItem value="contract">Contract Law</MenuItem>
                    <MenuItem value="employment">Employment Law</MenuItem>
                    <MenuItem value="intellectual_property">Intellectual Property</MenuItem>
                    <MenuItem value="corporate">Corporate Law</MenuItem>
                    <MenuItem value="data_protection">Data Protection</MenuItem>
                    <MenuItem value="litigation">Litigation</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Response Style</InputLabel>
                  <Select
                    value={settings.response_style}
                    onChange={(e) => setSettings(prev => ({ ...prev, response_style: e.target.value as any }))}
                  >
                    <MenuItem value="concise">Concise</MenuItem>
                    <MenuItem value="detailed">Detailed</MenuItem>
                    <MenuItem value="technical">Technical</MenuItem>
                  </Select>
                </FormControl>

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.include_sources}
                      onChange={(e) => setSettings(prev => ({ ...prev, include_sources: e.target.checked }))}
                    />
                  }
                  label="Include Document Sources"
                />
              </CardContent>
            </Card>

            {/* System Status */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Status
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Documents Indexed:</Typography>
                    <Chip label={availableDocuments} size="small" color="primary" />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">AI Model:</Typography>
                    <Chip 
                      label={settings.use_cloud ? settings.cloud_provider : settings.local_model.split(':')[0]} 
                      size="small" 
                      color={settings.use_cloud ? "warning" : "success"}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Context Documents:</Typography>
                    <Chip label={settings.max_context_documents} size="small" />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Consultation Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <Alert severity="info">
              <strong>Model Selection:</strong> Use the main sidebar to choose between Cloud AI (faster, requires internet) or Local AI (private, no internet required).
            </Alert>

            <TextField
              fullWidth
              type="number"
              label="Max Context Documents"
              value={settings.max_context_documents}
              onChange={(e) => setSettings(prev => ({ ...prev, max_context_documents: parseInt(e.target.value) }))}
              inputProps={{ min: 1, max: 20 }}
              helperText="Number of relevant documents to include in context"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.include_sources}
                  onChange={(e) => setSettings(prev => ({ ...prev, include_sources: e.target.checked }))}
                />
              }
              label="Show Document Sources in Responses"
            />

            <Alert severity="success">
              Settings are saved automatically and apply to new conversations.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConsultationPage; 