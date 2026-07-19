/**
 * Streaming API Client with Server-Sent Events (SSE)
 * 
 * Provides real-time component updates as the LLM generates them.
 * This is an OPTIONAL optimization for better perceived performance.
 */

import { ComponentSpec, LayoutSpec } from '@/types/api';

export interface StreamEvents {
  onProgress?: (data: { bytes: number }) => void;
  onComponent?: (component: ComponentSpec) => void;
  onLayout?: (layout: LayoutSpec) => void;
  onDataModel?: (dataModel: any) => void;
  onComplete?: (data: { success: boolean; message: string }) => void;
  onError?: (error: string) => void;
}

export interface StreamOptions {
  apiUrl?: string;
  signal?: AbortSignal;  // For cancellation
}

/**
 * Create a task with streaming updates
 * 
 * @param userInput - The user's query
 * @param events - Event handlers for different message types
 * @param options - Optional configuration
 */
export async function createTaskWithStreaming(
  userInput: string,
  events: StreamEvents,
  options: StreamOptions = {}
): Promise<void> {
  const apiUrl = options.apiUrl || import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const url = `${apiUrl}/api/refine/stream`;

  try {
    // Make POST request with EventSource-compatible body
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ user_input: userInput }),
      signal: options.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Read stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      // Decode chunk
      buffer += decoder.decode(value, { stream: true });

      // Process complete messages
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || ''; // Keep incomplete message in buffer

      for (const message of messages) {
        if (!message.trim()) continue;

        // Parse SSE message format
        const lines = message.split('\n');
        let eventType = 'message';
        let data = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            data = line.substring(5).trim();
          }
        }

        // Handle event
        try {
          const parsedData = JSON.parse(data);
          handleStreamEvent(eventType, parsedData, events);
        } catch (e) {
          console.error('[Streaming] Failed to parse event data:', e, data);
        }
      }
    }
  } catch (error) {
    if (error instanceof Error) {
      console.error('[Streaming] Error:', error.message);
      events.onError?.(error.message);
    } else {
      console.error('[Streaming] Unknown error:', error);
      events.onError?.('Unknown streaming error');
    }
  }
}

/**
 * Handle individual stream events
 */
function handleStreamEvent(
  eventType: string,
  data: any,
  events: StreamEvents
): void {
  console.log(`[Streaming] Event: ${eventType}`, data);

  switch (eventType) {
    case 'progress':
      events.onProgress?.(data);
      break;

    case 'component':
      // Validate component structure
      if (data.type && data.props) {
        events.onComponent?.(data as ComponentSpec);
      } else {
        console.warn('[Streaming] Invalid component data:', data);
      }
      break;

    case 'layout':
      events.onLayout?.(data as LayoutSpec);
      break;

    case 'data_model':
      events.onDataModel?.(data);
      break;

    case 'complete':
      events.onComplete?.(data);
      break;

    case 'error':
      events.onError?.(data.error || 'Unknown error');
      break;

    default:
      console.warn(`[Streaming] Unknown event type: ${eventType}`);
  }
}

/**
 * Hook to use streaming in React components
 * 
 * Example usage:
 * ```tsx
 * const { startStream, isStreaming, cancel } = useStreaming({
 *   onComponent: (comp) => setComponents(prev => [...prev, comp]),
 *   onComplete: () => setLoading(false),
 * });
 * 
 * // Start streaming
 * await startStream("Compare NVIDIA vs AMD");
 * ```
 */
export function useStreaming(events: StreamEvents) {
  const [isStreaming, setIsStreaming] = React.useState(false);
  const abortControllerRef = React.useRef<AbortController | null>(null);

  const startStream = React.useCallback(
    async (userInput: string) => {
      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();
      setIsStreaming(true);

      try {
        await createTaskWithStreaming(userInput, events, {
          signal: abortControllerRef.current.signal,
        });
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [events]
  );

  const cancel = React.useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { startStream, isStreaming, cancel };
}

// Re-export React for the hook
import * as React from 'react';
