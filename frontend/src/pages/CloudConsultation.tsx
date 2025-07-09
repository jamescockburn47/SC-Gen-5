import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  LinearProgress,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Cloud as CloudIcon,
  Psychology as AiIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Speed as SpeedIcon,
  AttachMoney as CostIcon,
  Edit as EditIcon,
  Assessment as AssessmentIcon,
  AutoFixHigh as ImproveIcon
} from '@mui/icons-material';

interface CloudProvider {
  available: boolean;
  models: string[];
  error?: string;
}

interface CloudProviders {
  [key: string]: CloudProvider;
}

interface ProtocolViolation {
  protocol: string;
  rule: string;
  severity: string;
  description: string;
  suggestion?: string;
}

interface ProtocolReport {
  overall_compliance: boolean;
  violations: ProtocolViolation[];
  ethical_warnings: string[];
  quality_score: number;
  recommendations: string[];
}

interface ConsultationSession {
  id: string;
  question: string;
  answer: string;
  provider: string;
  model: string;
  timestamp: Date;
  cost?: number;
  processingTime: number;
  protocolReport?: ProtocolReport;
}

const CloudConsultation: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [providers, setProviders] = useState<CloudProviders>({});
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [maxTokens, setMaxTokens] = useState(2000);
  const [temperature, setTemperature] = useState(0.7);
  const [userPosition, setUserPosition] = useState('claimant');
  const [context, setContext] = useState('');
  const [sessions, setSessions] = useState<ConsultationSession[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showProtocols, setShowProtocols] = useState(false);
  const [protocols, setProtocols] = useState<any>({});
  const [currentSession, setCurrentSession] = useState<ConsultationSession | null>(null);
  const [localEnforcementResult, setLocalEnforcementResult] = useState<any>(null);

  // Load sessions from localStorage
  useEffect(() => {
    const savedSessions = localStorage.getItem('cloud_consultation_sessions');
    if (savedSessions) {
      setSessions(JSON.parse(savedSessions));
    }
  }, []);

  // Save sessions to localStorage
  useEffect(() => {
    localStorage.setItem('cloud_consultation_sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Load available providers
  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/cloud-consultation/providers');
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers);
        
        // Auto-select first available provider
        const availableProvider = Object.keys(data.providers).find(
          key => data.providers[key].available
        );
        if (availableProvider) {
          setSelectedProvider(availableProvider);
          const models = data.providers[availableProvider].models;
          if (models.length > 0) {
            setSelectedModel(models[0]);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadProtocols = async () => {
    try {
      const response = await fetch('/api/cloud-consultation/protocols');
      if (response.ok) {
        const data = await response.json();
        setProtocols(data);
      }
    } catch (error) {
      console.error('Failed to load protocols:', error);
    }
  };

  const improvePrompt = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/cloud-consultation/improve-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_question: question.trim(),
          user_position: userPosition,
          context: context
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setQuestion(data.improved_question);
      } else {
        console.error('Failed to improve prompt');
      }
    } catch (error) {
      console.error('Error improving prompt:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!question.trim() || !selectedProvider) {
      return;
    }

    setIsLoading(true);
    setAnswer('');

    try {
      const response = await fetch('/api/cloud-consultation/consult', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          provider: selectedProvider,
          model: selectedModel || undefined,
          max_tokens: maxTokens,
          temperature: temperature,
          user_position: userPosition,
          context: context,
          session_id: `session_${Date.now()}`
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setAnswer(result.answer);
        
        // Save to sessions
        const newSession: ConsultationSession = {
          id: `session_${Date.now()}`,
          question: question.trim(),
          answer: result.answer,
          provider: result.provider,
          model: result.model,
          timestamp: new Date(),
          cost: result.cost_estimate,
          processingTime: result.processing_time,
          protocolReport: result.protocol_report
        };
        
        setSessions(prev => [newSession, ...prev.slice(0, 9)]); // Keep last 10 sessions
        setCurrentSession(newSession);
      } else {
        const error = await response.json();
        setAnswer(`Error: ${error.detail || 'Failed to get consultation'}`);
      }
    } catch (error) {
      console.error('Consultation failed:', error);
      setAnswer('Error: Failed to connect to consultation service');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocalEnforcement = async () => {
    if (!answer.trim()) return;
    
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/cloud-consultation/enforce-protocols', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cloud_response: answer.trim(),
          original_question: question.trim(),
          user_position: userPosition,
          context: context
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setLocalEnforcementResult(data);
      } else {
        console.error('Failed to review with local model');
      }
    } catch (error) {
      console.error('Error reviewing with local model:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai':
        return '🤖';
      case 'gemini':
        return '🔍';
      case 'claude':
        return '🧠';
      default:
        return '☁️';
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'openai':
        return '#10a37f';
      case 'gemini':
        return '#4285f4';
      case 'claude':
        return '#d97706';
      default:
        return '#666';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <CloudIcon sx={{ fontSize: 40 }} />
        Cloud Legal Consultation
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Standalone Cloud Consultation:</strong> Get direct legal advice from cloud AI models without searching your documents. 
          This provides general legal guidance based on the AI's training data.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Main Consultation Interface */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AiIcon />
                Legal Question
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  variant="outlined"
                  placeholder="Enter your legal question here..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={isLoading}
                />
                <Button
                  variant="outlined"
                  onClick={improvePrompt}
                  disabled={!question.trim() || isLoading}
                  startIcon={<ImproveIcon />}
                  sx={{ minWidth: 'auto', px: 2 }}
                  title="Improve your prompt"
                >
                  Improve
                </Button>
              </Box>

              {/* Provider Selection */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Cloud Provider
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {Object.entries(providers).map(([provider, status]) => (
                    <Chip
                      key={provider}
                      icon={<span>{getProviderIcon(provider)}</span>}
                      label={provider.toUpperCase()}
                      onClick={() => {
                        setSelectedProvider(provider);
                        if (status.models.length > 0) {
                          setSelectedModel(status.models[0]);
                        }
                      }}
                      variant={selectedProvider === provider ? 'filled' : 'outlined'}
                      color={selectedProvider === provider ? 'primary' : 'default'}
                      disabled={!status.available}
                      sx={{
                        backgroundColor: selectedProvider === provider ? getProviderColor(provider) : undefined,
                        color: selectedProvider === provider ? 'white' : undefined
                      }}
                    />
                  ))}
                </Box>
                {selectedProvider && providers[selectedProvider]?.error && (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    {providers[selectedProvider].error}
                  </Alert>
                )}
              </Box>

              {/* Model Selection */}
              {selectedProvider && providers[selectedProvider]?.models.length > 0 && (
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Model</InputLabel>
                  <Select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={isLoading}
                  >
                    {providers[selectedProvider].models.map((model) => (
                      <MenuItem key={model} value={model}>
                        {model}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              {/* Advanced Settings */}
              <Accordion expanded={showAdvanced} onChange={() => setShowAdvanced(!showAdvanced)}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SettingsIcon />
                    Advanced Settings
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" gutterBottom>
                        Max Tokens: {maxTokens}
                      </Typography>
                      <Slider
                        value={maxTokens}
                        onChange={(_, value) => setMaxTokens(value as number)}
                        min={500}
                        max={4000}
                        step={100}
                        marks={[
                          { value: 500, label: '500' },
                          { value: 2000, label: '2000' },
                          { value: 4000, label: '4000' }
                        ]}
                        disabled={isLoading}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" gutterBottom>
                        Temperature: {temperature}
                      </Typography>
                      <Slider
                        value={temperature}
                        onChange={(_, value) => setTemperature(value as number)}
                        min={0.0}
                        max={1.0}
                        step={0.1}
                        marks={[
                          { value: 0.0, label: '0.0' },
                          { value: 0.5, label: '0.5' },
                          { value: 1.0, label: '1.0' }
                        ]}
                        disabled={isLoading}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>User Position</InputLabel>
                        <Select
                          value={userPosition}
                          onChange={(e) => setUserPosition(e.target.value)}
                          disabled={isLoading}
                        >
                          <MenuItem value="claimant">Claimant</MenuItem>
                          <MenuItem value="respondent">Respondent</MenuItem>
                          <MenuItem value="defendant">Defendant</MenuItem>
                          <MenuItem value="plaintiff">Plaintiff</MenuItem>
                          <MenuItem value="neutral">Neutral Analysis</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Additional Context"
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        multiline
                        rows={3}
                        disabled={isLoading}
                        placeholder="Optional: Add relevant context, documents, or background information..."
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              <Button
                variant="contained"
                fullWidth
                onClick={handleSubmit}
                disabled={!question.trim() || !selectedProvider || isLoading}
                sx={{ mt: 2 }}
                startIcon={<CloudIcon />}
              >
                {isLoading ? 'Consulting...' : 'Get Legal Consultation'}
              </Button>
            </CardContent>
          </Card>

          {/* Answer Display */}
          {answer && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Legal Analysis
                </Typography>
                <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {answer}
                  </Typography>
                </Paper>
                
                {/* Protocol Compliance Report */}
                {currentSession?.protocolReport && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AssessmentIcon />
                      Protocol Compliance Report
                    </Typography>
                    
                    <Paper sx={{ p: 2, backgroundColor: currentSession.protocolReport.overall_compliance ? '#e8f5e8' : '#fff3cd' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Chip
                          label={currentSession.protocolReport.overall_compliance ? 'Compliant' : 'Non-Compliant'}
                          color={currentSession.protocolReport.overall_compliance ? 'success' : 'warning'}
                        />
                        <Typography variant="body2">
                          Quality Score: {(currentSession.protocolReport.quality_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                      
                      {currentSession.protocolReport.violations.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Violations:</Typography>
                          {currentSession.protocolReport.violations.map((violation, index) => (
                            <Alert key={index} severity={violation.severity as any} sx={{ mb: 1 }}>
                              <Typography variant="body2">
                                <strong>{violation.protocol}.{violation.rule}:</strong> {violation.description}
                              </Typography>
                              {violation.suggestion && (
                                <Typography variant="body2" sx={{ mt: 1 }}>
                                  <strong>Suggestion:</strong> {violation.suggestion}
                                </Typography>
                              )}
                            </Alert>
                          ))}
                        </Box>
                      )}
                      
                      {currentSession.protocolReport.ethical_warnings.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Ethical Warnings:</Typography>
                          {currentSession.protocolReport.ethical_warnings.map((warning, index) => (
                            <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                              {warning}
                            </Alert>
                          ))}
                        </Box>
                      )}
                      
                      {currentSession.protocolReport.recommendations.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>Recommendations:</Typography>
                          <List dense>
                            {currentSession.protocolReport.recommendations.map((rec, index) => (
                              <ListItem key={index}>
                                <ListItemIcon>
                                  <AssessmentIcon />
                                </ListItemIcon>
                                <ListItemText primary={rec} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                    </Paper>
                  </Box>
                )}
                
                {/* Local Model Protocol Review Button */}
                {answer && (
                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="outlined"
                      fullWidth
                      onClick={handleLocalEnforcement}
                      disabled={isLoading}
                      startIcon={<AssessmentIcon />}
                      sx={{ mb: 2 }}
                    >
                      Review with Local Model (Mistral-7B)
                    </Button>
                    
                    {localEnforcementResult && (
                      <Paper sx={{ p: 2, backgroundColor: localEnforcementResult.is_compliant ? '#e8f5e8' : '#fff3cd' }}>
                        <Typography variant="h6" gutterBottom>
                          Local Model Review Results
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Chip
                            label={localEnforcementResult.is_compliant ? 'Compliant' : 'Non-Compliant'}
                            color={localEnforcementResult.is_compliant ? 'success' : 'warning'}
                          />
                          <Typography variant="body2">
                            Confidence: {(localEnforcementResult.confidence * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                        
                        {localEnforcementResult.violations.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" gutterBottom>Violations Detected:</Typography>
                            {localEnforcementResult.violations.map((violation: ProtocolViolation, index: number) => (
                              <Alert key={index} severity={violation.severity as any} sx={{ mb: 1 }}>
                                <Typography variant="body2">
                                  <strong>{violation.protocol}.{violation.rule}:</strong> {violation.description}
                                </Typography>
                                {violation.suggestion && (
                                  <Typography variant="body2" sx={{ mt: 1 }}>
                                    <strong>Suggestion:</strong> {violation.suggestion}
                                  </Typography>
                                )}
                              </Alert>
                            ))}
                          </Box>
                        )}
                        
                        {localEnforcementResult.suggestions.length > 0 && (
                          <Box>
                            <Typography variant="subtitle2" gutterBottom>Suggestions:</Typography>
                            <List dense>
                              {localEnforcementResult.suggestions.map((suggestion: string, index: number) => (
                                <ListItem key={index}>
                                  <ListItemIcon>
                                    <AssessmentIcon />
                                  </ListItemIcon>
                                  <ListItemText primary={suggestion} />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                      </Paper>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Loading Progress */}
          {isLoading && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="body2" gutterBottom>
                  Consulting with {selectedProvider.toUpperCase()}...
                </Typography>
                <LinearProgress />
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          {/* Provider Status */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CloudIcon />
                Provider Status
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {Object.entries(providers).map(([provider, status]) => (
                  <Box key={provider} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{getProviderIcon(provider)}</span>
                      <Typography variant="body2" sx={{ textTransform: 'uppercase' }}>
                        {provider}
                      </Typography>
                    </Box>
                    <Chip
                      label={status.available ? 'Available' : 'Unavailable'}
                      size="small"
                      color={status.available ? 'success' : 'error'}
                      variant="outlined"
                    />
                  </Box>
                ))}
              </Box>
              
              <Button
                variant="outlined"
                size="small"
                onClick={loadProviders}
                startIcon={<RefreshIcon />}
                sx={{ mt: 2 }}
                fullWidth
              >
                Refresh Status
              </Button>
            </CardContent>
          </Card>

          {/* Protocol Management */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon />
                Strategic Protocols
              </Typography>
              
              <Button
                variant="outlined"
                size="small"
                onClick={loadProtocols}
                startIcon={<RefreshIcon />}
                sx={{ mb: 2 }}
                fullWidth
              >
                Load Protocols
              </Button>
              
              <Button
                variant="outlined"
                size="small"
                onClick={() => setShowProtocols(!showProtocols)}
                startIcon={<EditIcon />}
                fullWidth
              >
                {showProtocols ? 'Hide' : 'Show'} Protocol Editor
              </Button>
            </CardContent>
          </Card>

          {/* Recent Sessions */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Consultations
              </Typography>
              
              {sessions.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No consultations yet
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {sessions.slice(0, 5).map((session) => (
                    <Paper key={session.id} sx={{ p: 2, backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {session.question.length > 50 
                          ? session.question.substring(0, 50) + '...' 
                          : session.question
                        }
                      </Typography>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Chip
                          label={session.provider.toUpperCase()}
                          size="small"
                          sx={{ backgroundColor: getProviderColor(session.provider), color: 'white' }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {new Date(session.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          icon={<SpeedIcon />}
                          label={`${session.processingTime.toFixed(1)}s`}
                          size="small"
                          variant="outlined"
                        />
                        {session.cost && (
                          <Chip
                            icon={<CostIcon />}
                            label={`$${session.cost.toFixed(4)}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Protocol Editor Dialog */}
      <Dialog
        open={showProtocols}
        onClose={() => setShowProtocols(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Strategic Protocols Editor
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Edit strategic protocols for litigation analysis. These protocols ensure quality, compliance, and ethical standards.
          </Typography>
          
          {Object.entries(protocols).map(([protocolId, protocol]: [string, any]) => (
            <Accordion key={protocolId} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">
                  {protocolId}: {protocol.name}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {Object.entries(protocol.rules).map(([ruleId, rule]) => (
                    <TextField
                      key={ruleId}
                      label={`${protocolId}.${ruleId}`}
                      value={rule}
                      multiline
                      rows={2}
                      fullWidth
                      size="small"
                      onChange={(e) => {
                        // Update protocol rule
                        const updatedProtocols = { ...protocols };
                        updatedProtocols[protocolId].rules[ruleId] = e.target.value;
                        setProtocols(updatedProtocols);
                      }}
                    />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowProtocols(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={async () => {
              try {
                const response = await fetch('/api/cloud-consultation/protocols/save', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(protocols)
                });
                if (response.ok) {
                  setShowProtocols(false);
                }
              } catch (error) {
                console.error('Failed to save protocols:', error);
              }
            }}
          >
            Save Protocols
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CloudConsultation; 