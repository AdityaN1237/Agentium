import axios from 'axios';
import { AgentMetadata, TrainingMetric, AgentCreatePayload, AgentUpdatePayload, PredictPayload } from '@/types/agent';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Client-side cache for stats
let statsCache: { data: SystemStats; timestamp: number } | null = null;
const STATS_CACHE_TTL = 30000; // 30 seconds

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30s timeout for ML tasks
});

// Request Interceptor
apiClient.interceptors.request.use((config) => {
    try {
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
    } catch (err) {
        console.warn('⚠️ Failed to load auth token from storage:', err);
    }
    return config;
});

// Response Interceptor
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const status = error?.response?.status;
        const data = error?.response?.data;

        if (error.message === 'Network Error') {
            console.error(`❌ Network Error: Backend unreachable at ${API_BASE_URL}`);
        } else if (status === 500) {
            console.error('🔥 Server Error (500):', data?.detail || error.message);
        } else if (status === 400) {
            console.warn('⚠️ Bad Request (400):', data?.detail || 'Invalid payload');
        }

        // Token Refresh Logic
        const originalRequest = error.config;
        if (status === 401 && typeof window !== 'undefined' && !originalRequest?._retry) {
            originalRequest._retry = true;
            try {
                const refreshToken = localStorage.getItem('refreshToken');
                if (refreshToken) {
                    const refreshRes = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
                    const newToken = refreshRes.data?.access_token;
                    if (newToken) {
                        localStorage.setItem('token', newToken);
                        originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        return apiClient(originalRequest);
                    }
                }
            } catch {
                console.error('🚪 Session expired. Redirecting to login...');
                localStorage.removeItem('token');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export const agentApi = {
    list: () => apiClient.get<AgentMetadata[]>('/agents/'),
    getById: (id: string) => apiClient.get<AgentMetadata>(`/agents/${id}`),
    create: (data: AgentCreatePayload) => apiClient.post('/agents/', data),
    update: (id: string, data: AgentUpdatePayload) => apiClient.put(`/agents/${id}`, data),
    delete: (id: string) => apiClient.delete(`/agents/${id}`),
    getTypes: () => apiClient.get<string[]>('/agents/types'),
    upload: (id: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post(`/agents/${id}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 300000
        });
    },
    train: (id: string, config: Record<string, unknown> = {}) => apiClient.post(`/agents/${id}/train`, config),
    stop: (id: string) => apiClient.post(`/agents/${id}/stop`),
    getMetrics: (id: string) => apiClient.get<TrainingMetric>(`/agents/${id}/metrics`),
    predict: (id: string, data: PredictPayload) => apiClient.post(`/agents/${id}/predict`, data),
    predictFile: (id: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post<PredictFileResponse>(`/agents/${id}/predict/file`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    getTrainingWsUrl: (id: string) => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Ensure we use the exact same host as the API
        const host = API_BASE_URL.replace(/^https?:\/\//, '');
        return `${wsProtocol}//${host}/agents/${id}/training/ws`;
    },
    protocol: (id: string) => apiClient.get<Record<string, unknown>>(`/agents/${id}/protocol`)
};

export const modelApi = {
    getAllStatus: () => apiClient.get('/models/status'),
    getAgentStatus: (agentId: string) => apiClient.get(`/models/${agentId}/status`),
};

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export interface ChatResponse {
    response: string;
    sources?: { title: string; source: string; score: number }[];
    metadata?: {
        confidence?: number;
        latency_ms?: number;
        verified?: boolean;
        [key: string]: unknown;
    };
    agent_used: string;
    context_id: string;
}

export const chatApi = {
    send: (messages: ChatMessage[], contextId?: string, agentId?: string) =>
        apiClient.post<ChatResponse>('/chat/', { messages, context_id: contextId, agent_id: agentId }),
    clearContext: (contextId: string) => apiClient.delete(`/chat/context/${contextId}`)
};

export interface SystemStats {
    candidates: number;
    jobs: { total: number; active: number };
    system: {
        active_agents: number;
        training_active: number;
        total_vectors: number;
        global_queries: number;
        health_score: number;
    };
    ai_config: {
        embedding_model: string;
        embedding_dimension: number;
        weights: {
            semantic: number;
            skill_match: number;
            preference: number;
        };
    };
}

export interface AnalyticsData {
    skill_composition: { name: string; value: number; fill: string }[];
    market_drift: { subject: string; A: number; B: number; fullMark: number }[];
    inference_quality: { month: string; accuracy: number; latency: number }[];
}

export const systemApi = {
    stats: async () => {
        const now = Date.now();
        if (statsCache && (now - statsCache.timestamp) < STATS_CACHE_TTL) {
            return { data: statsCache.data };
        }
        const response = await apiClient.get<SystemStats>('/stats');
        statsCache = { data: response.data, timestamp: now };
        return response;
    },
    health: () => apiClient.get('/health'),
    analytics: () => apiClient.get<AnalyticsData>('/analytics/'),
};

// --- Candidates ---
export interface Candidate {
    _id: string;
    name: string;
    email?: string;
    current_role?: string;
    experience_years?: number;
    skills: string[];
    expanded_skills?: string[];
    resume_text?: string;
}

export interface CandidateListResponse {
    total: number;
    page: number;
    page_size: number;
    candidates: Candidate[];
}

export interface CandidateCreatePayload {
    name: string;
    email: string;
    current_role?: string;
    experience_years?: number;
    skills: string[];
    resume_text: string;
}

export const candidatesApi = {
    list: (params?: { page?: number; page_size?: number; skill?: string; search?: string }) =>
        apiClient.get<CandidateListResponse>('/candidates/', { params }),
    getById: (id: string) => apiClient.get<Candidate>(`/candidates/${id}`),
    create: (data: CandidateCreatePayload) => apiClient.post('/candidates/', data),
    update: (id: string, data: CandidateCreatePayload) => apiClient.put(`/candidates/${id}`, data),
    delete: (id: string) => apiClient.delete(`/candidates/${id}`),
    expandedSkills: (id: string) => apiClient.get<{ candidate_id: string; original_skills: string[]; expanded_skills: string[] }>(`/candidates/${id}/skills/expanded`),
    stats: () => apiClient.get('/candidates/stats/summary'),
};

// --- Jobs ---
export interface Job {
    _id: string;
    title: string;
    company?: string;
    location?: string;
    description?: string;
    required_skills: string[];
    nice_to_have?: string[];
    is_active?: boolean;
}

export interface JobListResponse {
    total: number;
    page: number;
    page_size: number;
    jobs: Job[];
}

export interface JobCreatePayload {
    title: string;
    company?: string;
    location?: string;
    description?: string;
    required_skills: string[];
    nice_to_have?: string[];
    is_active?: boolean;
}

export const jobsApi = {
    list: (params?: { page?: number; page_size?: number; skill?: string; search?: string; company?: string; location?: string }) =>
        apiClient.get<JobListResponse>('/jobs/', { params }),
    getById: (id: string) => apiClient.get<Job>(`/jobs/${id}`),
    create: (data: JobCreatePayload) => apiClient.post('/jobs/', data),
    update: (id: string, data: JobCreatePayload) => apiClient.put(`/jobs/${id}`, data),
    delete: (id: string) => apiClient.delete(`/jobs/${id}`),
    expandedSkills: (id: string) => apiClient.get<{ job_id: string; original_skills: string[]; expanded_skills: string[] }>(`/jobs/${id}/skills/expanded`),
    stats: () => apiClient.get('/jobs/stats/summary'),
};

// --- Resumes ---
export interface ResumeRecord {
    _id: string;
    user_id: string;
    filename: string;
    content_type: string;
    file_path: string;
    resume_text?: string;
    extracted_skills?: string[];
    current_role?: string | null;
    experience_years?: number;
    created_at?: string;
    updated_at?: string;
}

export const resumesApi = {
    upload: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post('/resumes/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
    me: () => apiClient.get<ResumeRecord | { message: string }>('/resumes/me'),
    list: (params?: { page?: number; page_size?: number }) =>
        apiClient.get<{ total: number; page: number; page_size: number; resumes: ResumeRecord[] }>('/resumes/', { params }),
    recommendationsForCandidate: (candidateId: string, top_k?: number) =>
        apiClient.get(`/recommendations/${candidateId}`, { params: { top_k } }),
    batchProcess: (directory: string) => apiClient.post('/resumes/batch', { directory })
};

export interface MatchedJob {
    job_id: string;
    title: string;
    company: string;
    score: number;
    required_skills: string[];
    description?: string;
}

export type PredictFileResponse = MatchedJob[];

