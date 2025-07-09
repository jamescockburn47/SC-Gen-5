import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Sidebar from './components/Layout/Sidebar';
import TopBar from './components/Layout/TopBar';
import Dashboard from './pages/Dashboard';
import DocumentsPage from './pages/DocumentsPage';
import CompaniesHousePage from './pages/CompaniesHousePage';
import LegalCitationPage from './pages/LegalCitationPage';
import Research from './pages/Research';
import CloudConsultation from './pages/CloudConsultation';
import AnalyticsPage from './pages/AnalyticsPage';
import ClaudeCliNativePage from './pages/ClaudeCliNativePage';
import DiagnosticsPage from './pages/DiagnosticsPage';

// LexCognito theme
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

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <QueryClientProvider client={queryClient}>
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
              <Route path="/research" element={<Research />} />
              <Route path="/cloud-consultation" element={<CloudConsultation />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/companies-house" element={<CompaniesHousePage />} />
              <Route path="/legal-citation" element={<LegalCitationPage />} />
              <Route path="/claude-cli" element={<ClaudeCliNativePage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/diagnostics" element={<DiagnosticsPage />} />
              {/* Redirect old consultation route to new research page */}
              <Route path="/consultation" element={<Research />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
