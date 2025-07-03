import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import Sidebar from './components/Layout/Sidebar';
import TopBar from './components/Layout/TopBar';
import Dashboard from './pages/Dashboard';
import ConsultationPage from './pages/ConsultationPage';
import DocumentsPage from './pages/DocumentsPage';
import CompaniesHousePage from './pages/CompaniesHousePage';
import TerminalPage from './pages/TerminalPage';
import AnalyticsPage from './pages/AnalyticsPage';

// Strategic Counsel theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1f4e79', // Legal blue
      dark: '#0d2a47',
      light: '#4a73a8'
    },
    secondary: {
      main: '#c8a882', // Legal gold
      dark: '#8b7355',
      light: '#e6c5a3'
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff'
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      color: '#1f4e79'
    },
    h5: {
      fontWeight: 500,
      color: '#1f4e79'
    }
  },
  components: {
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1f4e79',
          color: 'white'
        }
      }
    }
  }
});

const drawerWidth = 280;

function App() {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <TopBar 
            drawerWidth={drawerWidth} 
            sidebarOpen={sidebarOpen}
            toggleSidebar={toggleSidebar}
          />
          <Sidebar 
            drawerWidth={drawerWidth} 
            open={sidebarOpen}
            onToggle={toggleSidebar}
          />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              bgcolor: 'background.default',
              ml: sidebarOpen ? `${drawerWidth}px` : 0,
              mt: '64px', // AppBar height
              transition: theme => theme.transitions.create(['margin'], {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.leavingScreen,
              }),
              p: 3
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/consultation" element={<ConsultationPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/companies-house" element={<CompaniesHousePage />} />
              <Route path="/terminal" element={<TerminalPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
