import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  Paper,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tab,
  Tabs,
  LinearProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Gavel as GavelIcon,
  Search as SearchIcon,
  BookmarkBorder as BookmarkIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  Description as CaseIcon,
  AccountBalance as CourtIcon,
  DateRange as DateIcon,
  Person as JudgeIcon,
  Scale as ScaleIcon
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

interface LegalCase {
  id: string;
  title: string;
  citation: string;
  court: string;
  date: string;
  judge: string;
  summary: string;
  relevanceScore: number;
  keyPoints: string[];
}

interface CitationFormat {
  name: string;
  example: string;
}

const LegalCitationPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [jurisdiction, setJurisdiction] = useState('UK');
  const [courtLevel, setCourtLevel] = useState('all');
  const [dateRange, setDateRange] = useState('all');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<LegalCase[]>([]);
  const [citationQuery, setCitationQuery] = useState('');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    
    // Simulate API call delay
    setTimeout(() => {
      // Mock search results
      const mockResults: LegalCase[] = [
        {
          id: '1',
          title: 'R v Secretary of State for Transport, ex parte Factortame Ltd',
          citation: '[1990] 2 AC 85',
          court: 'House of Lords',
          date: '1990-06-21',
          judge: 'Lord Bridge',
          summary: 'Landmark case establishing the supremacy of EU law over conflicting provisions of national law.',
          relevanceScore: 95,
          keyPoints: [
            'EU law supremacy principle',
            'National court obligations',
            'Interim relief in EU law cases'
          ]
        },
        {
          id: '2',
          title: 'Donoghue v Stevenson',
          citation: '[1932] AC 562',
          court: 'House of Lords',
          date: '1932-05-26',
          judge: 'Lord Atkin',
          summary: 'Foundational case in tort law establishing the modern law of negligence and the neighbour principle.',
          relevanceScore: 88,
          keyPoints: [
            'Duty of care',
            'Neighbour principle',
            'Product liability'
          ]
        },
        {
          id: '3',
          title: 'Caparo Industries plc v Dickman',
          citation: '[1990] 2 AC 605',
          court: 'House of Lords',
          date: '1990-02-08',
          judge: 'Lord Bridge',
          summary: 'Established the three-stage test for determining duty of care in negligence claims.',
          relevanceScore: 82,
          keyPoints: [
            'Three-stage test',
            'Foreseeability',
            'Proximity and fairness'
          ]
        }
      ];
      
      setSearchResults(mockResults);
      setIsSearching(false);
    }, 2000);
  };

  const citationFormats: CitationFormat[] = [
    {
      name: 'OSCOLA (Oxford)',
      example: 'R v Secretary of State for Transport, ex parte Factortame Ltd [1990] 2 AC 85'
    },
    {
      name: 'AGLC (Australian)',
      example: 'R v Secretary of State for Transport, ex parte Factortame Ltd [1990] 2 AC 85'
    },
    {
      name: 'Bluebook (US)',
      example: 'R v Secretary of State for Transport, ex parte Factortame Ltd, [1990] 2 AC 85 (H.L.)'
    }
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <GavelIcon sx={{ fontSize: 40 }} />
        Legal Citation & Case Law Research
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          🏛️ Advanced Legal Research Platform
        </Typography>
        <Typography variant="body2">
          Search case law, generate citations, and analyze legal precedents across multiple jurisdictions. 
          Integration with legal databases coming soon.
        </Typography>
      </Alert>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Case Law Search" />
          <Tab label="Citation Generator" />
          <Tab label="Legal Analysis" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {/* Case Law Search */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Search Parameters</Typography>
                
                <TextField
                  fullWidth
                  label="Search Query"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., negligence duty of care, contract formation..."
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Jurisdiction</InputLabel>
                  <Select
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    label="Jurisdiction"
                  >
                    <MenuItem value="UK">United Kingdom</MenuItem>
                    <MenuItem value="EU">European Union</MenuItem>
                    <MenuItem value="US">United States</MenuItem>
                    <MenuItem value="AU">Australia</MenuItem>
                    <MenuItem value="CA">Canada</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Court Level</InputLabel>
                  <Select
                    value={courtLevel}
                    onChange={(e) => setCourtLevel(e.target.value)}
                    label="Court Level"
                  >
                    <MenuItem value="all">All Courts</MenuItem>
                    <MenuItem value="supreme">Supreme/House of Lords</MenuItem>
                    <MenuItem value="appeal">Court of Appeal</MenuItem>
                    <MenuItem value="high">High Court</MenuItem>
                    <MenuItem value="crown">Crown Court</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Date Range</InputLabel>
                  <Select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    label="Date Range"
                  >
                    <MenuItem value="all">All Time</MenuItem>
                    <MenuItem value="recent">Last 5 Years</MenuItem>
                    <MenuItem value="decade">Last 10 Years</MenuItem>
                    <MenuItem value="modern">Since 2000</MenuItem>
                    <MenuItem value="20th">20th Century</MenuItem>
                  </Select>
                </FormControl>

                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleSearch}
                  disabled={isSearching || !searchQuery.trim()}
                  sx={{ mb: 2 }}
                >
                  {isSearching ? 'Searching...' : 'Search Case Law'}
                </Button>

                {isSearching && <LinearProgress />}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Search Results</Typography>
                
                {searchResults.length === 0 && !isSearching && (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <ScaleIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      No search performed yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Enter search terms and click "Search Case Law" to find relevant cases
                    </Typography>
                  </Box>
                )}

                {searchResults.map((case_) => (
                  <Paper key={case_.id} sx={{ p: 2, mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                      <Typography variant="h6" sx={{ flexGrow: 1 }}>
                        {case_.title}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="Bookmark Case">
                          <IconButton size="small">
                            <BookmarkIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Share">
                          <IconButton size="small">
                            <ShareIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download">
                          <IconButton size="small">
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                    
                    <Typography variant="subtitle1" color="primary" sx={{ mb: 1 }}>
                      {case_.citation}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <CourtIcon fontSize="small" />
                        <Typography variant="body2">{case_.court}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <DateIcon fontSize="small" />
                        <Typography variant="body2">{new Date(case_.date).toLocaleDateString()}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <JudgeIcon fontSize="small" />
                        <Typography variant="body2">{case_.judge}</Typography>
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {case_.summary}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      {case_.keyPoints.map((point, index) => (
                        <Chip key={index} label={point} size="small" variant="outlined" />
                      ))}
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Relevance Score:
                      </Typography>
                      <Chip 
                        label={`${case_.relevanceScore}%`} 
                        color={case_.relevanceScore > 90 ? 'success' : case_.relevanceScore > 75 ? 'primary' : 'default'}
                        size="small"
                      />
                    </Box>
                  </Paper>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Citation Generator */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Generate Citation</Typography>
                
                <TextField
                  fullWidth
                  label="Case Name or Citation"
                  value={citationQuery}
                  onChange={(e) => setCitationQuery(e.target.value)}
                  placeholder="e.g., Donoghue v Stevenson or [1932] AC 562"
                  sx={{ mb: 2 }}
                />

                <Button variant="contained" disabled sx={{ mb: 3 }}>
                  Generate Citation (Coming Soon)
                </Button>

                <Divider sx={{ mb: 2 }} />
                
                <Typography variant="subtitle1" gutterBottom>Citation Formats</Typography>
                <List dense>
                  {citationFormats.map((format, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CaseIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={format.name}
                        secondary={format.example}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Citation Tips</Typography>
                
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">OSCOLA (Oxford Standard)</Typography>
                  <Typography variant="body2">
                    Most commonly used in UK legal writing. Format: Case Name [Year] Volume Reporter Page
                  </Typography>
                </Alert>

                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Neutral Citations</Typography>
                  <Typography variant="body2">
                    For cases from 2001 onwards, use neutral citations: [Year] Court Number
                  </Typography>
                </Alert>

                <Alert severity="success">
                  <Typography variant="subtitle2">Best Practices</Typography>
                  <Typography variant="body2">
                    • Always check the most recent citation
                    • Include pinpoint references for specific points
                    • Use appropriate abbreviations for courts
                  </Typography>
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Legal Analysis */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Legal Analysis Tools</Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              Advanced legal analysis features including precedent tracking, case comparison, 
              and legislative analysis will be available in future updates.
            </Alert>

            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <GavelIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6">Precedent Analysis</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Track how cases have been cited and applied in subsequent decisions
                  </Typography>
                  <Button variant="outlined" disabled sx={{ mt: 1 }}>
                    Coming Soon
                  </Button>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <ScaleIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6">Case Comparison</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Compare multiple cases side-by-side to identify patterns and differences
                  </Typography>
                  <Button variant="outlined" disabled sx={{ mt: 1 }}>
                    Coming Soon
                  </Button>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <CourtIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6">Legislative Tracker</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Monitor changes in legislation and their impact on existing case law
                  </Typography>
                  <Button variant="outlined" disabled sx={{ mt: 1 }}>
                    Coming Soon
                  </Button>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default LegalCitationPage;