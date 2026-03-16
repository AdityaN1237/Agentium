'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AgentMetadata, AgentCreatePayload, AgentUpdatePayload } from '@/types/agent';
import { agentApi } from '@/services/api';

interface AgentContextType {
    agents: AgentMetadata[];
    activeAgent: AgentMetadata | null;
    setActiveAgent: (agent: AgentMetadata | null) => void;
    isLoading: boolean;
    refreshAgents: () => Promise<void>;
    createAgent: (data: AgentCreatePayload) => Promise<void>;
    updateAgent: (id: string, data: AgentUpdatePayload) => Promise<void>;
    deleteAgent: (id: string) => Promise<void>;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export const AgentProvider = ({ children }: { children: ReactNode }) => {
    const [agents, setAgents] = useState<AgentMetadata[]>([]);
    const [activeAgent, setActiveAgent] = useState<AgentMetadata | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshAgents = async () => {
        setIsLoading(true);
        try {
            const response = await agentApi.list();
            setAgents(response.data);
            if (response.data.length > 0 && !activeAgent) {
                setActiveAgent(response.data[0]);
            }
        } catch (error) {
            console.error('Failed to fetch agents:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const createAgent = async (data: AgentCreatePayload) => {
        await agentApi.create(data);
        await refreshAgents();
    };

    const updateAgent = async (id: string, data: AgentUpdatePayload) => {
        await agentApi.update(id, data);
        await refreshAgents();
    };

    const deleteAgent = async (id: string) => {
        await agentApi.delete(id);
        if (activeAgent?.id === id) {
            setActiveAgent(null);
        }
        await refreshAgents();
    };

    useEffect(() => {
        const load = async () => {
            setIsLoading(true);
            try {
                const response = await agentApi.list();
                setAgents(response.data);
                if (response.data.length > 0) {
                    setActiveAgent(prev => prev ?? response.data[0]);
                }
            } catch (error) {
                console.error('Failed to fetch agents:', error);
            } finally {
                setIsLoading(false);
            }
        };
        load();
        // no dependencies: run on mount
    }, []);

    return (
        <AgentContext.Provider value={{
            agents,
            activeAgent,
            setActiveAgent,
            isLoading,
            refreshAgents,
            createAgent,
            updateAgent,
            deleteAgent
        }}>
            {children}
        </AgentContext.Provider>
    );
};

export const useAgents = () => {
    const context = useContext(AgentContext);
    if (context === undefined) {
        throw new Error('useAgents must be used within an AgentProvider');
    }
    return context;
};
