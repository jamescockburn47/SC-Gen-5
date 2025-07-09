import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Chip,
  Alert,
  AlertTitle,
  LinearProgress,
  IconButton,
  Tooltip,
  Grid,
  Paper
} from '@mui/material';
import {
  Monitor as ActivityIcon,
  Storage as ServerIcon,
  Psychology as BrainIcon,
  Storage as DatabaseIcon,
  Warning as AlertTriangleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as XCircleIcon,
  Refresh as RefreshIcon,
  Schedule as ClockIcon,
  FlashOn as ZapIcon
} from '@mui/icons-material';

interface SystemStatus {
  backend: {
    status: 'online' | 'offline' | 'error';
    responseTime: number;
    lastCheck: Date;
    error?: string;
  };
  models: {
    embedder: boolean;
    utility: boolean;
    generator: boolean;
    gpuMemory: number;
    cpuUsage: number;
  };
  documents: {
    total: number;
    chunks: number;
    lastUpload: Date | null;
  };
  performance: {
    avgResponseTime: number;
    requestsPerMinute: number;
    errorsLastHour: number;
  };
}

interface HealthCheck {
  timestamp: Date;
  status: 'success' | 'error' | 'timeout';
  responseTime: number;
  endpoint: string;
  error?: string;
}

const SystemMonitor: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    backend: {
      status: 'offline',
      responseTime: 0,
      lastCheck: new Date(),
    },
    models: {
      embedder: false,
      utility: false,
      generator: false,
      gpuMemory: 0,
      cpuUsage: 0,
    },
    documents: {
      total: 0,
      chunks: 0,
      lastUpload: null,
    },
    performance: {
      avgResponseTime: 0,
      requestsPerMinute: 0,
      errorsLastHour: 0,
    },
  });

  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false); // Start with auto-refresh OFF
  const [lastCheckTime, setLastCheckTime] = useState<Date | null>(null);

  // Health check endpoints to monitor
  const endpoints = [
    { name: 'Backend Status', url: '/api/rag/status' },
    { name: 'Documents', url: '/api/rag/documents' },
  ];

  const performHealthCheck = useCallback(async (endpoint: string) => {
    const startTime = Date.now();
    try {
      const response = await fetch(`http://localhost:8001${endpoint}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        return {
          timestamp: new Date(),
          status: 'success' as const,
          responseTime,
          endpoint,
        };
      } else {
        return {
          timestamp: new Date(),
          status: 'error' as const,
          responseTime,
          endpoint,
          error: `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      return {
        timestamp: new Date(),
        status: 'timeout' as const,
        responseTime: Date.now() - startTime,
        endpoint,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }, []);

  const checkSystemStatus = useCallback(async () => {
    // Prevent rapid successive requests
    if (isMonitoring) {
      return;
    }
    
    setIsMonitoring(true);
    setLastCheckTime(new Date());
    
    try {
      const checks = await Promise.all(
        endpoints.map(endpoint => performHealthCheck(endpoint.url))
      );
      
      setHealthChecks(prev => [...prev.slice(-50), ...checks]); // Keep last 50 checks

    // Update system status based on health checks
    const backendCheck = checks.find(c => c.endpoint === '/api/rag/status');
    const documentsCheck = checks.find(c => c.endpoint === '/api/rag/documents');
    
    if (backendCheck) {
      setSystemStatus(prev => ({
        ...prev,
        backend: {
          status: backendCheck.status === 'success' ? 'online' : 'offline',
          responseTime: backendCheck.responseTime,
          lastCheck: new Date(),
          error: backendCheck.error,
        },
        performance: {
          ...prev.performance,
          avgResponseTime: checks.reduce((sum, c) => sum + c.responseTime, 0) / checks.length,
          requestsPerMinute: checks.filter(c => c.timestamp > new Date(Date.now() - 60000)).length,
          errorsLastHour: checks.filter(c => 
            c.status === 'error' && c.timestamp > new Date(Date.now() - 3600000)
          ).length,
        },
      }));
    }

    // Try to get detailed status if backend is online
    if (backendCheck?.status === 'success') {
      try {
        const statusResponse = await fetch('http://localhost:8001/api/rag/status');
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setSystemStatus(prev => ({
            ...prev,
            models: {
              embedder: statusData.models?.embedder || false,
              utility: statusData.models?.utility || false,
              generator: statusData.models?.generator || false,
              gpuMemory: statusData.gpu_memory || 0,
              cpuUsage: statusData.cpu_usage || 0,
            },
          }));
        }
      } catch (error) {
        console.error('Failed to get detailed status:', error);
      }
    }

    // Get document count
    if (documentsCheck?.status === 'success') {
      try {
        const docsResponse = await fetch('http://localhost:8001/api/rag/documents');
        if (docsResponse.ok) {
          const docsData = await docsResponse.json();
          setSystemStatus(prev => ({
            ...prev,
            documents: {
              total: docsData.documents?.length || 0,
              chunks: docsData.total_chunks || 0,
              lastUpload: prev.documents.lastUpload,
            },
          }));
        }
      } catch (error) {
        console.error('Failed to get documents:', error);
      }
    }
    } catch (error) {
      console.error('System status check failed:', error);
    } finally {
      setIsMonitoring(false);
    }
  }, [performHealthCheck]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(checkSystemStatus, 30000); // Check every 30 seconds instead of 5
      return () => clearInterval(interval);
    }
  }, [autoRefresh, checkSystemStatus]);

  useEffect(() => {
    checkSystemStatus(); // Initial check
  }, [checkSystemStatus]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'success':
        return 'success';
      case 'offline':
      case 'error':
        return 'error';
      case 'timeout':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'offline':
      case 'error':
        return <XCircleIcon color="error" />;
      case 'timeout':
        return <ClockIcon color="warning" />;
      default:
        return <AlertTriangleIcon color="action" />;
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ActivityIcon />
              <Typography variant="h6">System Monitor</Typography>
              <Tooltip title="Refresh Status">
                <IconButton
                  onClick={checkSystemStatus}
                  disabled={isMonitoring}
                  size="small"
                >
                  <RefreshIcon className={isMonitoring ? 'animate-spin' : ''} />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        <CardContent>
          <Grid container spacing={2}>
            {/* Backend Status */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ServerIcon />
                    <Typography variant="body2" fontWeight="medium">Backend</Typography>
                  </Box>
                  {getStatusIcon(systemStatus.backend.status)}
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {systemStatus.backend.status === 'online' ? 'Online' : 'Offline'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {systemStatus.backend.responseTime}ms response time
                </Typography>
              </Paper>
            </Grid>

            {/* Models Status */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <BrainIcon />
                  <Typography variant="body2" fontWeight="medium">Models</Typography>
                </Box>
                <Box sx={{ spaceY: 0.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="caption">Embedder</Typography>
                    {systemStatus.models.embedder ? 
                      <CheckCircleIcon color="success" fontSize="small" /> : 
                      <XCircleIcon color="error" fontSize="small" />
                    }
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="caption">Utility</Typography>
                    {systemStatus.models.utility ? 
                      <CheckCircleIcon color="success" fontSize="small" /> : 
                      <XCircleIcon color="error" fontSize="small" />
                    }
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="caption">Generator</Typography>
                    {systemStatus.models.generator ? 
                      <CheckCircleIcon color="success" fontSize="small" /> : 
                      <XCircleIcon color="error" fontSize="small" />
                    }
                  </Box>
                </Box>
              </Paper>
            </Grid>

            {/* Documents Status */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <DatabaseIcon />
                  <Typography variant="body2" fontWeight="medium">Documents</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">{systemStatus.documents.total}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {systemStatus.documents.chunks} chunks total
                </Typography>
              </Paper>
            </Grid>

            {/* Performance */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <ZapIcon />
                  <Typography variant="body2" fontWeight="medium">Performance</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {Math.round(systemStatus.performance.avgResponseTime)}ms
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {systemStatus.performance.errorsLastHour} errors/hour
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Recent Health Checks */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>Recent Health Checks</Typography>
            <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
              {healthChecks.slice(-10).reverse().map((check, index) => (
                <Paper key={index} sx={{ p: 1, mb: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(check.status)}
                    <Typography variant="body2">{check.endpoint}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {check.responseTime}ms
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {check.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Box>
                </Paper>
              ))}
            </Box>
          </Box>

          {/* Error Alerts */}
          {systemStatus.backend.error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <AlertTitle>Backend Error</AlertTitle>
              <Typography variant="body2">
                {systemStatus.backend.error}
              </Typography>
            </Alert>
          )}

          {/* Auto-refresh warning */}
          {autoRefresh && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <AlertTitle>Auto-refresh Active</AlertTitle>
              <Typography variant="body2">
                System is automatically checking status every 30 seconds. This may generate some backend traffic.
              </Typography>
            </Alert>
          )}

          {/* Auto-refresh toggle */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <Button
              variant={autoRefresh ? "contained" : "outlined"}
              size="small"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </Button>
            <Typography variant="caption" color="text.secondary">
              {autoRefresh ? 'Checking every 30 seconds' : 'Manual refresh only'}
              {lastCheckTime && ` • Last check: ${lastCheckTime.toLocaleTimeString()}`}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemMonitor; 