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
  Analytics as AnalyticsIcon
} from '@mui/icons-material';

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

  React.useEffect(() => {
    fetchDashboardData();
    // Set placeholder data until real system monitoring is implemented
    setSystemStats({
      gpu: { usage: 0, memory: 'N/A' },
      ram: { usage: 0, memory: 'N/A' },
      cpu: { usage: 0, cores: 0 },
      storage: { usage: 0, space: 'N/A' }
    });
    setServices([]);
    setRecentActivity([]);
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
              ⚖️ LexCognito - AI-Powered Legal Research Platform
            </Typography>
            <Typography variant="body2">
              Powered by Legion 5 Pro • 8GB VRAM • 64GB RAM • CUDA Enabled • Local-First AI • 
              Advanced RAG Pipeline • Companies House Integration • Native Gemini CLI
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 