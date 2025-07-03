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

const Dashboard: React.FC = () => {
  const systemStats = {
    gpu: { usage: 34, memory: '3.2GB / 8GB' },
    ram: { usage: 67, memory: '43GB / 64GB' },
    cpu: { usage: 23, cores: 16 },
    storage: { usage: 45, space: '890GB / 2TB' }
  };

  const services = [
    { name: 'Mixtral Local LLM', status: 'running', port: 11434 },
    { name: 'Consult API', status: 'running', port: 8000 },
    { name: 'Companies House API', status: 'running', port: 8001 },
    { name: 'Vector Database', status: 'running', port: null },
    { name: 'Gemini CLI', status: 'ready', port: null }
  ];

  const recentActivity = [
    { action: 'Document processed', file: 'A1.5.pdf', time: '2 min ago' },
    { action: 'Legal query answered', query: 'Contract analysis...', time: '5 min ago' },
    { action: 'Company lookup', company: 'Microsoft Corporation', time: '12 min ago' },
    { action: 'Gemini analysis', task: 'Code review', time: '18 min ago' }
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <DashboardIcon sx={{ fontSize: 40 }} />
        Strategic Counsel Gen 5 Dashboard
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
                        value={systemStats.gpu.usage} 
                        sx={{ flexGrow: 1 }}
                        color="success"
                      />
                      <Typography variant="body2">{systemStats.gpu.usage}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats.gpu.memory}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">RAM Usage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats.ram.usage} 
                        sx={{ flexGrow: 1 }}
                        color="primary"
                      />
                      <Typography variant="body2">{systemStats.ram.usage}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats.ram.memory}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">CPU Usage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats.cpu.usage} 
                        sx={{ flexGrow: 1 }}
                        color="secondary"
                      />
                      <Typography variant="body2">{systemStats.cpu.usage}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats.cpu.cores} cores</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">Storage</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={systemStats.storage.usage} 
                        sx={{ flexGrow: 1 }}
                        color="info"
                      />
                      <Typography variant="body2">{systemStats.storage.usage}%</Typography>
                    </Box>
                    <Typography variant="caption">{systemStats.storage.space}</Typography>
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
                  <Typography variant="h4">1,247</Typography>
                  <Typography variant="body2" color="textSecondary">Documents</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <BusinessIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="h4">89</Typography>
                  <Typography variant="body2" color="textSecondary">Companies</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <AnalyticsIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4">456</Typography>
                  <Typography variant="body2" color="textSecondary">Queries</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <SpeedIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography variant="h4">2.3s</Typography>
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
                {services.map((service, index) => (
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
                ))}
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
                {recentActivity.map((activity, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={activity.action}
                      secondary={`${activity.file || activity.query || activity.company || activity.task} • ${activity.time}`}
                    />
                  </ListItem>
                ))}
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
              🏛️ Strategic Counsel Gen 5 Legal Research Assistant
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