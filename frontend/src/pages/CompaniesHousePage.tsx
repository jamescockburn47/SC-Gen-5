import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab
} from '@mui/material';
import {
  Business as BusinessIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  GetApp as BulkDownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Description as FilingIcon,
  LocationOn as AddressIcon,
  Person as OfficerIcon,
  AccountBalance as FinancialIcon,
  Timeline as HistoryIcon,
  ExpandMore as ExpandMoreIcon,
  CloudDownload as CloudDownloadIcon,
  Storage as StorageIcon
} from '@mui/icons-material';
import axios from 'axios';

interface Company {
  company_number: string;
  company_name: string;
  company_status: string;
  company_type: string;
  date_of_creation: string;
  registered_office_address: {
    address_line_1?: string;
    address_line_2?: string;
    locality?: string;
    postal_code?: string;
    country?: string;
  };
  sic_codes?: string[];
  jurisdiction?: string;
}

interface Filing {
  transaction_id: string;
  description: string;
  date: string;
  type: string;
  action_date?: string;
  category: string;
  subcategory?: string;
  paper_filed?: boolean;
  links?: {
    document_metadata?: string;
    self?: string;
  };
}

interface CompanyProfile {
  company: Company;
  officers?: Officer[];
  filings?: Filing[];
  charges?: any[];
  filing_history_status?: string;
}

interface Officer {
  name: string;
  officer_role: string;
  appointed_on?: string;
  resigned_on?: string;
  nationality?: string;
  occupation?: string;
  address?: {
    address_line_1?: string;
    locality?: string;
    postal_code?: string;
    country?: string;
  };
}

interface BulkJob {
  id: string;
  company_numbers: string[];
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  completed_at?: string;
  downloaded_count: number;
  total_count: number;
  error_message?: string;
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
      id={`companies-tabpanel-${index}`}
      aria-labelledby={`companies-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const CompaniesHousePage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<CompanyProfile | null>(null);
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const [bulkJobs, setBulkJobs] = useState<BulkJob[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [searchType, setSearchType] = useState<'company' | 'officer'>('company');
  const [bulkCompanyNumbers, setBulkCompanyNumbers] = useState('');
  const [apiStatus, setApiStatus] = useState<'checking' | 'available' | 'unavailable'>('checking');

  useEffect(() => {
    checkApiStatus();
    loadBulkJobs();
  }, []);

  const checkApiStatus = async () => {
    try {
      const response = await axios.get('/api/companies-house/status');
      setApiStatus(response.data.available ? 'available' : 'unavailable');
    } catch (error) {
      setApiStatus('unavailable');
    }
  };

  const loadBulkJobs = async () => {
    try {
      const response = await axios.get('/api/companies-house/bulk-jobs');
      setBulkJobs(response.data.jobs || []);
    } catch (error) {
      console.error('Failed to load bulk jobs:', error);
    }
  };

  const searchCompanies = async () => {
    if (!searchTerm.trim()) return;

    setLoading(true);
    try {
      const response = await axios.get('/api/companies-house/search', {
        params: {
          query: searchTerm,
          type: searchType
        }
      });
      setSearchResults(response.data.companies || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const loadCompanyProfile = async (companyNumber: string) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/companies-house/company/${companyNumber}`);
      setSelectedCompany(response.data);
      setProfileDialogOpen(true);
    } catch (error) {
      console.error('Failed to load company profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadFiling = async (companyNumber: string, transactionId: string) => {
    try {
      const response = await axios.get(
        `/api/companies-house/company/${companyNumber}/filing/${transactionId}/download`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${companyNumber}-${transactionId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const startBulkDownload = async () => {
    if (!bulkCompanyNumbers.trim()) return;

    const companyNumbers = bulkCompanyNumbers
      .split(/[,\n\r]+/)
      .map(num => num.trim())
      .filter(num => num.length > 0);

    if (companyNumbers.length === 0) return;

    try {
      const response = await axios.post('/api/companies-house/bulk-download', {
        company_numbers: companyNumbers
      });
      
      setBulkJobs(prev => [response.data.job, ...prev]);
      setBulkCompanyNumbers('');
      
      // Switch to bulk jobs tab
      setTabValue(2);
    } catch (error) {
      console.error('Failed to start bulk download:', error);
    }
  };

  const cancelBulkJob = async (jobId: string) => {
    try {
      await axios.post(`/api/companies-house/bulk-jobs/${jobId}/cancel`);
      loadBulkJobs(); // Refresh jobs
    } catch (error) {
      console.error('Failed to cancel bulk job:', error);
    }
  };

  const downloadBulkResults = async (jobId: string) => {
    try {
      const response = await axios.get(`/api/companies-house/bulk-jobs/${jobId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `bulk-download-${jobId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'dissolved': return 'error';
      case 'liquidation': return 'warning';
      case 'administration': return 'warning';
      default: return 'default';
    }
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <BusinessIcon sx={{ fontSize: 40 }} />
        Companies House Integration
      </Typography>

      {/* API Status Alert */}
      {apiStatus === 'unavailable' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Companies House API is currently unavailable. Please check your API key configuration.
        </Alert>
      )}

      {apiStatus === 'checking' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Checking Companies House API status...
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Company Search" />
        <Tab label="Bulk Operations" />
        <Tab label="Download Jobs" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* Company Search */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Search Companies
                </Typography>
                
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Search Type</InputLabel>
                      <Select
                        value={searchType}
                        onChange={(e) => setSearchType(e.target.value as any)}
                      >
                        <MenuItem value="company">Company Name</MenuItem>
                        <MenuItem value="officer">Officer Name</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Search term"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && searchCompanies()}
                      disabled={apiStatus !== 'available'}
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<SearchIcon />}
                      onClick={searchCompanies}
                      disabled={loading || apiStatus !== 'available'}
                    >
                      Search
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Search Results */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Search Results ({searchResults.length})
                </Typography>
                
                {loading ? (
                  <LinearProgress />
                ) : (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Company Name</TableCell>
                          <TableCell>Number</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Incorporated</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {searchResults.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={6} align="center">
                              <Typography variant="body2" color="text.secondary">
                                {searchTerm ? 'No companies found' : 'Enter a search term to find companies'}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ) : (
                          searchResults.map((company) => (
                            <TableRow key={company.company_number}>
                              <TableCell>
                                <Typography variant="subtitle2">
                                  {company.company_name}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip label={company.company_number} size="small" />
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={company.company_status}
                                  color={getStatusColor(company.company_status) as any}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>{company.company_type}</TableCell>
                              <TableCell>{formatDate(company.date_of_creation)}</TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                  <Tooltip title="View Profile">
                                    <IconButton
                                      size="small"
                                      onClick={() => loadCompanyProfile(company.company_number)}
                                    >
                                      <ViewIcon />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="Download Latest Filing">
                                    <IconButton size="small">
                                      <DownloadIcon />
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
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Bulk Operations */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Bulk Download Filings
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Enter company numbers (one per line or comma-separated) to download all their filings.
                </Typography>
                
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Company Numbers"
                  value={bulkCompanyNumbers}
                  onChange={(e) => setBulkCompanyNumbers(e.target.value)}
                  placeholder="12345678&#10;87654321&#10;11223344"
                  sx={{ mb: 2 }}
                />
                
                <Button
                  variant="contained"
                  startIcon={<BulkDownloadIcon />}
                  onClick={startBulkDownload}
                  disabled={!bulkCompanyNumbers.trim() || apiStatus !== 'available'}
                >
                  Start Bulk Download
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Bulk Processing Features
                </Typography>
                
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Automatic Filing Download"
                      secondary="Downloads all available filings for each company"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="OCR Processing"
                      secondary="Automatically extracts text from downloaded PDF filings"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Document Indexing"
                      secondary="Adds processed documents to the searchable index"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Progress Monitoring"
                      secondary="Real-time progress tracking for bulk operations"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Download Jobs */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Download Jobs
              </Typography>
              <Button startIcon={<RefreshIcon />} onClick={loadBulkJobs}>
                Refresh
              </Button>
            </Box>
            
            {bulkJobs.length === 0 ? (
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    No bulk download jobs found
                  </Typography>
                </CardContent>
              </Card>
            ) : (
              bulkJobs.map((job) => (
                <Card key={job.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                          <Typography variant="h6">
                            Bulk Job {job.id.substring(0, 8)}
                          </Typography>
                          <Chip
                            label={job.status}
                            color={getJobStatusColor(job.status) as any}
                            size="small"
                          />
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary">
                          {job.company_numbers.length} companies • Started {formatDate(job.created_at)}
                          {job.completed_at && ` • Completed ${formatDate(job.completed_at)}`}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Progress: {job.downloaded_count} / {job.total_count} files downloaded
                        </Typography>
                        
                        {job.status === 'running' && (
                          <LinearProgress
                            variant="determinate"
                            value={(job.downloaded_count / job.total_count) * 100}
                            sx={{ mt: 1 }}
                          />
                        )}
                        
                        {job.error_message && (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            {job.error_message}
                          </Alert>
                        )}
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {job.status === 'completed' && (
                          <Button
                            startIcon={<CloudDownloadIcon />}
                            onClick={() => downloadBulkResults(job.id)}
                          >
                            Download ZIP
                          </Button>
                        )}
                        {(job.status === 'pending' || job.status === 'running') && (
                          <Button
                            color="error"
                            onClick={() => cancelBulkJob(job.id)}
                          >
                            Cancel
                          </Button>
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            )}
          </Grid>
        </Grid>
      </TabPanel>

      {/* Company Profile Dialog */}
      <Dialog
        open={profileDialogOpen}
        onClose={() => setProfileDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {selectedCompany?.company.company_name}
            </Typography>
            <Chip
              label={selectedCompany?.company.company_number}
              variant="outlined"
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedCompany && (
            <Box>
              {/* Company Overview */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <InfoIcon />
                    Company Overview
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Status</Typography>
                      <Chip
                        label={selectedCompany.company.company_status}
                        color={getStatusColor(selectedCompany.company.company_status) as any}
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Type</Typography>
                      <Typography variant="body1">{selectedCompany.company.company_type}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Incorporated</Typography>
                      <Typography variant="body1">{formatDate(selectedCompany.company.date_of_creation)}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Jurisdiction</Typography>
                      <Typography variant="body1">{selectedCompany.company.jurisdiction || 'N/A'}</Typography>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Registered Office */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AddressIcon />
                    Registered Office
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body1">
                    {selectedCompany.company.registered_office_address.address_line_1}
                    {selectedCompany.company.registered_office_address.address_line_2 && 
                      `, ${selectedCompany.company.registered_office_address.address_line_2}`}
                    <br />
                    {selectedCompany.company.registered_office_address.locality}
                    {selectedCompany.company.registered_office_address.postal_code && 
                      ` ${selectedCompany.company.registered_office_address.postal_code}`}
                    <br />
                    {selectedCompany.company.registered_office_address.country}
                  </Typography>
                </AccordionDetails>
              </Accordion>

              {/* Officers */}
              {selectedCompany.officers && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <OfficerIcon />
                      Officers ({selectedCompany.officers.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {selectedCompany.officers.map((officer, index) => (
                        <ListItem key={index}>
                          <ListItemText
                            primary={officer.name}
                            secondary={
                              <Box>
                                <Typography variant="body2">{officer.officer_role}</Typography>
                                {officer.appointed_on && (
                                  <Typography variant="caption">
                                    Appointed: {formatDate(officer.appointed_on)}
                                  </Typography>
                                )}
                                {officer.resigned_on && (
                                  <Typography variant="caption" color="error">
                                    {' '} • Resigned: {formatDate(officer.resigned_on)}
                                  </Typography>
                                )}
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Recent Filings */}
              {selectedCompany.filings && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <FilingIcon />
                      Recent Filings ({selectedCompany.filings.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {selectedCompany.filings.slice(0, 10).map((filing, index) => (
                        <ListItem key={index}>
                          <ListItemText
                            primary={filing.description}
                            secondary={`${filing.type} • ${formatDate(filing.date)}`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton
                              onClick={() => downloadFiling(selectedCompany.company.company_number, filing.transaction_id)}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProfileDialogOpen(false)}>Close</Button>
          {selectedCompany && (
            <Button
              startIcon={<BulkDownloadIcon />}
              onClick={() => {
                setBulkCompanyNumbers(selectedCompany.company.company_number);
                setProfileDialogOpen(false);
                setTabValue(1);
              }}
            >
              Bulk Download
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CompaniesHousePage; 