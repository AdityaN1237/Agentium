export interface AgentMetadata {
    id: string;
    name: string;
    description: string;
    version: string;
    status: 'active' | 'training' | 'error' | 'inactive';
    last_trained?: string;
    accuracy?: number;
    type?: string;
    config?: Record<string, unknown>;
}

export interface TrainingMetric {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    timestamp: string;
}

export interface TrainingLog {
    run_id: string;
    timestamp: string;
    status: 'completed' | 'failed' | 'in_progress';
    metrics: Record<string, number>;
    logs: string[];
}

export interface AgentStats {
    agent_id: string;
    total_trainings: number;
    best_accuracy: number;
    last_run_status: string;
    history: unknown[];
}

export interface AgentCreatePayload {
    id: string;
    name: string;
    description: string;
    type: string;
    config?: Record<string, unknown>;
}

export interface AgentUpdatePayload {
    id?: string;
    name?: string;
    description?: string;
    type?: string;
    config?: Record<string, unknown>;
}

export type PredictPayload = Record<string, unknown>;

export interface ModelStatus {
    has_embeddings: boolean;
    latest_version: string;
    embedding_count: number;
    last_saved: string;
}
