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
  Chip,
  IconButton,
  Alert,
  Grid,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Psychology as ConsultIcon,
  Send as SendIcon,
  Clear as ClearIcon,
  Settings as SettingsIcon,
  Description as DocumentIcon,
  AutoAwesome as AiIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Lightbulb as SuggestionIcon
} from '@mui/icons-material';
import { useRAGStatus, useAskQuestion } from '../api/rag';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: Array<{
    document_id: string;
    filename: string;
    relevance_score: number;
    text_excerpt: string;
  }>;
  model?: string;
  confidence?: number;
}

interface ConsultationSettings {
  response_style: 'concise' | 'detailed' | 'technical';
  legal_area: string;
  include_sources: boolean;
  max_tokens: number;
}

const ConsultationPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [settings, setSettings] = useState<ConsultationSettings>({
    response_style: 'detailed',
    legal_area: 'general',
    include_sources: true,
    max_tokens: 200
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // API hooks
  const { data: status, isLoading: statusLoading } = useRAGStatus();
  const askQuestion = useAskQuestion();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load saved messages on mount
  useEffect(() => {
    const saved = localStorage.getItem('consultation_messages');
    if (saved) {
      try {
        const parsedMessages = JSON.parse(saved).map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(parsedMessages);
      } catch (error) {
        console.error('Failed to load saved messages:', error);
      }
    }
  }, []);

  // Save messages when they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('consultation_messages', JSON.stringify(messages));
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!currentMessage.trim() || askQuestion.isPending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: currentMessage,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const questionText = currentMessage;
    setCurrentMessage('');

    try {
      const response = await askQuestion.mutateAsync({
        question: questionText,
        max_tokens: settings.max_tokens,
        include_sources: settings.include_sources,
        response_style: settings.response_style
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.answer,
        role: 'assistant',
        timestamp: new Date(),
        sources: response.sources || [],
        model: response.model_used || 'RAG System',
        confidence: response.confidence
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    localStorage.removeItem('consultation_messages');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestions = [
    "What are the key elements of a valid contract?",
    "Explain the difference between copyright and trademark",
    "What are the liability implications of negligence?",
    "What are the employment law considerations for dismissal?"
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setCurrentMessage(suggestion);
    inputRef.current?.focus();
  };

  // System status indicators
  const getStatusColor = () => {
    if (statusLoading) return 'warning';
    if (status?.ready) return 'success';
    return 'error';
  };

  const getStatusText = () => {
    if (statusLoading) return 'Checking...';
    if (status?.ready) return 'Ready';
    return 'Not Ready';
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <ConsultIcon sx={{ fontSize: 40 }} />
        Legal Consultation
        <Chip
          icon={getStatusColor() === 'success' ? <CheckIcon /> : <ErrorIcon />}
          label={getStatusText()}
          color={getStatusColor()}
          variant="outlined"
          size="small"
        />
      </Typography>

      <Grid container spacing={3}>
        {/* Main Chat Interface */}
        <Grid item xs={12} lg={9}>
          <Card sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
            {/* Chat Header */}
            <CardContent sx={{ borderBottom: 1, borderColor: 'divider', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip
                    icon={<AiIcon />}
                    label={`${messages.length} messages`}
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<DocumentIcon />}
                    label={`${status?.documents.count || 0} documents`}
                    color="secondary"
                    variant="outlined"
                  />
                  {status?.models && (
                    <Chip
                      label={`${Object.values(status.models).filter(Boolean).length}/${Object.keys(status.models).length} models ready`}
                      color={status.ready ? "success" : "warning"}
                      variant="filled"
                    />
                  )}
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Clear Chat">
                    <IconButton onClick={clearMessages} disabled={messages.length === 0}>
                      <ClearIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Settings">
                    <IconButton onClick={() => setSettingsOpen(!settingsOpen)}>
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
                      Try asking:
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
                    <ListItem key={message.id} sx={{ flexDirection: 'column', alignItems: 'stretch', mb: 2 }}>
                      <Paper
                        sx={{
                          p: 2,
                          bgcolor: message.role === 'user' ? 'primary.light' : 'background.paper',
                          color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                          alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                          maxWidth: '85%',
                          border: message.role === 'assistant' ? 1 : 0,
                          borderColor: 'divider'
                        }}
                      >
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                          {message.content}
                        </Typography>
                        
                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                              Sources ({message.sources.length}):
                            </Typography>
                            {message.sources.map((source, index) => (
                              <Accordion key={index} sx={{ mt: 1 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                  <Typography variant="body2">
                                    {source.filename} - Relevance: {(source.relevance_score * 100).toFixed(1)}%
                                  </Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                  <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                                    "{source.text_excerpt}"
                                  </Typography>
                                </AccordionDetails>
                              </Accordion>
                            ))}
                          </Box>
                        )}
                        
                        {/* Message metadata */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {message.timestamp.toLocaleTimeString()}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            {message.confidence && (
                              <Chip 
                                label={`${(message.confidence * 100).toFixed(0)}% confidence`} 
                                size="small" 
                                variant="outlined"
                                color={message.confidence > 0.8 ? 'success' : message.confidence > 0.6 ? 'warning' : 'error'}
                              />
                            )}
                            {message.model && (
                              <Chip label={message.model} size="small" variant="outlined" />
                            )}
                          </Box>
                        </Box>
                      </Paper>
                    </ListItem>
                  ))}
                  
                  {askQuestion.isPending && (
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
                  disabled={askQuestion.isPending}
                  inputRef={inputRef}
                />
                <Button
                  variant="contained"
                  endIcon={<SendIcon />}
                  onClick={sendMessage}
                  disabled={askQuestion.isPending || !currentMessage.trim()}
                  sx={{ minWidth: 100 }}
                >
                  Send
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Settings Sidebar */}
        <Grid item xs={12} lg={3}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* System Status */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Status
                </Typography>
                
                {status && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Overall Status:</Typography>
                      <Chip 
                        label={status.status} 
                        size="small" 
                        color={status.ready ? "success" : "warning"}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Documents:</Typography>
                      <Chip label={status.documents.count} size="small" color="primary" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">GPU Memory:</Typography>
                      <Chip 
                        label={`${status.hardware?.memory_usage?.toFixed(1) || '0.0'}GB`} 
                        size="small" 
                        color={(status.hardware?.memory_usage || 0) > 6 ? "warning" : "success"}
                      />
                    </Box>
                    
                    <Divider sx={{ my: 1 }} />
                    
                    <Typography variant="caption" color="text.secondary">
                      Model Status:
                    </Typography>
                    {Object.entries(status.models).map(([model, ready]) => (
                      <Box key={model} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {model}:
                        </Typography>
                        <Chip 
                          label={ready ? "Ready" : "Not Ready"} 
                          size="small" 
                          color={ready ? "success" : "default"}
                          variant="outlined"
                        />
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Settings Panel */}
            {settingsOpen && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Settings
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth size="small">
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

                    <FormControl fullWidth size="small">
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
                      </Select>
                    </FormControl>

                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Max Response Length"
                      value={settings.max_tokens}
                      onChange={(e) => setSettings(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                      inputProps={{ min: 50, max: 500 }}
                    />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.include_sources}
                          onChange={(e) => setSettings(prev => ({ ...prev, include_sources: e.target.checked }))}
                          size="small"
                        />
                      }
                      label="Include Document Sources"
                    />
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Quick Help */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Help
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  <strong>💡 Tips:</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • Ask specific legal questions for better answers
                  • Include context about your jurisdiction if relevant
                  • Use technical response style for detailed legal analysis
                  • Sources will show which documents were referenced
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>

      {/* Error Alert */}
      {askQuestion.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to get response. Please check your connection and try again.
        </Alert>
      )}
    </Box>
  );
};

export default ConsultationPage;