import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  FormControlLabel,
  Switch,
  Chip,
  Typography,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Send as SendIcon,
  Clear as ClearIcon,
  Settings as SettingsIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';

export interface AskOptions {
  max_chunks?: number;
  min_relevance?: number;
  include_sources?: boolean;
  response_style?: string;
  // Litigation-specific options
  matter_type?: 'litigation' | 'tort' | 'criminal' | 'civil_procedure' | 'evidence' | 'constitutional';
  analysis_style?: 'comprehensive' | 'concise' | 'technical';
  focus_area?: 'liability' | 'procedural' | 'evidence' | 'damages' | 'defenses' | 'settlement';
}

interface AskBarProps {
  onSubmit: (question: string, options: AskOptions) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
}

const AskBar: React.FC<AskBarProps> = ({ 
  onSubmit, 
  disabled = false, 
  loading = false,
  placeholder = "Ask a litigation question..."
}) => {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState<AskOptions>({
    max_chunks: 15,
    min_relevance: 0.2,
    include_sources: true,
    response_style: 'detailed',
    matter_type: 'litigation',
    analysis_style: 'comprehensive',
    focus_area: 'liability'
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !loading) {
      onSubmit(question.trim(), options);
      setQuestion(''); // Clear input after submit
    }
  };

  const handleClear = () => {
    setQuestion('');
  };

  const exampleQuestions = [
    "What are the plaintiff's strongest arguments in this negligence case?",
    "Analyze the defendant's potential defenses and their strength",
    "What evidence would be most critical for proving liability?",
    "How does the burden of proof apply to this litigation matter?",
    "What procedural issues might arise in this case?",
    "Assess the settlement value based on the available evidence"
  ];

  const handleExampleClick = (example: string) => {
    setQuestion(example);
  };

  return (
    <Paper sx={{ p: 3, mb: 2 }}>
      {/* Main Input Form */}
      <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={placeholder}
            disabled={disabled || loading}
            variant="outlined"
            size="medium"
            InputProps={{
              endAdornment: question && (
                <Tooltip title="Clear">
                  <IconButton 
                    size="small" 
                    onClick={handleClear}
                    disabled={loading}
                  >
                    <ClearIcon />
                  </IconButton>
                </Tooltip>
              )
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                fontSize: '1rem',
                lineHeight: 1.5
              }
            }}
          />
          
          <Tooltip title="Advanced Options">
            <IconButton 
              color={showAdvanced ? 'primary' : 'default'}
              onClick={() => setShowAdvanced(!showAdvanced)}
              disabled={loading}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            type="submit"
            variant="contained"
            disabled={!question.trim() || disabled || loading}
            startIcon={loading ? <PsychologyIcon className="animate-spin" /> : <SendIcon />}
            size="large"
            sx={{ 
              minWidth: 120,
              height: 56 // Match TextField height
            }}
          >
            {loading ? 'Processing...' : 'Ask'}
          </Button>
        </Box>
      </Box>

      {/* Advanced Options */}
      {showAdvanced && (
        <Box sx={{ 
          p: 2, 
          backgroundColor: 'grey.50', 
          borderRadius: 1, 
          border: '1px solid',
          borderColor: 'divider',
          mb: 2
        }}>
          <Typography variant="subtitle2" gutterBottom>
            Query Options
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <TextField
              label="Max Chunks"
              type="number"
              size="small"
              value={options.max_chunks}
              onChange={(e) => setOptions(prev => ({ ...prev, max_chunks: parseInt(e.target.value) || 15 }))}
              disabled={loading}
              inputProps={{ min: 1, max: 30 }}
              sx={{ width: 120 }}
              helperText="15-30 for comprehensive analysis"
            />
            
            <TextField
              label="Min Relevance"
              type="number"
              size="small"
              value={options.min_relevance}
              onChange={(e) => setOptions(prev => ({ ...prev, min_relevance: parseFloat(e.target.value) || 0.2 }))}
              disabled={loading}
              inputProps={{ min: 0.0, max: 1.0, step: 0.1 }}
              sx={{ width: 120 }}
              helperText="0.2-0.4 for more chunks"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={options.include_sources}
                  onChange={(e) => setOptions(prev => ({ ...prev, include_sources: e.target.checked }))}
                  disabled={loading}
                />
              }
              label="Include sources"
            />
            
            <Box>
              <Typography variant="caption" display="block" gutterBottom>
                Response Style:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {(['concise', 'detailed', 'technical'] as const).map((style) => (
                  <Chip
                    key={style}
                    label={style.charAt(0).toUpperCase() + style.slice(1)}
                    variant={options.response_style === style ? 'filled' : 'outlined'}
                    color={options.response_style === style ? 'primary' : 'default'}
                    size="small"
                    clickable
                    disabled={loading}
                    onClick={() => setOptions(prev => ({ ...prev, response_style: style }))}
                  />
                ))}
              </Box>
            </Box>
          </Box>

          {/* Litigation-Specific Options */}
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            <Typography variant="subtitle2" gutterBottom>
              Litigation Analysis Options
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
              <Box>
                <Typography variant="caption" display="block" gutterBottom>
                  Matter Type:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {(['litigation', 'tort', 'criminal', 'civil_procedure', 'evidence', 'constitutional'] as const).map((type) => (
                    <Chip
                      key={type}
                      label={type.replace('_', ' ').charAt(0).toUpperCase() + type.replace('_', ' ').slice(1)}
                      variant={options.matter_type === type ? 'filled' : 'outlined'}
                      color={options.matter_type === type ? 'primary' : 'default'}
                      size="small"
                      clickable
                      disabled={loading}
                      onClick={() => setOptions(prev => ({ ...prev, matter_type: type }))}
                    />
                  ))}
                </Box>
              </Box>

              <Box>
                <Typography variant="caption" display="block" gutterBottom>
                  Analysis Style:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {(['comprehensive', 'concise', 'technical'] as const).map((style) => (
                    <Chip
                      key={style}
                      label={style.charAt(0).toUpperCase() + style.slice(1)}
                      variant={options.analysis_style === style ? 'filled' : 'outlined'}
                      color={options.analysis_style === style ? 'primary' : 'default'}
                      size="small"
                      clickable
                      disabled={loading}
                      onClick={() => setOptions(prev => ({ ...prev, analysis_style: style }))}
                    />
                  ))}
                </Box>
              </Box>

              <Box>
                <Typography variant="caption" display="block" gutterBottom>
                  Focus Area:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {(['liability', 'procedural', 'evidence', 'damages', 'defenses', 'settlement'] as const).map((area) => (
                    <Chip
                      key={area}
                      label={area.charAt(0).toUpperCase() + area.slice(1)}
                      variant={options.focus_area === area ? 'filled' : 'outlined'}
                      color={options.focus_area === area ? 'primary' : 'default'}
                      size="small"
                      clickable
                      disabled={loading}
                      onClick={() => setOptions(prev => ({ ...prev, focus_area: area }))}
                    />
                  ))}
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
      )}

      {/* Example Questions */}
      {!question && (
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom display="block">
            Try these example questions:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {exampleQuestions.map((example, index) => (
              <Chip
                key={index}
                label={example}
                variant="outlined"
                size="small"
                clickable
                disabled={loading}
                onClick={() => handleExampleClick(example)}
                sx={{ 
                  fontSize: '0.75rem',
                  '&:hover': {
                    backgroundColor: 'primary.light',
                    color: 'white'
                  }
                }}
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Character Counter */}
      {question && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {question.length} characters
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default AskBar;