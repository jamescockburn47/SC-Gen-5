import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  IconButton,
  Collapse,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Search as SearchIcon,
  Psychology as ModelIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Timer as TimerIcon,
  Storage as StorageIcon,
  TextSnippet as TextIcon
} from '@mui/icons-material';

export interface ProcessingStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error' | 'skipped';
  progress: number; // 0-100
  message: string;
  startTime?: Date;
  endTime?: Date;
  estimatedDuration?: number; // seconds
  chunksProcessed?: number;
  totalChunks?: number;
  modelUsed?: string;
  memoryUsage?: number; // GB
  errorMessage?: string;
}

export interface ProgressTrackerProps {
  steps: ProcessingStep[];
  isExpanded?: boolean;
  onToggleExpanded?: () => void;
  showDetails?: boolean;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  steps,
  isExpanded = false,
  onToggleExpanded,
  showDetails = true
}) => {
  const getStatusColor = (status: ProcessingStep['status']): string => {
    switch (status) {
      case 'completed': return '#4caf50'; // green
      case 'processing': return '#2196f3'; // blue
      case 'error': return '#f44336'; // red
      case 'skipped': return '#ff9800'; // orange
      default: return '#9e9e9e'; // grey
    }
  };

  const getStatusIcon = (status: ProcessingStep['status']) => {
    switch (status) {
      case 'completed': return <CheckIcon style={{ color: '#4caf50' }} />;
      case 'processing': return <CircularProgress size={16} style={{ color: '#2196f3' }} />;
      case 'error': return <ErrorIcon style={{ color: '#f44336' }} />;
      case 'skipped': return <WarningIcon style={{ color: '#ff9800' }} />;
      default: return null;
    }
  };

  const getStepIcon = (stepName: string) => {
    const name = stepName.toLowerCase();
    if (name.includes('search') || name.includes('retrieval')) return <SearchIcon />;
    if (name.includes('model') || name.includes('generation')) return <ModelIcon />;
    if (name.includes('memory') || name.includes('cache')) return <MemoryIcon />;
    if (name.includes('speed') || name.includes('performance')) return <SpeedIcon />;
    if (name.includes('chunk') || name.includes('text')) return <TextIcon />;
    if (name.includes('storage') || name.includes('vector')) return <StorageIcon />;
    return <TimerIcon />;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs.toFixed(0)}s`;
  };

  const getElapsedTime = (step: ProcessingStep) => {
    if (!step.startTime) return '';
    const startTime = step.startTime instanceof Date ? step.startTime : new Date(step.startTime);
    const end = step.endTime ? (step.endTime instanceof Date ? step.endTime : new Date(step.endTime)) : new Date();
    const elapsed = (end.getTime() - startTime.getTime()) / 1000;
    return formatDuration(elapsed);
  };

  const getEstimatedTimeRemaining = (step: ProcessingStep) => {
    if (!step.startTime || !step.estimatedDuration) return '';
    const startTime = step.startTime instanceof Date ? step.startTime : new Date(step.startTime);
    const elapsed = (new Date().getTime() - startTime.getTime()) / 1000;
    const remaining = Math.max(0, step.estimatedDuration - elapsed);
    return formatDuration(remaining);
  };

  const getProgressMessage = (step: ProcessingStep) => {
    if (step.status === 'completed') {
      return `Completed in ${getElapsedTime(step)}`;
    }
    if (step.status === 'processing') {
      const remaining = getEstimatedTimeRemaining(step);
      return remaining ? `Estimated ${remaining} remaining` : step.message;
    }
    if (step.status === 'error') {
      return step.errorMessage || 'Error occurred';
    }
    return step.message;
  };

  const completedSteps = steps.filter(s => s.status === 'completed').length;
  const totalSteps = steps.length;
  const overallProgress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon style={{ color: '#1f4e79' }} />
            <Typography variant="h6">Processing Progress</Typography>
            <Chip 
              label={`${completedSteps}/${totalSteps} steps`}
              size="small"
              style={{ backgroundColor: '#1f4e79', color: 'white' }}
            />
          </Box>
          {onToggleExpanded && (
            <IconButton onClick={onToggleExpanded} size="small">
              {isExpanded ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
          )}
        </Box>

        {/* Overall Progress */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Overall Progress</Typography>
            <Typography variant="body2" style={{ color: '#666' }}>
              {overallProgress.toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={overallProgress}
            sx={{ 
              height: 8, 
              borderRadius: 4,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: '#1f4e79'
              }
            }}
          />
        </Box>

        {/* Step Details */}
        <Collapse in={isExpanded || showDetails}>
          <Box sx={{ mt: 2 }}>
            {steps.map((step, index) => (
              <Box key={step.id} sx={{ mb: 2 }}>
                {/* Step Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {getStepIcon(step.name)}
                  <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                    {step.name}
                  </Typography>
                  <Chip
                    icon={getStatusIcon(step.status) || undefined}
                    label={step.status.toUpperCase()}
                    size="small"
                    style={{ 
                      backgroundColor: getStatusColor(step.status),
                      color: 'white'
                    }}
                  />
                  {step.modelUsed && (
                    <Chip
                      label={step.modelUsed}
                      size="small"
                      variant="outlined"
                      style={{ borderColor: '#1f4e79', color: '#1f4e79' }}
                    />
                  )}
                </Box>

                {/* Progress Bar */}
                <Box sx={{ mb: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={step.progress}
                    sx={{ 
                      height: 6, 
                      borderRadius: 3,
                      backgroundColor: '#e0e0e0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getStatusColor(step.status)
                      }
                    }}
                  />
                </Box>

                {/* Step Details */}
                <Grid container spacing={1} sx={{ mt: 1 }}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" style={{ color: '#666' }}>
                      {getProgressMessage(step)}
                    </Typography>
                  </Grid>
                  
                  {step.chunksProcessed && step.totalChunks && (
                    <Grid item xs={12} sm={3}>
                      <Typography variant="caption" style={{ color: '#666' }}>
                        Chunks: {step.chunksProcessed}/{step.totalChunks}
                      </Typography>
                    </Grid>
                  )}
                  
                  {step.memoryUsage && (
                    <Grid item xs={12} sm={3}>
                      <Typography variant="caption" style={{ color: '#666' }}>
                        Memory: {step.memoryUsage.toFixed(1)}GB
                      </Typography>
                    </Grid>
                  )}
                </Grid>

                {/* Error Display */}
                {step.status === 'error' && step.errorMessage && (
                  <Alert severity="error" sx={{ mt: 1 }}>
                    <Typography variant="caption">{step.errorMessage}</Typography>
                  </Alert>
                )}
              </Box>
            ))}
          </Box>
        </Collapse>

        {/* Summary Stats */}
        {!isExpanded && showDetails && (
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" style={{ color: '#666' }}>Completed</Typography>
                <Typography variant="body2">{completedSteps}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" style={{ color: '#666' }}>Processing</Typography>
                <Typography variant="body2">
                  {steps.filter(s => s.status === 'processing').length}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" style={{ color: '#666' }}>Errors</Typography>
                <Typography variant="body2" style={{ color: '#f44336' }}>
                  {steps.filter(s => s.status === 'error').length}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" style={{ color: '#666' }}>Total Time</Typography>
                <Typography variant="body2">
                  {formatDuration(steps.reduce((total, step) => {
                    if (step.startTime && step.endTime) {
                      const startTime = step.startTime instanceof Date ? step.startTime : new Date(step.startTime);
                      const endTime = step.endTime instanceof Date ? step.endTime : new Date(step.endTime);
                      return total + (endTime.getTime() - startTime.getTime()) / 1000;
                    }
                    return total;
                  }, 0))}
                </Typography>
              </Grid>
            </Grid>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default ProgressTracker; 