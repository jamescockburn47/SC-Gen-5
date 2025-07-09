import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Alert
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Description as DocumentIcon,
  Business as BusinessIcon,
  Analytics as AnalyticsIcon,
  Psychology as RAGIcon,
  AutoAwesome as AIIcon
} from '@mui/icons-material';
import { useRAGStatus, useHardwareStatus } from '../api/rag';

interface SystemStats {
  gpu: { usage: number; memory: string };
  ram: { usage: number; memory: string };
  cpu: { usage: number; cores: number };
  storage: { usage: number; space: string };
}

interface Service {
  name: string;
  status: 'running' | 'stopped';
  port: number | null;
}

interface Activity {
  action: string;
  file?: string;
  query?: string;
  company?: string;
  task?: string;
  time: string;
}

const Dashboard: React.FC = () => {
  const [systemStats, setSystemStats] = React.useState<SystemStats | null>(null);
  const [services, setServices] = React.useState<Service[]>([]);
  const [recentActivity, setRecentActivity] = React.useState<Activity[]>([]);
  const [dashboardStats, setDashboardStats] = React.useState({
    documents: 0,
    companies: 0,
    queries: 0,
    avgResponseTime: '0s'
  });

  // RAG v2 status hooks
  const { data: ragStatus, isLoading: ragLoading } = useRAGStatus();
  const { data: hardwareStatus, isLoading: hardwareLoading } = useHardwareStatus();

  React.useEffect(() => {
    fetchDashboardData();
    fetchSystemStats();
    fetchServices();
    updateRecentActivity();
    
    // Update system stats every 10 seconds
    const statsInterval = setInterval(fetchSystemStats, 10000);
    // Update dashboard data every 30 seconds
    const dataInterval = setInterval(fetchDashboardData, 30000);
    
    return () => {
      clearInterval(statsInterval);
      clearInterval(dataInterval);
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard/stats');
      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data);
      }
    } catch (error) {
      console.log('Using development mode - API not available');
    }
  };
  
  const fetchSystemStats = async () => {
    try {
      const response = await fetch('/api/system/stats');
      if (response.ok) {
        const data = await response.json();
        setSystemStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch system stats:', error);
      // Set fallback data
      setSystemStats({
        gpu: { usage: 0, memory: 'N/A' },
        ram: { usage: 0, memory: 'N/A' },
        cpu: { usage: 0, cores: 0 },
        storage: { usage: 0, space: 'N/A' }
      });
    }
  };
  
  const fetchServices = async () => {
    try {
      // Check which services are running
      const serviceChecks = [
        { name: 'FastAPI Backend', port: 8001, endpoint: '/api/rag/status' },
        { name: 'React Frontend', port: 3000, endpoint: null },
      ];
      
      const serviceStatuses = await Promise.all(
        serviceChecks.map(async (service) => {
          try {
            if (service.endpoint) {
              const response = await fetch(`http://localhost:${service.port}${service.endpoint}`, {
                signal: AbortSignal.timeout(2000)
              });
              return {
                ...service,
                status: response.ok ? 'running' as const : 'stopped' as const
              };
            } else {
              // For services without health endpoints, assume running if we can reach this code
              return { ...service, status: 'running' as const };
            }
          } catch {
            return { ...service, status: 'stopped' as const };
          }
        })
      );
      
      setServices(serviceStatuses);
    } catch (error) {
      console.error('Failed to check services:', error);
      setServices([]);
    }
  };
  
  const updateRecentActivity = () => {
    // Simulate recent activity based on current system state
    const now = new Date();
    const activities: Activity[] = [
      {
        action: 'System monitoring started',
        task: 'Dashboard initialization',
        time: now.toLocaleTimeString()
      },
      {
        action: 'API services checked',
        task: 'Service health monitoring',
        time: new Date(now.getTime() - 30000).toLocaleTimeString()
      },
      {
        action: 'System stats updated',
        task: 'Performance monitoring',
        time: new Date(now.getTime() - 60000).toLocaleTimeString()
      }
    ];
    
    setRecentActivity(activities);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <DashboardIcon sx={{ fontSize: 40 }} />
        LexCognito Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Performance */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Performance
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">GPU Usage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats?.gpu.usage || 0} 
                        sx={{ flexGrow: 1 }}
                        color="success"
                      />
                      <Typography variant="body2">{systemStats?.gpu.usage || 0}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats?.gpu.memory || 'N/A'}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">RAM Usage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats?.ram.usage || 0} 
                        sx={{ flexGrow: 1 }}
                        color="primary"
                      />
                      <Typography variant="body2">{systemStats?.ram.usage || 0}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats?.ram.memory || 'N/A'}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">CPU Usage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats?.cpu.usage || 0} 
                        sx={{ flexGrow: 1 }}
                        color="secondary"
                      />
                      <Typography variant="body2">{systemStats?.cpu.usage || 0}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats?.cpu.cores || 0} cores</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">Storage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats?.storage.usage || 0} 
                        sx={{ flexGrow: 1 }}
                        color="info"
                      />
                      <Typography variant="body2">{systemStats?.storage.usage || 0}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats?.storage.space || 'N/A'}</Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Simple RAG System Status */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <RAGIcon color="primary" />
                Simple RAG System Status
              </Typography>
              
              {ragLoading ? (
                <LinearProgress sx={{ mb: 2 }} />
              ) : (
                <Grid container spacing={2}>
                  {/* Models Status */}
                  <Grid item xs={12} md={4}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>AI Models (Lazy Loading)</Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            <AIIcon color={ragStatus?.models?.utility ? "success" : "info"} />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Mistral-7B (Main)" 
                            secondary={ragStatus?.models?.utility ? "Loaded - Ready for use" : "Will load on first use"}
                          />
                          <Chip 
                            label={ragStatus?.models?.utility ? "Ready" : "Lazy Load"} 
                            color={ragStatus?.models?.utility ? "success" : "info"}
                            size="small"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <AIIcon color={ragStatus?.models?.reasoning ? "success" : "info"} />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Mistral-7B (Generation)" 
                            secondary={ragStatus?.models?.reasoning ? "Loaded - Answer Generation" : "Will load on first use"}
                          />
                          <Chip 
                            label={ragStatus?.models?.reasoning ? "Ready" : "Lazy Load"} 
                            color={ragStatus?.models?.reasoning ? "success" : "info"}
                            size="small"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <MemoryIcon color={ragStatus?.models?.embedder ? "success" : "warning"} />
                          </ListItemIcon>
                          <ListItemText 
                            primary="BGE Embeddings" 
                            secondary={ragStatus?.models?.embedder ? "Loaded - Semantic Search" : "Not loaded"}
                          />
                          <Chip 
                            label={ragStatus?.models?.embedder ? "Ready" : "Loading"} 
                            color={ragStatus?.models?.embedder ? "success" : "warning"}
                            size="small"
                          />
                        </ListItem>
                      </List>
                    </Box>
                  </Grid>
                  
                  {/* Vector Stores */}
                  <Grid item xs={12} md={4}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>Vector Stores</Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            <StorageIcon color={ragStatus?.documents?.indexed ? "success" : "warning"} />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Document Store" 
                            secondary={`${ragStatus?.documents?.count || 0} documents (${ragStatus?.chunks?.count || 0} chunks)`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <StorageIcon color={ragStatus?.ready ? "success" : "warning"} />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Vector Index" 
                            secondary={ragStatus?.ready ? "Ready" : "Not Ready"}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <StorageIcon color={ragStatus?.status === "ready" ? "success" : "warning"} />
                          </ListItemIcon>
                          <ListItemText 
                            primary="System Status" 
                            secondary={ragStatus?.message || "Checking..."}
                          />
                        </ListItem>
                      </List>
                    </Box>
                  </Grid>
                  
                  {/* Hardware Status */}
                  <Grid item xs={12} md={4}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>Hardware Optimization</Typography>
                      {hardwareLoading ? (
                        <LinearProgress />
                      ) : (
                        <List dense>
                          <ListItem>
                            <ListItemIcon>
                              <CheckIcon color={hardwareStatus?.gpu_available ? "success" : "warning"} />
                            </ListItemIcon>
                            <ListItemText 
                              primary="GPU Status" 
                              secondary={hardwareStatus?.gpu_available ? "Available" : "CPU Only"}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <MemoryIcon color="info" />
                            </ListItemIcon>
                            <ListItemText 
                              primary="Memory Usage" 
                              secondary={`${hardwareStatus?.memory_usage?.toFixed(1) || 0}GB / ${hardwareStatus?.total_memory?.toFixed(1) || 0}GB`}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <SpeedIcon color="info" />
                            </ListItemIcon>
                            <ListItemText 
                              primary="System Status" 
                              secondary="CPU-Based Generation"
                            />
                          </ListItem>
                        </List>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <DocumentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4">{dashboardStats.documents}</Typography>
                  <Typography variant="body2" color="textSecondary">Documents</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <BusinessIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="h4">{dashboardStats.companies}</Typography>
                  <Typography variant="body2" color="textSecondary">Companies</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <AnalyticsIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4">{dashboardStats.queries}</Typography>
                  <Typography variant="body2" color="textSecondary">Queries</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <SpeedIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography variant="h4">{dashboardStats.avgResponseTime}</Typography>
                  <Typography variant="body2" color="textSecondary">Avg Response</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Service Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Service Status</Typography>
              <List dense>
                {services.length > 0 ? services.map((service, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {service.status === 'running' ? 
                        <CheckIcon color="success" /> : 
                        <WarningIcon color="warning" />
                      }
                    </ListItemIcon>
                    <ListItemText
                      primary={service.name}
                      secondary={service.port ? `Port ${service.port}` : 'Ready'}
                    />
                    <Chip 
                      label={service.status} 
                      color={service.status === 'running' ? 'success' : 'warning'}
                      size="small"
                    />
                  </ListItem>
                )) : (
                  <ListItem>
                    <ListItemText primary="No services configured" secondary="System monitoring not yet implemented" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recent Activity</Typography>
              <List dense>
                {recentActivity.length > 0 ? recentActivity.map((activity, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={activity.action}
                      secondary={`${activity.file || activity.query || activity.company || activity.task} • ${activity.time}`}
                    />
                  </ListItem>
                )) : (
                  <ListItem>
                    <ListItemText primary="No recent activity" secondary="Activity tracking not yet implemented" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Quick Actions</Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button variant="contained" color="primary">
                  New Legal Query
                </Button>
                <Button variant="outlined">
                  Upload Documents
                </Button>
                <Button variant="outlined">
                  Company Lookup
                </Button>
                <Button variant="outlined">
                  Open Terminal
                </Button>
                <Button variant="outlined">
                  View Analytics
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Info */}
        <Grid item xs={12}>
          <Alert severity="info">
            <Typography variant="subtitle2" gutterBottom>
              ⚖️ LexCognito - AI-Powered Legal Research Platform v5.0
            </Typography>
            <Typography variant="body2">
              Powered by Simple RAG Architecture • 3-Step Process: Search → Analyze → Generate • 
              TinyLlama (Utility) + Mistral-7B (Generation) • BGE Embeddings • FAISS Vector Search • 
              Clear Model Separation • Document-Based Responses • Local-First AI
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 