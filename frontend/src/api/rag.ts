/**
 * Simple RAG API client with 3-step process support
 */

import axios from 'axios';
import { useMutation, useQuery } from '@tanstack/react-query';

// Types
export interface QuestionRequest {
  question: string;
  session_id?: string;
  max_chunks?: number;
  min_relevance?: number;
  include_sources?: boolean;
  response_style?: string;
  max_tokens?: number;
  // Litigation-specific options
  matter_type?: 'litigation' | 'tort' | 'criminal' | 'civil_procedure' | 'evidence' | 'constitutional';
  analysis_style?: 'comprehensive' | 'concise' | 'technical';
  focus_area?: 'liability' | 'procedural' | 'evidence' | 'damages' | 'defenses' | 'settlement';
}

export interface AnswerResponse {
  answer: string;
  confidence: number;
  sources: Array<{
    document_id: string;
    filename: string;
    chunk_id: string;
    relevance_score: number;
    text_excerpt: string;
  }>;
  chunks_analyzed: number;
  chunks_used: number;
  processing_time: number;
  model_used: string;
  // Litigation-specific response fields
  party_positions?: {
    plaintiff?: string;
    defendant?: string;
  };
  argument_strengths?: {
    plaintiff_strength?: number;
    defendant_strength?: number;
    overall_assessment?: string;
  };
  litigation_analysis?: {
    issue?: string;
    rule?: string;
    application?: string;
    conclusion?: string;
  };
}

export interface StatusResponse {
  status: string;
  models: {
    embedder?: boolean;
    utility?: boolean;
    reasoning?: boolean;
  };
  documents: {
    count: number;
    indexed: boolean;
  };
  chunks: {
    count: number;
    indexed: boolean;
  };
  ready: boolean;
  message: string;
  hardware?: {
    memory_usage: number;
    gpu_available: boolean;
    total_memory: number;
  };
}

export interface UploadResponse {
  message: string;
  doc_id: string;
  chunks_created: number;
  processing_time: number;
  task_id?: string; // Add optional task_id for backward compatibility
}

// Legacy types for backward compatibility
export interface StreamMessage {
  type: string;
  session_id?: string;
  content?: string;
  step?: string;
  status?: string;
  message?: string;
  component?: string;
  context_type?: string;
  token_usage?: any;
  error?: string;
  timestamp: number;
  current?: number;
  total?: number;
  answer?: string;
  confidence?: number;
  model?: string;
}

export interface TaskStatus {
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  files: string[];
  created: string;
  results?: any;
  error?: string;
}

export interface HardwareStatus {
  gpu_available: boolean;
  memory_usage: number;
  total_memory: number;
  cuda_available?: boolean;
  gpu_memory?: {
    allocated: number;
    total: number;
  };
  tf32_enabled?: boolean;
  requirements_met?: boolean;
  warnings?: string[];
  memory?: {
    gpu_allocated_gb: number;
    gpu_total_gb: number;
  };
}

// API Client - Use simple RAG endpoint
const API_BASE = '/api/rag';

// React Query hooks
export const useRAGStatus = () => {
  return useQuery<StatusResponse>({
    queryKey: ['rag-status'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/status`);
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useRAGAnswer = () => {
  return useMutation<AnswerResponse, Error, QuestionRequest>({
    mutationFn: async (request) => {
      const response = await axios.post(`${API_BASE}/answer`, request);
      return response.data;
    },
  });
};

export const useRAGUpload = () => {
  return useMutation<UploadResponse, Error, FormData>({
    mutationFn: async (formData) => {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
  });
};

export const useRAGDocuments = () => {
  return useQuery({
    queryKey: ['rag-documents'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/documents`);
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
};

export const useRAGDeleteDocument = () => {
  return useMutation<{ message: string }, Error, string>({
    mutationFn: async (docId) => {
      const response = await axios.delete(`${API_BASE}/documents/${docId}`);
      return response.data;
    },
  });
};

export const useRAGInitialize = () => {
  return useMutation<{ message: string; status: string }, Error, void>({
    mutationFn: async () => {
      const response = await axios.post(`${API_BASE}/initialize`);
      return response.data;
    },
  });
};

// Legacy compatibility hooks
export const useInitializeRAG = useRAGInitialize;
export const useAskQuestion = useRAGAnswer;
export const useUploadDocuments = useRAGUpload;

// Mock implementations for removed functionality
export const useHardwareStatus = () => {
  return useQuery<HardwareStatus>({
    queryKey: ['hardware-status'],
    queryFn: async () => {
      // Mock hardware status since we removed the hardware endpoint
      return {
        gpu_available: true,
        memory_usage: 2.9,
        total_memory: 8.0
      };
    },
    refetchInterval: 10000,
  });
};

export const useClearCache = () => {
  return useMutation({
    mutationFn: async () => {
      // Mock clear cache since we removed this endpoint
      return { message: "Cache cleared successfully" };
    },
  });
};

export const useWarmupModels = () => {
  return useMutation({
    mutationFn: async () => {
      // Mock warmup since models are loaded progressively
      return { message: "Models warmed up successfully" };
    },
  });
};

export const useTaskStatus = (taskId: string | null) => {
  return useQuery<TaskStatus>({
    queryKey: ['task-status', taskId],
    queryFn: async () => {
      if (!taskId) throw new Error('No task ID');
      // Mock task status since we removed task-based uploads
      return {
        status: 'completed',
        progress: 100,
        files: [],
        created: new Date().toISOString(),
        results: { message: "Upload completed" }
      };
    },
    enabled: !!taskId,
    refetchInterval: false,
  });
};

// WebSocket streaming (mock implementation)
export const connectStream = (
  question: string, 
  onMessage: (message: StreamMessage) => void,
  onError?: (error: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket => {
  // Mock WebSocket since we removed streaming
  const mockWs = {
    onopen: () => {},
    onmessage: () => {},
    onerror: () => {},
    onclose: () => {},
    send: () => {},
    close: () => {},
    binaryType: 'blob' as BinaryType,
    bufferedAmount: 0,
    extensions: '',
    protocol: '',
    readyState: 1,
    url: '',
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true
  } as unknown as WebSocket;
  
  // Simulate immediate response
  setTimeout(() => {
    onMessage({
      type: 'answer',
      content: 'Mock response - streaming not implemented in Simple RAG',
      timestamp: Date.now()
    });
  }, 1000);
  
  return mockWs;
};

// Health check
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['rag-health'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/health`);
      return response.data;
    },
    refetchInterval: 60000, // Check every minute
  });
};

// Utility functions
export const createQuestionRequest = (
  question: string,
  options?: {
    max_chunks?: number;
    min_relevance?: number;
    include_sources?: boolean;
    response_style?: string;
  }
): QuestionRequest => {
  return {
    question,
    max_chunks: options?.max_chunks ?? 5,
    min_relevance: options?.min_relevance ?? 0.3,
    include_sources: options?.include_sources ?? true,
    response_style: options?.response_style ?? 'detailed',
  };
};

export const createUploadFormData = (file: File): FormData => {
  const formData = new FormData();
  formData.append('file', file);
  return formData;
};