import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  PictureAsPdf as PdfIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useUploadDocuments, useTaskStatus } from '../api/rag';

interface UploadZoneProps {
  onUploadComplete?: (taskId: string) => void;
  onError?: (error: string) => void;
}

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

const UploadZone: React.FC<UploadZoneProps> = ({ onUploadComplete, onError }) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  const uploadMutation = useUploadDocuments();
  const { data: taskStatus } = useTaskStatus(currentTaskId);

  const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const newFiles: UploadFile[] = Array.from(selectedFiles).map(file => ({
      file,
      id: `${file.name}-${Date.now()}`,
      status: 'pending'
    }));

    // Filter for PDF files only
    const pdfFiles = newFiles.filter(f => f.file.type === 'application/pdf');
    const nonPdfFiles = newFiles.filter(f => f.file.type !== 'application/pdf');

    if (nonPdfFiles.length > 0) {
      if (onError) {
        onError(`${nonPdfFiles.length} non-PDF files were ignored. Only PDF files are supported.`);
      }
    }

    setFiles(prev => [...prev, ...pdfFiles]);
  }, [onError]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
    // Reset input
    e.target.value = '';
  }, [handleFileSelect]);

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    try {
      // Mark files as uploading
      setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' as const })));

      // Create FormData with files
      const formData = new FormData();
      files.forEach((uploadFile) => {
        formData.append('file', uploadFile.file);
      });

      const result = await uploadMutation.mutateAsync(formData);
      
      // Mark files as success
      setFiles(prev => prev.map(f => ({ ...f, status: 'success' as const })));
      setCurrentTaskId(result.task_id || result.doc_id);
      
      if (onUploadComplete) {
        onUploadComplete(result.task_id || result.doc_id);
      }
      
    } catch (error) {
      // Mark files as error
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'error' as const,
        error: error instanceof Error ? error.message : 'Upload failed'
      })));
      
      if (onError) {
        onError(error instanceof Error ? error.message : 'Upload failed');
      }
    }
  };

  const clearFiles = () => {
    setFiles([]);
    setCurrentTaskId(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <SuccessIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'uploading': return <LinearProgress />;
      default: return <PdfIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'uploading': return 'primary';
      default: return 'default';
    }
  };

  return (
    <Box>
      {/* Upload Area */}
      <Paper
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: dragOver ? 'primary.main' : 'grey.300',
          backgroundColor: dragOver ? 'primary.light' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'grey.50'
          }
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={handleFileInput}
        />
        
        <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        
        <Typography variant="h6" gutterBottom>
          Upload Legal Documents
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Drag and drop PDF files here, or click to select files
        </Typography>
        
        <Button variant="outlined" startIcon={<UploadIcon />}>
          Choose Files
        </Button>
        
        <Typography variant="caption" display="block" sx={{ mt: 1 }} color="text.secondary">
          Only PDF files are supported. Multiple files can be uploaded at once.
        </Typography>
      </Paper>

      {/* File List */}
      {files.length > 0 && (
        <Paper sx={{ mt: 2 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Selected Files ({files.length})
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={files.length === 0 || uploadMutation.isPending}
                startIcon={<UploadIcon />}
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload All'}
              </Button>
              <Button
                variant="outlined"
                onClick={clearFiles}
                disabled={uploadMutation.isPending}
                startIcon={<DeleteIcon />}
              >
                Clear All
              </Button>
            </Box>
          </Box>
          
          <List>
            {files.map((uploadFile) => (
              <ListItem
                key={uploadFile.id}
                secondaryAction={
                  <IconButton
                    edge="end"
                    onClick={() => removeFile(uploadFile.id)}
                    disabled={uploadMutation.isPending}
                  >
                    <DeleteIcon />
                  </IconButton>
                }
              >
                <ListItemIcon>
                  {getStatusIcon(uploadFile.status)}
                </ListItemIcon>
                <ListItemText
                  primary={uploadFile.file.name}
                  secondary={`${formatFileSize(uploadFile.file.size)} • ${uploadFile.file.type}`}
                />
                <Chip
                  label={uploadFile.status}
                  color={getStatusColor(uploadFile.status) as any}
                  size="small"
                  variant="outlined"
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Task Status */}
      {taskStatus && (
        <Alert
          severity={
            taskStatus.status === 'completed' ? 'success' :
            taskStatus.status === 'failed' ? 'error' : 'info'
          }
          sx={{ mt: 2 }}
        >
          <Typography variant="subtitle2">
            Processing Status: {taskStatus.status.toUpperCase()}
          </Typography>
          <Typography variant="body2">
            {taskStatus.status === 'processing' && (
              <>
                Progress: {taskStatus.progress}%
                <LinearProgress variant="determinate" value={taskStatus.progress} sx={{ mt: 1 }} />
              </>
            )}
            {taskStatus.status === 'completed' && taskStatus.results && (
              <>
                Successfully processed {taskStatus.results.documents_processed} documents.
                Built indices: {Object.entries(taskStatus.results.indices_built || {}).map(([key, value]) => 
                  `${key}: ${value}`
                ).join(', ')}
              </>
            )}
            {taskStatus.status === 'failed' && (
              <>Error: {taskStatus.error}</>
            )}
          </Typography>
        </Alert>
      )}

      {/* Upload Error */}
      {uploadMutation.error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Upload failed: {uploadMutation.error.message}
        </Alert>
      )}
    </Box>
  );
};

export default UploadZone;