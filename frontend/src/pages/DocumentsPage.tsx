import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  Tabs,
  Tab
} from '@mui/material';
import {
  Description as DocumentIcon,
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  GetApp as ExtractIcon,
  TextSnippet as OcrIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

interface Document {
  id: string;
  filename: string;
  file_type: string;
  size: number;
  upload_date: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  pages: number;
  ocr_engine?: string;
  extraction_method?: string;
  text_preview?: string;
  metadata?: any;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`documents-tabpanel-${index}`}
      aria-labelledby={`documents-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [documentText, setDocumentText] = useState<string>('');

  // File upload with drag & drop
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']
    },
    onDrop: handleFileUpload
  });

  // Load documents on component mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/documents');
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  async function handleFileUpload(acceptedFiles: File[]) {
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('filename', file.name);
      
      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        
        const response = await axios.post('/api/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
            }
          },
        });
        
        // Add the new document to the list
        setDocuments(prev => [...prev, response.data.document]);
        
        // Clear upload progress
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
        
      } catch (error) {
        console.error('Upload failed:', error);
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
      }
    }
  }

  const handleDeleteDocument = async (docId: string) => {
    try {
      await axios.delete(`/api/documents/${docId}`);
      setDocuments(prev => prev.filter(doc => doc.id !== docId));
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const handleViewDocument = async (document: Document) => {
    setSelectedDocument(document);
    setViewDialogOpen(true);
    
    // Load document text
    try {
      const response = await axios.get(`/api/documents/${document.id}/text`);
      setDocumentText(response.data.text || 'No text content available');
    } catch (error) {
      setDocumentText('Failed to load document text');
    }
  };

  const handleDownloadDocument = async (docId: string, filename: string) => {
    try {
      const response = await axios.get(`/api/documents/${docId}/download`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleReprocessDocument = async (docId: string) => {
    try {
      await axios.post(`/api/documents/${docId}/reprocess`);
      loadDocuments(); // Refresh document list
    } catch (error) {
      console.error('Reprocessing failed:', error);
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || doc.processing_status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <DocumentIcon sx={{ fontSize: 40 }} />
        Document Manager
      </Typography>

      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Upload & Manage" />
        <Tab label="Search & Filter" />
        <Tab label="Processing Queue" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* Upload Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Documents
            </Typography>
            
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive ? 'action.hover' : 'background.paper',
                transition: 'all 0.2s ease'
              }}
            >
              <input {...getInputProps()} />
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop files here...' : 'Drag & drop files here or click to select'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supports PDF, PNG, JPG, JPEG, TIFF, BMP, GIF
              </Typography>
            </Box>

            {/* Upload Progress */}
            {Object.entries(uploadProgress).length > 0 && (
              <Box sx={{ mt: 2 }}>
                {Object.entries(uploadProgress).map(([filename, progress]) => (
                  <Box key={filename} sx={{ mb: 1 }}>
                    <Typography variant="body2">{filename}</Typography>
                    <LinearProgress variant="determinate" value={progress} />
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Documents List */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Document Library</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={loadDocuments}
                  disabled={loading}
                >
                  Refresh
                </Button>
              </Box>
            </Box>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Filename</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Pages</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Upload Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                          <LinearProgress sx={{ width: '100%' }} />
                        </Box>
                      </TableCell>
                    </TableRow>
                  ) : filteredDocuments.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <Typography variant="body2" color="text.secondary">
                          No documents found
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredDocuments.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell>{doc.filename}</TableCell>
                        <TableCell>
                          <Chip label={doc.file_type.toUpperCase()} size="small" />
                        </TableCell>
                        <TableCell>{formatFileSize(doc.size)}</TableCell>
                        <TableCell>{doc.pages || '-'}</TableCell>
                        <TableCell>
                          <Chip
                            label={doc.processing_status}
                            color={getStatusColor(doc.processing_status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(doc.upload_date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="View Document">
                              <IconButton
                                size="small"
                                onClick={() => handleViewDocument(doc)}
                                disabled={doc.processing_status !== 'completed'}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Download">
                              <IconButton
                                size="small"
                                onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                              >
                                <DownloadIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reprocess">
                              <IconButton
                                size="small"
                                onClick={() => handleReprocessDocument(doc.id)}
                                disabled={doc.processing_status === 'processing'}
                              >
                                <ExtractIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteDocument(doc.id)}
                                color="error"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Search and Filter */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search Documents"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              select
              label="Filter by Status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="processing">Processing</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </TextField>
          </Grid>
        </Grid>

        {/* Filtered Results */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Search Results ({filteredDocuments.length})
          </Typography>
          <Grid container spacing={2}>
            {filteredDocuments.map((doc) => (
              <Grid item xs={12} sm={6} md={4} key={doc.id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" noWrap>
                      {doc.filename}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatFileSize(doc.size)} • {doc.pages} pages
                    </Typography>
                    <Chip
                      label={doc.processing_status}
                      color={getStatusColor(doc.processing_status) as any}
                      size="small"
                      sx={{ mt: 1 }}
                    />
                    {doc.text_preview && (
                      <Typography variant="body2" sx={{ mt: 1 }} noWrap>
                        {doc.text_preview.substring(0, 100)}...
                      </Typography>
                    )}
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        startIcon={<ViewIcon />}
                        onClick={() => handleViewDocument(doc)}
                        disabled={doc.processing_status !== 'completed'}
                      >
                        View
                      </Button>
                      <Button
                        size="small"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                      >
                        Download
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Processing Queue */}
        <Alert severity="info" sx={{ mb: 2 }}>
          Monitor document processing status and OCR extraction progress
        </Alert>

        <Grid container spacing={3}>
          {documents
            .filter(doc => doc.processing_status === 'processing' || doc.processing_status === 'pending')
            .map((doc) => (
              <Grid item xs={12} key={doc.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="h6">{doc.filename}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {doc.file_type.toUpperCase()} • {formatFileSize(doc.size)}
                          {doc.pages && ` • ${doc.pages} pages`}
                        </Typography>
                        {doc.ocr_engine && (
                          <Typography variant="body2" color="text.secondary">
                            OCR Engine: {doc.ocr_engine}
                          </Typography>
                        )}
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Chip
                          label={doc.processing_status}
                          color={getStatusColor(doc.processing_status) as any}
                        />
                        <Box sx={{ mt: 1 }}>
                          <Button
                            size="small"
                            startIcon={<RefreshIcon />}
                            onClick={() => loadDocuments()}
                          >
                            Refresh
                          </Button>
                        </Box>
                      </Box>
                    </Box>
                    {doc.processing_status === 'processing' && (
                      <LinearProgress sx={{ mt: 2 }} />
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
        </Grid>
      </TabPanel>

      {/* Document Viewer Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {selectedDocument?.filename}
            </Typography>
            <Box>
              {selectedDocument?.ocr_engine && (
                <Chip
                  icon={<OcrIcon />}
                  label={`OCR: ${selectedDocument.ocr_engine}`}
                  size="small"
                  sx={{ mr: 1 }}
                />
              )}
              {selectedDocument?.extraction_method && (
                <Chip
                  label={selectedDocument.extraction_method}
                  size="small"
                />
              )}
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {selectedDocument && `${selectedDocument.pages} pages • ${formatFileSize(selectedDocument.size)} • Uploaded ${new Date(selectedDocument.upload_date).toLocaleDateString()}`}
            </Typography>
          </Box>
          
          <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
              {documentText}
            </Typography>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          {selectedDocument && (
            <Button
              startIcon={<DownloadIcon />}
              onClick={() => {
                handleDownloadDocument(selectedDocument.id, selectedDocument.filename);
                setViewDialogOpen(false);
              }}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentsPage;