import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { io, Socket } from 'socket.io-client';
import {
  Paper,
  Box,
  Typography,
  Button,
  ButtonGroup,
  Chip,
  Alert,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Terminal as TerminalIcon,
  Refresh as RefreshIcon,
  Clear as ClearIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import '@xterm/xterm/css/xterm.css';

const TerminalPage: React.FC = () => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminal = useRef<Terminal | null>(null);
  const fitAddon = useRef<FitAddon | null>(null);
  const socket = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isGeminiRunning, setIsGeminiRunning] = useState(false);

  useEffect(() => {
    if (terminalRef.current && !terminal.current) {
      // Initialize terminal
      terminal.current = new Terminal({
        fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
        fontSize: 14,
        fontWeight: 400,
        lineHeight: 1.2,
        letterSpacing: 0,
        theme: {
          background: '#1a1a1a',
          foreground: '#ffffff',
          cursor: '#00ff00',
          black: '#000000',
          red: '#ff6b6b',
          green: '#51cf66',
          yellow: '#ffd43b',
          blue: '#74c0fc',
          magenta: '#f783ac',
          cyan: '#3bc9db',
          white: '#ffffff',
          brightBlack: '#495057',
          brightRed: '#ff8787',
          brightGreen: '#69db7c',
          brightYellow: '#ffe066',
          brightBlue: '#91a7ff',
          brightMagenta: '#f06292',
          brightCyan: '#66d9ef',
          brightWhite: '#f8f9fa'
        },
        cursorBlink: true,
        cursorStyle: 'block',
        scrollback: 10000,
        rows: 30,
        cols: 120
      });

      fitAddon.current = new FitAddon();
      const webLinksAddon = new WebLinksAddon();
      terminal.current.loadAddon(fitAddon.current);
      terminal.current.loadAddon(webLinksAddon);
      terminal.current.open(terminalRef.current);

      // Only fit if the container has dimensions
      const fitTerminal = () => {
        if (
          terminalRef.current &&
          terminalRef.current.offsetWidth > 0 &&
          terminalRef.current.offsetHeight > 0
        ) {
          fitAddon.current && fitAddon.current.fit();
        } else {
          // Retry after a short delay
          setTimeout(fitTerminal, 500);
        }
      };
      fitTerminal();

      // Welcome message
      terminal.current.writeln('\x1b[1;32m🏛️  Strategic Counsel Gen 5 - Native Terminal Interface\x1b[0m');
      terminal.current.writeln('\x1b[1;34m⚖️  Advanced Legal Research Assistant Terminal\x1b[0m');
      terminal.current.writeln('');
      terminal.current.writeln('\x1b[1;33m🚀 Ready to connect to Google Gemini CLI...\x1b[0m');
      terminal.current.writeln('');

      // Handle terminal input
      terminal.current.onData((data) => {
        if (socket.current && isConnected) {
          socket.current.emit('terminal-input', data);
        }
      });

      // Connect to WebSocket server
      connectToServer();

      // Handle window resize
      const handleResize = () => {
        if (fitAddon.current) {
          fitAddon.current.fit();
        }
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        if (socket.current) {
          socket.current.disconnect();
        }
        if (terminal.current) {
          terminal.current.dispose();
        }
      };
    }
  }, []);

  const connectToServer = () => {
    // Connect to our WebSocket server that will proxy to Gemini CLI
    socket.current = io('ws://localhost:3001');

    socket.current.on('connect', () => {
      setIsConnected(true);
      terminal.current?.writeln('\x1b[1;32m✅ Connected to Terminal Server\x1b[0m');
      terminal.current?.writeln('');
    });

    socket.current.on('disconnect', () => {
      setIsConnected(false);
      terminal.current?.writeln('\x1b[1;31m❌ Disconnected from Terminal Server\x1b[0m');
    });

    socket.current.on('terminal-output', (data: string) => {
      terminal.current?.write(data);
    });

    socket.current.on('gemini-status', (status: { running: boolean }) => {
      setIsGeminiRunning(status.running);
    });
  };

  const startGeminiCLI = () => {
    if (socket.current && isConnected) {
      socket.current.emit('start-gemini');
      terminal.current?.writeln('\x1b[1;33m🤖 Starting Google Gemini CLI...\x1b[0m');
    }
  };

  const stopGeminiCLI = () => {
    if (socket.current && isConnected) {
      socket.current.emit('stop-gemini');
      terminal.current?.writeln('\x1b[1;31m🛑 Stopping Gemini CLI...\x1b[0m');
    }
  };

  const clearTerminal = () => {
    terminal.current?.clear();
  };

  const quickCommands = [
    {
      label: 'Analyze Codebase',
      command: 'Analyze this Strategic Counsel codebase architecture and suggest improvements'
    },
    {
      label: 'Generate README',
      command: 'Generate a comprehensive README.md for this legal research system'
    },
    {
      label: 'Review Security',
      command: 'Review the security practices in this legal research application'
    },
    {
      label: 'Legal AI Review',
      command: 'Review this legal AI system for compliance and best practices'
    }
  ];

  const sendQuickCommand = (command: string) => {
    if (socket.current && isConnected && terminal.current) {
      // Type the command in the terminal
      terminal.current.write(command);
      // Send enter
      socket.current.emit('terminal-input', '\r');
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <TerminalIcon sx={{ fontSize: 40 }} />
        Native Gemini CLI Terminal
      </Typography>

      <Grid container spacing={3}>
        {/* Terminal Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Terminal Controls</Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip 
                    label={isConnected ? 'Connected' : 'Disconnected'} 
                    color={isConnected ? 'success' : 'error'}
                    size="small"
                  />
                  <Chip 
                    label={isGeminiRunning ? 'Gemini Running' : 'Gemini Stopped'} 
                    color={isGeminiRunning ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>

              <ButtonGroup variant="outlined" size="small">
                <Button
                  startIcon={<PlayIcon />}
                  onClick={startGeminiCLI}
                  disabled={!isConnected || isGeminiRunning}
                >
                  Start Gemini CLI
                </Button>
                <Button
                  startIcon={<StopIcon />}
                  onClick={stopGeminiCLI}
                  disabled={!isConnected || !isGeminiRunning}
                  color="error"
                >
                  Stop Gemini
                </Button>
                <Button
                  startIcon={<ClearIcon />}
                  onClick={clearTerminal}
                >
                  Clear
                </Button>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={connectToServer}
                  disabled={isConnected}
                >
                  Reconnect
                </Button>
              </ButtonGroup>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Commands */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Quick Commands</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {quickCommands.map((cmd, index) => (
                  <Button
                    key={index}
                    variant="outlined"
                    size="small"
                    onClick={() => sendQuickCommand(cmd.command)}
                    disabled={!isConnected || !isGeminiRunning}
                  >
                    {cmd.label}
                  </Button>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Terminal */}
        <Grid item xs={12}>
          <Paper 
            elevation={3}
            sx={{ 
              p: 2,
              bgcolor: '#1a1a1a',
              borderRadius: 2,
              border: '1px solid #333'
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2" sx={{ color: '#fff', fontFamily: 'monospace' }}>
                🤖 Google Gemini CLI - Native Interface
              </Typography>
              <Box>
                <Tooltip title="Terminal Settings">
                  <IconButton size="small" sx={{ color: '#fff' }}>
                    <SettingsIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            
            <Box
              ref={terminalRef}
              sx={{
                height: '500px',
                width: '100%',
                '& .xterm': {
                  height: '100%'
                },
                '& .xterm .xterm-viewport': {
                  backgroundColor: 'transparent'
                }
              }}
            />
          </Paper>
        </Grid>

        {/* Help */}
        <Grid item xs={12}>
          <Alert severity="info">
            <Typography variant="subtitle2" gutterBottom>
              🎯 Native Terminal Features:
            </Typography>
            <Typography variant="body2">
              • <strong>Real Terminal Emulation:</strong> Full xterm.js terminal with native key bindings<br/>
              • <strong>Live Gemini CLI:</strong> Direct connection to Google's official CLI tool<br/>
              • <strong>Interactive Chat:</strong> True back-and-forth conversation with Gemini<br/>
              • <strong>Repository Context:</strong> Gemini has full awareness of your Strategic Counsel codebase<br/>
              • <strong>Native Features:</strong> Copy/paste, scrollback, keyboard shortcuts, and more
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TerminalPage; 