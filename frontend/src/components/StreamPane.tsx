import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  Alert
} from '@mui/material';
import { 
  Psychology as IssueIcon,
  Gavel as RuleIcon,
  Assignment as ApplicationIcon,
  CheckCircle as ConclusionIcon,
  Info as InfoIcon,
  Error as ErrorIcon,
  Token as TokenIcon
} from '@mui/icons-material';
import { connectStream, StreamMessage } from '../api/rag';

interface StreamPaneProps {
  question: string;
  onAnswer?: (answer: string, confidence: number) => void;
  onError?: (error: string) => void;
}

interface StreamState {
  content: string;
  step: string;
  status: string;
  iracComponents: {
    issue: string;
    rule: string;
    application: string;
    conclusion: string;
  };
  progress: {
    current: number;
    total: number;
    message: string;
  };
  isConnected: boolean;
  hasError: boolean;
  errorMessage: string;
}

const StreamPane: React.FC<StreamPaneProps> = ({ question, onAnswer, onError }) => {
  const [streamState, setStreamState] = useState<StreamState>({
    content: '',
    step: 'Initializing...',
    status: 'connecting',
    iracComponents: {
      issue: '',
      rule: '',
      application: '',
      conclusion: ''
    },
    progress: {
      current: 0,
      total: 100,
      message: ''
    },
    isConnected: false,
    hasError: false,
    errorMessage: ''
  });

  const wsRef = useRef<WebSocket | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!question) return;

    // Reset state
    setStreamState(prev => ({
      ...prev,
      content: '',
      step: 'Connecting...',
      status: 'connecting',
      isConnected: false,
      hasError: false,
      errorMessage: ''
    }));

    // Connect WebSocket
    wsRef.current = connectStream(
      question,
      handleMessage,
      handleError,
      handleClose
    );

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [question]);

  // Auto-scroll to bottom when content updates
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [streamState.content]);

  const handleMessage = (message: StreamMessage) => {
    setStreamState(prev => {
      const newState = { ...prev };

      switch (message.type) {
        case 'token':
          // Append new token to content
          newState.content += message.content || '';
          break;

        case 'step_start':
          newState.step = message.step || 'Processing...';
          newState.status = 'processing';
          break;

        case 'step_end':
          // Keep step name but mark as completed
          break;

        case 'status':
          newState.status = message.status || 'processing';
          if (message.message) {
            newState.step = message.message;
          }
          break;

        case 'progress':
          newState.progress = {
            current: message.current || 0,
            total: message.total || 100,
            message: message.message || ''
          };
          break;

        case 'irac_update':
          if (message.component && message.content) {
            newState.iracComponents = {
              ...newState.iracComponents,
              [message.component]: message.content
            };
          }
          break;

        case 'final_answer':
          newState.status = 'completed';
          newState.step = 'Complete';
          if (onAnswer && message.answer) {
            onAnswer(message.answer, message.confidence || 0);
          }
          break;

        case 'error':
          newState.hasError = true;
          newState.errorMessage = message.error || 'Unknown error';
          newState.status = 'error';
          if (onError) {
            onError(message.error || 'Stream error');
          }
          break;

        case 'llm_start':
          newState.step = `Generating with ${message.model || 'LLM'}...`;
          break;

        case 'llm_end':
          // Could show token usage stats here
          break;

        case 'context_update':
          newState.step = `Retrieved ${message.context_type || 'context'}...`;
          break;
      }

      if (message.type !== 'token') {
        console.log('Stream message:', message);
      }

      return newState;
    });
  };

  const handleError = (error: Event) => {
    console.error('WebSocket error:', error);
    setStreamState(prev => ({
      ...prev,
      hasError: true,
      errorMessage: 'Connection error',
      status: 'error',
      isConnected: false
    }));
    if (onError) {
      onError('WebSocket connection error');
    }
  };

  const handleClose = (event: CloseEvent) => {
    console.log('WebSocket closed:', event);
    setStreamState(prev => ({
      ...prev,
      isConnected: false,
      status: prev.hasError ? 'error' : 'completed'
    }));
  };

  const getStatusColor = () => {
    switch (streamState.status) {
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'processing': return 'primary';
      default: return 'default';
    }
  };

  const getProgressPercentage = () => {
    if (streamState.progress.total === 0) return 0;
    return (streamState.progress.current / streamState.progress.total) * 100;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Status Header */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ pb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Chip
              label={streamState.status.toUpperCase()}
              color={getStatusColor()}
              size="small"
            />
            <Typography variant="body2" sx={{ flexGrow: 1 }}>
              {streamState.step}
            </Typography>
          </Box>
          
          {streamState.progress.total > 0 && (
            <Box>
              <LinearProgress
                variant="determinate"
                value={getProgressPercentage()}
                sx={{ mb: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {streamState.progress.message || `${streamState.progress.current}/${streamState.progress.total}`}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {streamState.hasError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">Streaming Error</Typography>
          <Typography variant="body2">{streamState.errorMessage}</Typography>
        </Alert>
      )}

      {/* IRAC Analysis Progress */}
      {Object.values(streamState.iracComponents).some(comp => comp.length > 0) && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>IRAC Analysis Progress</Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <IssueIcon color={streamState.iracComponents.issue ? 'primary' : 'disabled'} />
                <Typography variant="body2">
                  Issue {streamState.iracComponents.issue && '✓'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <RuleIcon color={streamState.iracComponents.rule ? 'primary' : 'disabled'} />
                <Typography variant="body2">
                  Rule {streamState.iracComponents.rule && '✓'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ApplicationIcon color={streamState.iracComponents.application ? 'primary' : 'disabled'} />
                <Typography variant="body2">
                  Application {streamState.iracComponents.application && '✓'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ConclusionIcon color={streamState.iracComponents.conclusion ? 'primary' : 'disabled'} />
                <Typography variant="body2">
                  Conclusion {streamState.iracComponents.conclusion && '✓'}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Streaming Content */}
      <Paper 
        sx={{ 
          flexGrow: 1, 
          p: 2, 
          overflow: 'hidden', 
          display: 'flex', 
          flexDirection: 'column' 
        }}
      >
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TokenIcon />
          Live Response Stream
        </Typography>
        
        <Box
          ref={contentRef}
          sx={{
            flexGrow: 1,
            fontFamily: 'monospace',
            fontSize: '0.9rem',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
            overflow: 'auto',
            backgroundColor: 'grey.50',
            p: 2,
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider'
          }}
        >
          {streamState.content || (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Waiting for response stream...
            </Typography>
          )}
        </Box>
        
        {streamState.status === 'processing' && (
          <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <LinearProgress sx={{ flexGrow: 1 }} />
            <Typography variant="caption" color="text.secondary">
              Streaming...
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default StreamPane;