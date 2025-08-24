import { createTheme } from '@mui/material/styles';

/**
 * Modern dark theme for the LexCognito interface.
 * Provides a sleek palette, subtle rounding and removes default paper images.
 */
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#7e57c2', // Soft purple accent
    },
    secondary: {
      main: '#26c6da', // Teal accent
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 600 },
    h5: { fontWeight: 500 },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

export default theme;
