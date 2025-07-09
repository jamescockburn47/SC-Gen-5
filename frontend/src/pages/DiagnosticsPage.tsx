import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Button,
  TextField,
  Alert,
  Divider,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  BugReport as BugReportIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import SystemMonitor from '../components/SystemMonitor';

interface TestResult {
  test: string;
  status: 'success' | 'error' | 'timeout';
  duration: number;
  message: string;
  timestamp: Date;
}

const DiagnosticsPage: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [testQuestion, setTestQuestion] = useState('What are the key points about document processing?');

  const runBackendHealthCheck = async (): Promise<TestResult> => {
    const startTime = Date.now();
    try {
      const response = await fetch('http://localhost:8001/api/rag/status');
      const duration = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          test: 'Backend Health Check',
          status: 'success',
          duration,
          message: `Backend is online. Models: ${JSON.stringify(data.models)}`,
          timestamp: new Date()
        };
      } else {
        return {
          test: 'Backend Health Check',
          status: 'error',
          duration,
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date()
        };
      }
    } catch (error) {
      return {
        test: 'Backend Health Check',
        status: 'timeout',
        duration: Date.now() - startTime,
        message: error instanceof Error ? error.message : 'Network error',
        timestamp: new Date()
      };
    }
  };

  const runDocumentTest = async (): Promise<TestResult> => {
    const startTime = Date.now();
    try {
      const response = await fetch('http://localhost:8001/api/rag/documents');
      const duration = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          test: 'Document Store Test',
          status: 'success',
          duration,
          message: `Found ${data.documents?.length || 0} documents with ${data.total_chunks || 0} chunks`,
          timestamp: new Date()
        };
      } else {
        return {
          test: 'Document Store Test',
          status: 'error',
          duration,
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date()
        };
      }
    } catch (error) {
      return {
        test: 'Document Store Test',
        status: 'timeout',
        duration: Date.now() - startTime,
        message: error instanceof Error ? error.message : 'Network error',
        timestamp: new Date()
      };
    }
  };

  const runQuestionTest = async (question: string): Promise<TestResult> => {
    const startTime = Date.now();
    try {
      const response = await fetch('http://localhost:8001/api/rag/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          max_chunks: 5,
          min_relevance: 0.3,
          include_sources: true,
          response_style: 'detailed'
        })
      });
      const duration = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          test: 'Question Answering Test',
          status: 'success',
          duration,
          message: `Generated answer with ${data.sources?.length || 0} sources. Confidence: ${data.confidence || 'N/A'}`,
          timestamp: new Date()
        };
      } else {
        return {
          test: 'Question Answering Test',
          status: 'error',
          duration,
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date()
        };
      }
    } catch (error) {
      return {
        test: 'Question Answering Test',
        status: 'timeout',
        duration: Date.now() - startTime,
        message: error instanceof Error ? error.message : 'Network error',
        timestamp: new Date()
      };
    }
  };

  const runUploadTest = async (): Promise<TestResult> => {
    const startTime = Date.now();
    try {
      // Create a simple test document
      const testContent = 'This is a test document for diagnostics. It contains sample text to verify document processing capabilities.';
      const blob = new Blob([testContent], { type: 'text/plain' });
      const file = new File([blob], 'test_diagnostic.txt', { type: 'text/plain' });
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8001/api/rag/upload', {
        method: 'POST',
        body: formData
      });
      const duration = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          test: 'Document Upload Test',
          status: 'success',
          duration,
          message: `Uploaded test document. Document ID: ${data.document_id}`,
          timestamp: new Date()
        };
      } else {
        return {
          test: 'Document Upload Test',
          status: 'error',
          duration,
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date()
        };
      }
    } catch (error) {
      return {
        test: 'Document Upload Test',
        status: 'timeout',
        duration: Date.now() - startTime,
        message: error instanceof Error ? error.message : 'Network error',
        timestamp: new Date()
      };
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    const results: TestResult[] = [];
    
    // Run tests sequentially
    results.push(await runBackendHealthCheck());
    results.push(await runDocumentTest());
    results.push(await runUploadTest());
    results.push(await runQuestionTest(testQuestion));
    
    setTestResults(results);
    setIsRunning(false);
  };

  const runSingleTest = async (testFunction: () => Promise<TestResult>, testName: string) => {
    setIsRunning(true);
    const result = await testFunction();
    setTestResults(prev => [...prev, result]);
    setIsRunning(false);
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'timeout':
        return <WarningIcon color="warning" />;
      default:
        return <WarningIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'timeout':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <BugReportIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        System Diagnostics
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Comprehensive testing and monitoring tools for the RAG system
      </Typography>

      <Grid container spacing={3}>
        {/* System Monitor */}
        <Grid item xs={12}>
          <SystemMonitor />
        </Grid>

        {/* Test Controls */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Diagnostic Tests"
              action={
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={isRunning ? <CircularProgress size={16} /> : <PlayIcon />}
                    onClick={runAllTests}
                    disabled={isRunning}
                  >
                    {isRunning ? 'Running...' : 'Run All Tests'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={clearResults}
                    disabled={isRunning}
                  >
                    Clear Results
                  </Button>
                </Box>
              }
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Test Question"
                    value={testQuestion}
                    onChange={(e) => setTestQuestion(e.target.value)}
                    disabled={isRunning}
                    multiline
                    rows={2}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => runSingleTest(runBackendHealthCheck, 'Backend Health Check')}
                      disabled={isRunning}
                    >
                      Health Check
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => runSingleTest(runDocumentTest, 'Document Test')}
                      disabled={isRunning}
                    >
                      Document Test
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => runSingleTest(runUploadTest, 'Upload Test')}
                      disabled={isRunning}
                    >
                      Upload Test
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => runSingleTest(() => runQuestionTest(testQuestion), 'Question Test')}
                      disabled={isRunning}
                    >
                      Question Test
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Test Results */}
        {testResults.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Test Results" />
              <CardContent>
                <Box sx={{ spaceY: 2 }}>
                  {testResults.map((result, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getStatusIcon(result.status)}
                          <Typography variant="subtitle1" fontWeight="medium">
                            {result.test}
                          </Typography>
                          <Chip
                            label={result.status}
                            color={getStatusColor(result.status)}
                            size="small"
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {result.duration}ms
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {result.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {result.timestamp.toLocaleString()}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Troubleshooting Guide */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Troubleshooting Guide</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ spaceY: 2 }}>
                <Alert severity="info">
                  <Typography variant="subtitle2" gutterBottom>Common Issues:</Typography>
                  <Typography variant="body2" component="div">
                    <ul>
                      <li><strong>Backend Offline:</strong> Check if the server is running on port 8001</li>
                      <li><strong>Model Loading Errors:</strong> Verify GPU memory and model availability</li>
                      <li><strong>Timeout Errors:</strong> Check network connectivity and server load</li>
                      <li><strong>Document Processing Issues:</strong> Verify document format and content</li>
                    </ul>
                  </Typography>
                </Alert>
                
                <Alert severity="warning">
                  <Typography variant="subtitle2" gutterBottom>Performance Tips:</Typography>
                  <Typography variant="body2">
                    • Monitor GPU memory usage during model loading<br/>
                    • Use CPU-based models for stability<br/>
                    • Check system resources during heavy operations
                  </Typography>
                </Alert>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DiagnosticsPage; 