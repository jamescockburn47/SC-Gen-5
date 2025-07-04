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
  Tab,
  Snackbar
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
  TextSnippet as OcrIcon,
  Refresh as ReprocessIcon,
  CheckCircle as QualityIcon,
  Pages as PagesIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

interface Document {
  doc_id: string;
  filename: string;
  file_type?: string;
  file_size: number;
  created_at: string;
  processing_status?: 'pending' | 'processing' | 'completed' | 'failed';
  pages?: number;
  extraction_method?: string;
  quality_score?: number;
  text_length?: number;
  num_chunks?: number;
  ocr_engine?: string;
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
  const [reprocessingDoc, setReprocessingDoc] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info'
  });

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
      setSnackbar({
        open: true,
        message: 'Failed to load documents',
        severity: 'error'
      });
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
        setDocuments(prev => [...prev, response.data]);
        
        // Clear upload progress
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
        
        setSnackbar({
          open: true,
          message: `Successfully uploaded ${file.name}`,
          severity: 'success'
        });
        
      } catch (error) {
        console.error('Upload failed:', error);
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
        setSnackbar({
          open: true,
          message: `Failed to upload ${file.name}`,
          severity: 'error'
        });
      }
    }
  }

  const handleDeleteDocument = async (docId: string) => {
    try {
      await axios.delete(`/api/documents/${docId}`);
      setDocuments(prev => prev.filter(doc => doc.doc_id !== docId));
      setSnackbar({
        open: true,
        message: 'Document deleted successfully',
        severity: 'success'
      });
    } catch (error) {
      console.error('Failed to delete document:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete document',
        severity: 'error'
      });
    }
  };

  const handleViewDocument = async (document: Document) => {
    setSelectedDocument(document);
    setViewDialogOpen(true);
    
    // Load document text
    try {
      const response = await axios.get(`/api/documents/${document.doc_id}/text`);
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
      
      setSnackbar({
        open: true,
        message: 'Document downloaded successfully',
        severity: 'success'
      });
    } catch (error) {
      console.error('Download failed:', error);
      setSnackbar({
        open: true,
        message: 'Failed to download document',
        severity: 'error'
      });
    }
  };

  const handleReprocessDocument = async (docId: string) => {
    setReprocessingDoc(docId);
    try {
      const response = await axios.post(`/api/documents/${docId}/reprocess`);
      await loadDocuments(); // Refresh document list
      setSnackbar({
        open: true,
        message: 'Document reprocessed successfully',
        severity: 'success'
      });
    } catch (error) {
      console.error('Reprocessing failed:', error);
      setSnackbar({
        open: true,
        message: 'Failed to reprocess document',
        severity: 'error'
      });
    } finally {
      setReprocessingDoc(null);
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

  const getQualityColor = (score: number | undefined) => {
    if (score === undefined || score === null) return 'default';
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getExtractionMethodColor = (method: string | undefined) => {
    switch (method) {
      case 'direct': return 'success';
      case 'ocr': return 'warning';
      default: return 'default';
    }
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
                    <TableCell>Extraction Method</TableCell>
                    <TableCell>Quality Score</TableCell>
                    <TableCell>Pages</TableCell>
                    <TableCell>Size</TableCell>
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
                      <TableRow key={doc.doc_id}>
                        <TableCell>{doc.filename}</TableCell>
                        <TableCell>
                          <Chip 
                            label={doc.extraction_method || 'unknown'} 
                            color={getExtractionMethodColor(doc.extraction_method) as any}
                            size="small"
                            icon={doc.extraction_method === 'ocr' ? <OcrIcon /> : undefined}
                          />
                        </TableCell>
                        <TableCell>
                          {doc.quality_score !== undefined && doc.quality_score !== null ? (
                            <Chip
                              label={`${(doc.quality_score * 100).toFixed(0)}%`}
                              color={getQualityColor(doc.quality_score) as any}
                              size="small"
                              icon={<QualityIcon />}
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          {doc.pages ? (
                            <Chip
                              label={`${doc.pages} pages`}
                              size="small"
                              icon={<PagesIcon />}
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                        <TableCell>
                          {new Date(doc.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="View Document">
                              <IconButton
                                size="small"
                                onClick={() => handleViewDocument(doc)}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Download">
                              <IconButton
                                size="small"
                                onClick={() => handleDownloadDocument(doc.doc_id, doc.filename)}
                              >
                                <DownloadIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reprocess Document">
                              <IconButton
                                size="small"
                                onClick={() => handleReprocessDocument(doc.doc_id)}
                                disabled={reprocessingDoc === doc.doc_id}
                              >
                                <ReprocessIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteDocument(doc.doc_id)}
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
              <Grid item xs={12} sm={6} md={4} key={doc.doc_id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" noWrap>
                      {doc.filename}
                    </Typography>
                                          <Typography variant="body2" color="text.secondary">
                        {formatFileSize(doc.file_size)} • {doc.pages || 0} pages
                      </Typography>
                    <Chip
                      label={doc.processing_status || 'unknown'}
                      color={getStatusColor(doc.processing_status || 'unknown') as any}
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
                        onClick={() => handleDownloadDocument(doc.doc_id, doc.filename)}
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
              <Grid item xs={12} key={doc.doc_id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="h6">{doc.filename}</Typography>
                        <Typography variant="body2" color="text.secondary">
                                                     {doc.file_type?.toUpperCase() || 'UNKNOWN'} • {formatFileSize(doc.file_size)}
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
                          label={doc.processing_status || 'unknown'}
                          color={getStatusColor(doc.processing_status || 'unknown') as any}
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
            <Box sx={{ display: 'flex', gap: 1 }}>
              {selectedDocument?.extraction_method && (
                <Chip
                  label={selectedDocument.extraction_method}
                  color={getExtractionMethodColor(selectedDocument.extraction_method) as any}
                  size="small"
                  icon={selectedDocument.extraction_method === 'ocr' ? <OcrIcon /> : undefined}
                />
              )}
              {selectedDocument?.quality_score !== undefined && selectedDocument?.quality_score !== null && (
                <Chip
                  label={`Quality: ${(selectedDocument.quality_score * 100).toFixed(0)}%`}
                  color={getQualityColor(selectedDocument.quality_score) as any}
                  size="small"
                  icon={<QualityIcon />}
                />
              )}
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {selectedDocument && (
                <>
                  {selectedDocument.pages && `${selectedDocument.pages} pages • `}
                  {formatFileSize(selectedDocument.file_size)} • 
                  Uploaded {new Date(selectedDocument.created_at).toLocaleDateString()}
                  {selectedDocument.text_length && ` • ${selectedDocument.text_length.toLocaleString()} characters`}
                  {selectedDocument.num_chunks && ` • ${selectedDocument.num_chunks} chunks`}
                </>
              )}
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
            <>
              <Button
                startIcon={<ReprocessIcon />}
                onClick={() => {
                  handleReprocessDocument(selectedDocument.doc_id);
                  setViewDialogOpen(false);
                }}
                disabled={reprocessingDoc === selectedDocument.doc_id}
              >
                Reprocess
              </Button>
              <Button
                startIcon={<DownloadIcon />}
                onClick={() => {
                  handleDownloadDocument(selectedDocument.doc_id, selectedDocument.filename);
                  setViewDialogOpen(false);
                }}
              >
                Download
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default DocumentsPage;