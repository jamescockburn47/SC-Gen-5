import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Tab,
  Tabs,
  Alert,
  Button,
  Paper,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
  Slider,
  TextField
} from '@mui/material';
import {
  Psychology as RAGIcon,
  CloudUpload as UploadIcon,
  Settings as SettingsIcon,
  Speed as PerformanceIcon,
  Refresh as RefreshIcon,
  Memory as MemoryIcon,
  Tune as TuneIcon
} from '@mui/icons-material';

import AskBar, { AskOptions } from '../components/AskBar';
import StreamPane from '../components/StreamPane';
import UploadZone from '../components/UploadZone';
import ProgressTracker, { ProcessingStep } from '../components/ProgressTracker';
import { 
  useRAGStatus, 
  useInitializeRAG, 
  useAskQuestion,
  useHardwareStatus,
  useClearCache,
  useWarmupModels,
  StatusResponse 
} from '../api/rag';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

// Local storage keys for state persistence
const STORAGE_KEYS = {
  CURRENT_QUESTION: 'research_current_question',
  CURRENT_ANSWER: 'research_current_answer',
  CURRENT_CONFIDENCE: 'research_current_confidence',
  PROGRESS_STEPS: 'research_progress_steps',
  SHOW_PROGRESS_DETAILS: 'research_show_progress_details',
  TAB_VALUE: 'research_tab_value'
};

const Research: React.FC = () => {
  // Load persisted state from localStorage
  const [tabValue, setTabValue] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEYS.TAB_VALUE);
    return saved ? parseInt(saved) : 0;
  });
  
  const [currentQuestion, setCurrentQuestion] = useState(() => {
    return localStorage.getItem(STORAGE_KEYS.CURRENT_QUESTION) || '';
  });
  
  const [currentAnswer, setCurrentAnswer] = useState(() => {
    return localStorage.getItem(STORAGE_KEYS.CURRENT_ANSWER) || '';
  });
  
  const [currentConfidence, setCurrentConfidence] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEYS.CURRENT_CONFIDENCE);
    return saved ? parseFloat(saved) : 0;
  });
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [initDialog, setInitDialog] = useState(false);
  
  const [progressSteps, setProgressSteps] = useState<ProcessingStep[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEYS.PROGRESS_STEPS);
    return saved ? JSON.parse(saved) : [];
  });
  
  const [showProgressDetails, setShowProgressDetails] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEYS.SHOW_PROGRESS_DETAILS);
    return saved ? JSON.parse(saved) : false;
  });

  // Utility model configuration state
  const [utilityConfig, setUtilityConfig] = useState({
    enabled: true,
    threshold: 0.3,
    model_name: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
  });
  const [configDialog, setConfigDialog] = useState(false);

  // API hooks
  const { data: status, refetch: refetchStatus } = useRAGStatus();
  const { data: hardwareStatus } = useHardwareStatus();
  const initMutation = useInitializeRAG();
  const askMutation = useAskQuestion();
  const clearCacheMutation = useClearCache();
  const warmupMutation = useWarmupModels();

  // Persist state changes to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.TAB_VALUE, tabValue.toString());
  }, [tabValue]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CURRENT_QUESTION, currentQuestion);
  }, [currentQuestion]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CURRENT_ANSWER, currentAnswer);
  }, [currentAnswer]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CURRENT_CONFIDENCE, currentConfidence.toString());
  }, [currentConfidence]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.PROGRESS_STEPS, JSON.stringify(progressSteps));
  }, [progressSteps]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SHOW_PROGRESS_DETAILS, JSON.stringify(showProgressDetails));
  }, [showProgressDetails]);

  // Check if system needs initialization
  useEffect(() => {
    if (status && !status.ready) {
      setInitDialog(true);
    }
  }, [status]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const initializeProgressSteps = () => {
    const steps: ProcessingStep[] = [
      {
        id: 'query-analysis',
        name: 'Query Analysis',
        status: 'pending',
        progress: 0,
        message: 'Analyzing legal question and identifying key issues',
        estimatedDuration: 2
      },
      {
        id: 'document-retrieval',
        name: 'Document Retrieval',
        status: 'pending',
        progress: 0,
        message: 'Searching and retrieving relevant legal documents',
        estimatedDuration: 5
      },
      {
        id: 'chunk-processing',
        name: 'Chunk Processing',
        status: 'pending',
        progress: 0,
        message: 'Processing document chunks for relevance',
        estimatedDuration: 3
      },
      {
        id: 'context-building',
        name: 'Context Building',
        status: 'pending',
        progress: 0,
        message: 'Building comprehensive legal context',
        estimatedDuration: 2
      },
      {
        id: 'model-generation',
        name: 'Legal Analysis Generation',
        status: 'pending',
        progress: 0,
        message: 'Generating comprehensive legal analysis',
        estimatedDuration: 15,
        modelUsed: 'Mistral-7B-Instruct'
      },
      {
        id: 'response-formatting',
        name: 'Response Formatting',
        status: 'pending',
        progress: 0,
        message: 'Formatting final legal analysis',
        estimatedDuration: 1
      }
    ];
    setProgressSteps(steps);
  };

  const updateProgressStep = (stepId: string, updates: Partial<ProcessingStep>) => {
    setProgressSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, ...updates } : step
    ));
  };

  const handleAskQuestion = async (question: string, options: AskOptions) => {
    setCurrentQuestion(question);
    setCurrentAnswer('');
    setCurrentConfidence(0);
    initializeProgressSteps();

    // Use new Simple RAG API with litigation options
    try {
      // Start progress tracking
      updateProgressStep('query-analysis', { 
        status: 'processing', 
        startTime: new Date(),
        progress: 10 
      });

      const result = await askMutation.mutateAsync({
        question,
        max_chunks: options.max_chunks || 5,
        min_relevance: options.min_relevance || 0.3,
        include_sources: options.include_sources !== false,
        response_style: options.response_style || 'detailed',
        // Litigation-specific options
        matter_type: options.matter_type || 'litigation',
        analysis_style: options.analysis_style || 'comprehensive',
        focus_area: options.focus_area || 'liability'
      });
      
      // Update progress steps based on result
      updateProgressStep('query-analysis', { 
        status: 'completed', 
        endTime: new Date(),
        progress: 100 
      });
      
      updateProgressStep('document-retrieval', { 
        status: 'completed', 
        endTime: new Date(),
        progress: 100,
        chunksProcessed: result.chunks_analyzed || 0,
        totalChunks: result.chunks_used || 0
      });
      
      updateProgressStep('chunk-processing', { 
        status: 'completed', 
        endTime: new Date(),
        progress: 100 
      });
      
      updateProgressStep('context-building', { 
        status: 'completed', 
        endTime: new Date(),
        progress: 100 
      });
      
      updateProgressStep('model-generation', { 
        status: 'completed', 
        endTime: new Date(),
        progress: 100,
        memoryUsage: hardwareStatus?.memory_usage || 0
      });
      
      updateProgressStep('response-formatting', { 
        status: 'completed', 
        endTime: new Date(),
        progress: 100 
      });
      
      setCurrentAnswer(result.answer);
      setCurrentConfidence(result.confidence);
    } catch (error) {
      console.error('Question failed:', error);
      // Mark current step as error
      const currentStep = progressSteps.find(s => s.status === 'processing');
      if (currentStep) {
        updateProgressStep(currentStep.id, { 
          status: 'error', 
          endTime: new Date(),
          errorMessage: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  };

  const handleStreamAnswer = (answer: string, confidence: number) => {
    setCurrentAnswer(answer);
    setCurrentConfidence(confidence);
    setIsStreaming(false);
  };

  const handleStreamError = (error: string) => {
    console.error('Stream error:', error);
    setIsStreaming(false);
  };

  const handleInitialize = async () => {
    try {
      await initMutation.mutateAsync();
      setInitDialog(false);
      refetchStatus();
    } catch (error) {
      console.error('Initialization failed:', error);
    }
  };

  const getSystemStatusColor = (): 'success' | 'warning' | 'error' | 'default' => {
    if (!status) return 'default';
    if (status.ready) return 'success';
    if (Object.values(status.models).some(Boolean)) return 'warning';
    return 'error';
  };

  const getSystemStatusText = () => {
    if (!status) return 'Loading...';
    if (status.ready) return 'Ready';
    if (Object.values(status.models).some(Boolean)) return 'Partially Ready';
    return 'Not Ready';
  };

  // Clear research state function
  const clearResearchState = () => {
    setCurrentQuestion('');
    setCurrentAnswer('');
    setCurrentConfidence(0);
    setProgressSteps([]);
    // Clear localStorage
    localStorage.removeItem(STORAGE_KEYS.CURRENT_QUESTION);
    localStorage.removeItem(STORAGE_KEYS.CURRENT_ANSWER);
    localStorage.removeItem(STORAGE_KEYS.CURRENT_CONFIDENCE);
    localStorage.removeItem(STORAGE_KEYS.PROGRESS_STEPS);
  };

  // Utility model configuration functions
  const fetchUtilityConfig = async () => {
    try {
      const response = await fetch('/api/rag/utility-config');
      if (response.ok) {
        const config = await response.json();
        setUtilityConfig(config);
      }
    } catch (error) {
      console.error('Failed to fetch utility config:', error);
    }
  };

  const updateUtilityConfig = async (newConfig: typeof utilityConfig) => {
    try {
      const response = await fetch('/api/rag/utility-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newConfig),
      });
      
      if (response.ok) {
        setUtilityConfig(newConfig);
        setConfigDialog(false);
        // Refresh status to reflect changes
        refetchStatus();
      } else {
        console.error('Failed to update utility config');
      }
    } catch (error) {
      console.error('Failed to update utility config:', error);
    }
  };

  // Load utility config on component mount
  useEffect(() => {
    fetchUtilityConfig();
  }, []);

  return (
    <Box>
      {/* Header */}
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <RAGIcon sx={{ fontSize: 40 }} />
        Legal Research & Consultation
      </Typography>

      {/* System Status Alert */}
      <Alert 
        severity={status?.ready ? 'success' : 'warning'} 
        sx={{ mb: 3 }}
        action={
          <Button 
            color="inherit" 
            size="small" 
            onClick={() => refetchStatus()}
            startIcon={<RefreshIcon />}
          >
            Refresh
          </Button>
        }
      >
        <Typography variant="subtitle2" gutterBottom>
          🚀 Simple RAG System Status
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <Chip 
            label={getSystemStatusText()}
            size="small"
            style={{ 
              backgroundColor: getSystemStatusColor() === 'success' ? '#4caf50' : 
                            getSystemStatusColor() === 'warning' ? '#ff9800' : 
                            getSystemStatusColor() === 'error' ? '#f44336' : '#9e9e9e',
              color: 'white'
            }}
          />
          {status && (
            <>
              <Chip 
                label={`Models: ${Object.values(status.models).filter(Boolean).length}/3`}
                size="small"
                variant="outlined"
              />
              <Chip 
                label={`Documents: ${status.documents?.count || 0} indexed`}
                size="small"
                variant="outlined"
              />
              {hardwareStatus && (
                <Chip 
                  label={`Memory: ${hardwareStatus.memory_usage?.toFixed(1) || 0}GB used`}
                  size="small"
                  variant="outlined"
                />
              )}
            </>
          )}
        </Box>
      </Alert>

      {/* Progress Tracker */}
      {progressSteps.length > 0 && (
        <ProgressTracker
          steps={progressSteps}
          isExpanded={showProgressDetails}
          onToggleExpanded={() => setShowProgressDetails(!showProgressDetails)}
          showDetails={true}
        />
      )}

      {/* Main Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Ask Questions" />
          <Tab label="Upload Documents" />
          <Tab label="System Management" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {/* Question Interface */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
              <AskBar
                onSubmit={handleAskQuestion}
                disabled={!status?.ready}
                loading={askMutation.isPending || isStreaming}
                placeholder="Ask a legal question using the Simple RAG system..."
              />
              {(currentQuestion || currentAnswer) && (
                <Button
                  variant="outlined"
                  size="small"
                  onClick={clearResearchState}
                  sx={{ minWidth: 'auto' }}
                >
                  Clear
                </Button>
              )}
            </Box>
          </Grid>

          {currentQuestion && (
            <Grid item xs={12}>
              <Paper sx={{ p: 2, mb: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Question:
                </Typography>
                <Typography variant="body1">
                  {currentQuestion}
                </Typography>
              </Paper>
            </Grid>
          )}

          {currentAnswer && (
            <Grid item xs={12}>
              {isStreaming ? (
                <StreamPane 
                  question={currentQuestion}
                  onAnswer={handleStreamAnswer}
                  onError={handleStreamError}
                />
              ) : (
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">
                        Legal Analysis Result
                      </Typography>
                      <Chip 
                        label={`Confidence: ${(currentConfidence * 100).toFixed(1)}%`}
                        size="small"
                        style={{ 
                          backgroundColor: currentConfidence > 0.8 ? '#4caf50' : 
                                        currentConfidence > 0.6 ? '#1f4e79' : '#ff9800',
                          color: 'white'
                        }}
                      />
                    </Box>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {currentAnswer}
                    </Typography>
                  </CardContent>
                </Card>
              )}
            </Grid>
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Document Upload */}
        <UploadZone
          onUploadComplete={(taskId) => {
            console.log('Upload completed:', taskId);
            // Optionally refetch status after upload
            setTimeout(() => refetchStatus(), 5000);
          }}
          onError={(error) => {
            console.error('Upload error:', error);
          }}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* System Management */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SettingsIcon />
                  System Control
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="contained"
                    onClick={handleInitialize}
                    disabled={initMutation.isPending}
                    fullWidth
                  >
                    {initMutation.isPending ? 'Initializing...' : 'Initialize System'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={() => warmupMutation.mutate()}
                    disabled={warmupMutation.isPending}
                    fullWidth
                  >
                    {warmupMutation.isPending ? 'Warming Up...' : 'Warm Up Models'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={() => clearCacheMutation.mutate()}
                    disabled={clearCacheMutation.isPending}
                    startIcon={<MemoryIcon />}
                    fullWidth
                  >
                    Clear GPU Cache
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PerformanceIcon />
                  Performance Stats
                </Typography>
                
                {hardwareStatus ? (
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Memory Usage: {hardwareStatus.memory_usage?.toFixed(1) || 0}GB / {hardwareStatus.total_memory?.toFixed(1) || 0}GB
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={hardwareStatus.total_memory ? 
                        (hardwareStatus.memory_usage / hardwareStatus.total_memory) * 100 : 0
                      }
                      sx={{ mb: 2 }}
                    />
                    
                    <Typography variant="body2">
                      GPU Available: {hardwareStatus.gpu_available ? '✅' : '❌'}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary">
                      CPU-Based Generation: Enabled
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Loading hardware status...
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TuneIcon />
                  Utility Model Configuration
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body1">
                      Enable Utility Model
                    </Typography>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={utilityConfig.enabled}
                          onChange={(e) => setUtilityConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                        />
                      }
                      label=""
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Relevance Threshold: {utilityConfig.threshold.toFixed(2)}
                    </Typography>
                    <Slider
                      value={utilityConfig.threshold}
                      onChange={(_, value) => setUtilityConfig(prev => ({ ...prev, threshold: value as number }))}
                      min={0.0}
                      max={1.0}
                      step={0.05}
                      marks={[
                        { value: 0.0, label: '0.0' },
                        { value: 0.5, label: '0.5' },
                        { value: 1.0, label: '1.0' }
                      ]}
                      disabled={!utilityConfig.enabled}
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary">
                    Model: {utilityConfig.model_name}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {utilityConfig.enabled 
                      ? "Utility model is enabled and will filter chunks by relevance before passing to the main LLM."
                      : "Utility model is disabled. All retrieved chunks will be passed directly to the main LLM."
                    }
                  </Typography>
                  
                  <Button
                    variant="contained"
                    onClick={() => updateUtilityConfig(utilityConfig)}
                    fullWidth
                  >
                    Update Configuration
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Initialization Dialog */}
      <Dialog open={initDialog} onClose={() => setInitDialog(false)}>
        <DialogTitle>Initialize Simple RAG System</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            The Simple RAG system needs to be initialized before use. This will:
          </Typography>
          <Box component="ul" sx={{ pl: 2 }}>
            <li>Load embedding model for semantic search</li>
            <li>Load utility model for chunk relevance analysis</li>
            <li>Load reasoning model (Mistral-7B) for answer generation</li>
            <li>Initialize vector store for document retrieval</li>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This may take a few minutes on first run.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInitDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleInitialize} 
            variant="contained"
            disabled={initMutation.isPending}
          >
            {initMutation.isPending ? 'Initializing...' : 'Initialize'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Research;