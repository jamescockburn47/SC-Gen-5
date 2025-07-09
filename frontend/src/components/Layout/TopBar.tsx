import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Chip,
  Badge
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
  Memory as MemoryIcon,
  Computer as ComputerIcon
} from '@mui/icons-material';
import axios from 'axios';

interface TopBarProps {
  drawerWidth: number;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

interface SystemStats {
  cpu: { usage: number; cores: number };
  ram: { usage: number; memory: string };
  gpu: { usage: number; memory: string };
}

const TopBar: React.FC<TopBarProps> = ({ drawerWidth, sidebarOpen, toggleSidebar }) => {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [notificationCount] = useState(0); // TODO: Implement real notification system
  
  useEffect(() => {
    fetchSystemStats();
    // Update system stats every 30 seconds
    const interval = setInterval(fetchSystemStats, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const fetchSystemStats = async () => {
    try {
      const response = await axios.get('/api/system/stats');
      setSystemStats(response.data);
    } catch (error) {
      console.error('Failed to fetch system stats:', error);
    }
  };
  
  const getSystemStatus = () => {
    if (!systemStats) return { label: 'System Loading...', color: 'default' as const };
    
    const highUsage = systemStats.cpu.usage > 80 || systemStats.ram.usage > 85;
    if (highUsage) {
      return { label: 'System Busy', color: 'warning' as const };
    }
    return { label: 'System Ready', color: 'success' as const };
  };
  
  const getGpuStatus = () => {
    if (!systemStats || systemStats.gpu.usage === 0) {
      return { label: 'GPU Idle', color: 'default' as const };
    }
    return { label: 'GPU Active', color: 'success' as const };
  };
  return (
    <AppBar
      position="fixed"
      sx={{
        width: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%',
        ml: sidebarOpen ? `${drawerWidth}px` : 0,
        transition: theme => theme.transitions.create(['margin', 'width'], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }),
        bgcolor: 'white',
        color: 'primary.main',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="toggle sidebar"
          onClick={toggleSidebar}
          edge="start"
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, color: 'primary.main' }}>
          LexCognito
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* System Status Indicators */}
          {systemStats && (
            <>
              <Chip
                icon={<ComputerIcon />}
                label={getSystemStatus().label}
                color={getSystemStatus().color}
                variant="outlined"
                size="small"
                title={`CPU: ${systemStats.cpu.usage}% | RAM: ${systemStats.ram.usage}%`}
              />
              
              <Chip
                icon={<MemoryIcon />}
                label={getGpuStatus().label}
                color={getGpuStatus().color}
                variant="outlined"
                size="small"
                title={systemStats.gpu.memory}
              />
            </>
          )}

          <IconButton color="inherit">
            <Badge badgeContent={notificationCount > 0 ? notificationCount : null} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          <IconButton color="inherit">
            <AccountCircle />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar; 