import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider,
  Chip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Chat as ChatIcon,
  Cloud as CloudIcon,
  Description as DocumentIcon,
  Business as BusinessIcon,
  MenuBook as CitationIcon,
  Analytics as AnalyticsIcon,
  Gavel as GavelIcon,
  Code as CodeIcon,
  BugReport as BugReportIcon
} from '@mui/icons-material';

interface SidebarProps {
  drawerWidth: number;
  open: boolean;
  onToggle: () => void;
}

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Legal Research', icon: <ChatIcon />, path: '/research' },
  { text: 'Cloud Consultation', icon: <CloudIcon />, path: '/cloud-consultation' },
  { text: 'Document Manager', icon: <DocumentIcon />, path: '/documents' },
  { text: 'Companies House', icon: <BusinessIcon />, path: '/companies-house' },
  { text: 'Claude Code CLI', icon: <CodeIcon />, path: '/claude-cli' },
  { text: 'Legal Citation', icon: <CitationIcon />, path: '/legal-citation' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Diagnostics', icon: <BugReportIcon />, path: '/diagnostics' }
];

const Sidebar: React.FC<SidebarProps> = ({ drawerWidth, open }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          bgcolor: 'primary.main',
          color: 'white'
        },
      }}
      variant="persistent"
      anchor="left"
      open={open}
    >
      {/* Header */}
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <GavelIcon sx={{ fontSize: 48, mb: 1, color: 'secondary.main' }} />
        <Typography variant="h5" sx={{ color: 'white', fontWeight: 600 }}>
          LexCognito
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 2 }}>
          AI-Powered Legal Research Platform
        </Typography>
        <Chip 
          label="v5.0.0" 
          size="small" 
          sx={{ 
            bgcolor: 'secondary.main',
            color: 'primary.main',
            fontWeight: 600
          }} 
        />
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.2)' }} />

      {/* Navigation */}
      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                mx: 1,
                color: 'white',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.1)'
                },
                ...(location.pathname === item.path && {
                  bgcolor: 'secondary.main',
                  color: 'primary.main',
                  '&:hover': {
                    bgcolor: 'secondary.light'
                  }
                })
              }}
            >
              <ListItemIcon 
                sx={{ 
                  color: location.pathname === item.path ? 'primary.main' : 'white',
                  minWidth: 40
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.9rem',
                  fontWeight: location.pathname === item.path ? 600 : 400
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Box sx={{ flexGrow: 1 }} />

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,0.2)' }}>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
          Powered by Legion 5 Pro
        </Typography>
        <br />
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
          8GB VRAM • 64GB RAM • CUDA
        </Typography>
      </Box>
    </Drawer>
  );
};

export default Sidebar; 