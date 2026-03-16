import { useState, useEffect, useRef } from 'react';
import { agentApi } from '@/services/api';

interface Log {
    timestamp: string;
    message: string;
    level: string;
}

type Status = 'IDLE' | 'PENDING' | 'PROCESSING' | 'INDEXING' | 'LIVE' | 'ERROR';

export function useTrainingStream(agentId?: string) {
    const [logs, setLogs] = useState<Log[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [status, setStatus] = useState<Status>('IDLE');
    const retryTimeout = useRef<NodeJS.Timeout | null>(null);
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (!agentId) {
            if (ws.current) {
                ws.current.close();
                ws.current = null;
            }
            if (retryTimeout.current) clearTimeout(retryTimeout.current);
            setTimeout(() => {
                setIsConnected(false);
                setLogs([]);
                setStatus('IDLE');
            }, 0);
            return;
        }

        const connect = () => {
            if (retryTimeout.current) clearTimeout(retryTimeout.current);

            // Avoid creating multiple connections
            if (ws.current?.readyState === WebSocket.OPEN) return;

            const url = agentApi.getTrainingWsUrl(agentId);
            const socket = new WebSocket(url);
            ws.current = socket;

            socket.onopen = () => {
                setIsConnected(true);
                // Clear any pending retry
                if (retryTimeout.current) clearTimeout(retryTimeout.current);
                setLogs(prev => [...prev, { timestamp: new Date().toISOString(), message: 'Connection established.', level: 'SYSTEM' }]);
            };

            socket.onmessage = (event) => {
                try {
                    const logData = JSON.parse(event.data) as Log;
                    if (logData.level === 'STATE') {
                        const newStatus = logData.message.toUpperCase();
                        if (['PENDING', 'PROCESSING', 'INDEXING', 'LIVE', 'ERROR'].includes(newStatus)) {
                            setStatus(newStatus as Status);
                        }
                    } else {
                        setLogs(prev => [...prev, logData]);
                    }
                } catch (e) {
                    console.error('Failed to parse log:', e);
                }
            };

            socket.onclose = () => {
                setIsConnected(false);
                setLogs(prev => [...prev, { timestamp: new Date().toISOString(), message: 'Connection closed. Retrying...', level: 'SYSTEM' }]);
                // Attempt reconnect after 3 seconds
                retryTimeout.current = setTimeout(() => {
                    if (agentId) connect();
                }, 3000);
            };

            socket.onerror = (error) => {
                console.warn('WebSocket connection failed:', error);
                // onError usually precedes onClose, close logic handles retry
                socket.close();
            };
        };

        connect();

        return () => {
            if (ws.current) ws.current.close();
            if (retryTimeout.current) clearTimeout(retryTimeout.current);
        };
    }, [agentId]);

    const clearLogs = () => {
        setLogs([]);
        setStatus('IDLE');
    };

    return { logs, isConnected, status, clearLogs };
}
