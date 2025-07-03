const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const pty = require('node-pty');
const path = require('path');
const cors = require('cors');

const app = express();
const server = http.createServer(app);

// Enable CORS for all routes
app.use(cors({
  origin: ["http://localhost:3000", "http://localhost:3001"],
  credentials: true
}));

const io = socketIo(server, {
  cors: {
    origin: ["http://localhost:3000", "http://localhost:3001"],
    methods: ["GET", "POST"],
    credentials: true
  }
});

const PORT = 3001;

// Store active terminal sessions
const terminals = {};
let geminiProcess = null;

console.log('🏛️  Strategic Counsel Gen 5 - Terminal Server Starting...');
console.log('⚖️  Native Gemini CLI Bridge Server');

// Handle WebSocket connections
io.on('connection', (socket) => {
  console.log(`✅ Client connected: ${socket.id}`);

  // Create a new terminal session for this client
  const shell = process.platform === 'win32' ? 'cmd.exe' : 'bash';
  const terminal = pty.spawn(shell, [], {
    name: 'xterm-color',
    cols: 120,
    rows: 30,
    cwd: path.join(__dirname, '..'), // Set to SC Gen 5 root directory
    env: {
      ...process.env,
      TERM: 'xterm-256color',
      COLORTERM: 'truecolor'
    }
  });

  terminals[socket.id] = terminal;

  // Send welcome message
  setTimeout(() => {
    terminal.write('echo "🏛️  Strategic Counsel Gen 5 Terminal Bridge"\r');
    terminal.write('echo "⚖️  Ready for Gemini CLI integration"\r');
    terminal.write('echo ""\r');
    terminal.write('pwd\r');
  }, 500);

  // Handle terminal output
  terminal.onData((data) => {
    socket.emit('terminal-output', data);
  });

  // Handle terminal exit
  terminal.onExit(() => {
    delete terminals[socket.id];
    socket.emit('terminal-output', '\r\n*** Terminal session ended ***\r\n');
  });

  // Handle input from client
  socket.on('terminal-input', (data) => {
    if (terminals[socket.id]) {
      terminals[socket.id].write(data);
    }
  });

  // Handle Gemini CLI start
  socket.on('start-gemini', () => {
    console.log('🤖 Starting Gemini CLI for client:', socket.id);
    
    if (terminals[socket.id]) {
      // Send command to start Gemini CLI
      const geminiCommand = 'npx --yes https://github.com/google-gemini/gemini-cli\r';
      terminals[socket.id].write(geminiCommand);
      
      // Update status
      socket.emit('gemini-status', { running: true });
      
      // Send notification
      socket.emit('terminal-output', '\r\n🤖 Starting Google Gemini CLI...\r\n');
    }
  });

  // Handle Gemini CLI stop
  socket.on('stop-gemini', () => {
    console.log('🛑 Stopping Gemini CLI for client:', socket.id);
    
    if (terminals[socket.id]) {
      // Send Ctrl+C to interrupt
      terminals[socket.id].write('\x03');
      
      // Update status
      socket.emit('gemini-status', { running: false });
      
      // Send notification
      socket.emit('terminal-output', '\r\n🛑 Stopping Gemini CLI...\r\n');
    }
  });

  // Handle client disconnect
  socket.on('disconnect', () => {
    console.log(`❌ Client disconnected: ${socket.id}`);
    
    // Clean up terminal
    if (terminals[socket.id]) {
      terminals[socket.id].kill();
      delete terminals[socket.id];
    }
  });

  // Send initial status
  socket.emit('gemini-status', { running: false });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    server: 'Strategic Counsel Gen 5 Terminal Server',
    connections: Object.keys(terminals).length,
    uptime: process.uptime()
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`\n🚀 Terminal Server running on port ${PORT}`);
  console.log(`📡 WebSocket endpoint: ws://localhost:${PORT}`);
  console.log(`🔗 Health check: http://localhost:${PORT}/health`);
  console.log(`\n✨ Features Enabled:`);
  console.log(`   • Real terminal emulation via node-pty`);
  console.log(`   • Native Gemini CLI bridge`);
  console.log(`   • Interactive chat support`);
  console.log(`   • Full repository context`);
  console.log(`   • ANSI color support`);
  console.log(`\n🎯 Ready for React frontend connection!`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down Terminal Server...');
  
  // Close all terminals
  Object.keys(terminals).forEach(socketId => {
    terminals[socketId].kill();
  });
  
  server.close(() => {
    console.log('✅ Terminal Server stopped');
    process.exit(0);
  });
});

// Error handling
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
}); 