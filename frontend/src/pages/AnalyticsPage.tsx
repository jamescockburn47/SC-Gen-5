import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  NetworkCheck as NetworkIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Computer as ComputerIcon,
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';
import axios from 'axios';

interface SystemMetrics {
  timestamp: string;
  cpu: {
    percent: number;
    count: number;
    temperature?: number;
  };
  memory: {
    total: number;
    available: number;
    percent: number;
    used: number;
  };
  disk: {
    total: number;
    free: number;
    percent: number;
  };
  gpu?: {
    name: string;
    load: number;
    memory_used: number;
    memory_total: number;
    memory_percent: number;
    temperature: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
  };
  uptime: number;
}

interface ServiceMetrics {
  name: string;
  status: 'running' | 'stopped' | 'error';
  port?: number;
  uptime: number;
  memory_usage: number;
  cpu_usage: number;
  request_count: number;
  error_count: number;
  response_time_avg: number;
}

interface UsageStats {
  documents: {
    total: number;
    processed_today: number;
    processing_time_avg: number;
    ocr_success_rate: number;
  };
  consultations: {
    total_sessions: number;
    sessions_today: number;
    avg_session_length: number;
    user_satisfaction: number;
  };
  companies_house: {
    searches_today: number;
    downloads_today: number;
    api_quota_used: number;
    api_quota_limit: number;
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const AnalyticsPage: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<SystemMetrics | null>(null);
  const [serviceMetrics, setServiceMetrics] = useState<ServiceMetrics[]>([]);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadAllMetrics();
    
    if (autoRefresh) {
      const interval = setInterval(loadAllMetrics, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, timeRange]);

  const loadAllMetrics = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadSystemMetrics(),
        loadServiceMetrics(),
        loadUsageStats()
      ]);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSystemMetrics = async () => {
    try {
      const response = await axios.get('/api/analytics/system-metrics', {
        params: { timeRange }
      });
      setSystemMetrics(response.data.metrics || []);
      if (response.data.metrics && response.data.metrics.length > 0) {
        setCurrentMetrics(response.data.metrics[response.data.metrics.length - 1]);
      }
    } catch (error) {
      console.error('Failed to load system metrics:', error);
    }
  };

  const loadServiceMetrics = async () => {
    try {
      const response = await axios.get('/api/analytics/service-metrics');
      setServiceMetrics(response.data.services || []);
    } catch (error) {
      console.error('Failed to load service metrics:', error);
    }
  };

  const loadUsageStats = async () => {
    try {
      const response = await axios.get('/api/analytics/usage-stats');
      setUsageStats(response.data);
    } catch (error) {
      console.error('Failed to load usage stats:', error);
    }
  };

  const exportMetrics = async () => {
    try {
      const response = await axios.get('/api/analytics/export', {
        params: { timeRange },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sc-gen5-analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getHealthStatus = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return { color: 'error', icon: <WarningIcon /> };
    if (value >= thresholds.warning) return { color: 'warning', icon: <WarningIcon /> };
    return { color: 'success', icon: <CheckCircleIcon /> };
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <AnalyticsIcon sx={{ fontSize: 40 }} />
          System Analytics
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small">
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              label="Time Range"
            >
              <MenuItem value="1h">Last Hour</MenuItem>
              <MenuItem value="6h">Last 6 Hours</MenuItem>
              <MenuItem value="24h">Last 24 Hours</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Export Metrics">
            <IconButton onClick={exportMetrics}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Refresh">
            <IconButton onClick={loadAllMetrics} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Grid container spacing={3}>
        {/* System Overview Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" color="text.secondary">
                    CPU Usage
                  </Typography>
                  <Typography variant="h4">
                    {currentMetrics?.cpu.percent.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentMetrics?.cpu.count} cores
                  </Typography>
                </Box>
                <SpeedIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={currentMetrics?.cpu.percent || 0}
                sx={{ mt: 2 }}
                color={getHealthStatus(currentMetrics?.cpu.percent || 0, { warning: 70, critical: 90 }).color as any}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" color="text.secondary">
                    Memory Usage
                  </Typography>
                  <Typography variant="h4">
                    {currentMetrics?.memory.percent.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentMetrics && formatBytes(currentMetrics.memory.used)} / {currentMetrics && formatBytes(currentMetrics.memory.total)}
                  </Typography>
                </Box>
                <MemoryIcon sx={{ fontSize: 40, color: 'secondary.main' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={currentMetrics?.memory.percent || 0}
                sx={{ mt: 2 }}
                color={getHealthStatus(currentMetrics?.memory.percent || 0, { warning: 80, critical: 95 }).color as any}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" color="text.secondary">
                    Disk Usage
                  </Typography>
                  <Typography variant="h4">
                    {currentMetrics?.disk.percent.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentMetrics && formatBytes(currentMetrics.disk.total - currentMetrics.disk.free)} / {currentMetrics && formatBytes(currentMetrics.disk.total)}
                  </Typography>
                </Box>
                <StorageIcon sx={{ fontSize: 40, color: 'info.main' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={currentMetrics?.disk.percent || 0}
                sx={{ mt: 2 }}
                color={getHealthStatus(currentMetrics?.disk.percent || 0, { warning: 80, critical: 95 }).color as any}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" color="text.secondary">
                    System Uptime
                  </Typography>
                  <Typography variant="h4">
                    {currentMetrics && formatUptime(currentMetrics.uptime)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Since last restart
                  </Typography>
                </Box>
                <ComputerIcon sx={{ fontSize: 40, color: 'success.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* GPU Card (if available) */}
        {currentMetrics?.gpu && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  GPU Performance
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    {currentMetrics.gpu.name}
                  </Typography>
                  <Chip label={`${currentMetrics.gpu.temperature}°C`} size="small" />
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">GPU Usage</Typography>
                    <Typography variant="body2">{currentMetrics.gpu.load.toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={currentMetrics.gpu.load} sx={{ mt: 1 }} />
                </Box>
                
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">VRAM Usage</Typography>
                    <Typography variant="body2">{currentMetrics.gpu.memory_percent.toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={currentMetrics.gpu.memory_percent} sx={{ mt: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    {formatBytes(currentMetrics.gpu.memory_used * 1024 * 1024)} / {formatBytes(currentMetrics.gpu.memory_total * 1024 * 1024)}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Performance Trends */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Trends ({timeRange})
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={systemMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="cpu.percent" stroke="#8884d8" name="CPU %" strokeWidth={2} />
                  <Line type="monotone" dataKey="memory.percent" stroke="#82ca9d" name="Memory %" strokeWidth={2} />
                  <Line type="monotone" dataKey="disk.percent" stroke="#ffc658" name="Disk %" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Status
              </Typography>
              <List dense>
                {serviceMetrics.map((service, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {getHealthStatus(
                        service.status === 'running' ? 0 : 100, 
                        { warning: 50, critical: 90 }
                      ).icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={service.name}
                      secondary={
                        <Box>
                          <Typography variant="caption">
                            {service.status} • {service.port ? `Port ${service.port}` : 'No port'}
                          </Typography>
                          <br />
                          <Typography variant="caption">
                            CPU: {service.cpu_usage.toFixed(1)}% • RAM: {formatBytes(service.memory_usage)}
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip
                      label={service.status}
                      color={
                        service.status === 'running' ? 'success' :
                        service.status === 'stopped' ? 'warning' : 'error'
                      }
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Usage Statistics */}
        {usageStats && (
          <>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Document Processing
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Total Documents</Typography>
                      <Chip label={usageStats.documents.total} color="primary" size="small" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Processed Today</Typography>
                      <Chip label={usageStats.documents.processed_today} color="secondary" size="small" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">OCR Success Rate</Typography>
                      <Chip 
                        label={`${usageStats.documents.ocr_success_rate.toFixed(1)}%`} 
                        color="success" 
                        size="small" 
                      />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Avg Processing Time</Typography>
                      <Typography variant="body2">
                        {usageStats.documents.processing_time_avg.toFixed(1)}s
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Legal Consultations
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Total Sessions</Typography>
                      <Chip label={usageStats.consultations.total_sessions} color="primary" size="small" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Sessions Today</Typography>
                      <Chip label={usageStats.consultations.sessions_today} color="secondary" size="small" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Avg Session Length</Typography>
                      <Typography variant="body2">
                        {formatUptime(usageStats.consultations.avg_session_length)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">User Satisfaction</Typography>
                      <Chip 
                        label={`${usageStats.consultations.user_satisfaction.toFixed(1)}/5`} 
                        color="success" 
                        size="small" 
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Companies House
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Searches Today</Typography>
                      <Chip label={usageStats.companies_house.searches_today} color="primary" size="small" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Downloads Today</Typography>
                      <Chip label={usageStats.companies_house.downloads_today} color="secondary" size="small" />
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">API Quota</Typography>
                        <Typography variant="body2">
                          {usageStats.companies_house.api_quota_used} / {usageStats.companies_house.api_quota_limit}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(usageStats.companies_house.api_quota_used / usageStats.companies_house.api_quota_limit) * 100}
                        color={
                          (usageStats.companies_house.api_quota_used / usageStats.companies_house.api_quota_limit) > 0.9 
                            ? 'error' 
                            : (usageStats.companies_house.api_quota_used / usageStats.companies_house.api_quota_limit) > 0.7 
                              ? 'warning' 
                              : 'primary'
                        }
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Alerts and Recommendations */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health & Recommendations
              </Typography>
              
              {currentMetrics && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {currentMetrics.cpu.percent > 90 && (
                    <Alert severity="error">
                      High CPU usage detected ({currentMetrics.cpu.percent.toFixed(1)}%). Consider reducing workload or upgrading hardware.
                    </Alert>
                  )}
                  {currentMetrics.memory.percent > 95 && (
                    <Alert severity="error">
                      Critical memory usage ({currentMetrics.memory.percent.toFixed(1)}%). System may become unstable.
                    </Alert>
                  )}
                  {currentMetrics.disk.percent > 90 && (
                    <Alert severity="warning">
                      Disk space running low ({currentMetrics.disk.percent.toFixed(1)}%). Consider cleaning up old files.
                    </Alert>
                  )}
                  {currentMetrics.gpu && currentMetrics.gpu.temperature > 80 && (
                    <Alert severity="warning">
                      GPU temperature is high ({currentMetrics.gpu.temperature}°C). Check cooling.
                    </Alert>
                  )}
                  {serviceMetrics.some(s => s.status === 'error') && (
                    <Alert severity="error">
                      Some services are in error state. Check service logs for details.
                    </Alert>
                  )}
                  {usageStats && usageStats.companies_house.api_quota_used / usageStats.companies_house.api_quota_limit > 0.9 && (
                    <Alert severity="warning">
                      Companies House API quota nearly exhausted. Consider upgrading your plan.
                    </Alert>
                  )}
                  
                  {/* Success messages */}
                  {currentMetrics.cpu.percent < 50 && currentMetrics.memory.percent < 70 && (
                    <Alert severity="success">
                      System performance is optimal. All metrics within normal ranges.
                    </Alert>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AnalyticsPage;