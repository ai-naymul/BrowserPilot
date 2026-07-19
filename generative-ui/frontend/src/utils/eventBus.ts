/**
 * Event Bus System
 *
 * Lightweight pub/sub system for component communication.
 * Enables direct manipulation and related module updates without prop drilling.
 *
 * Key Events:
 * - CARD_EXPANDED: When a metric card is expanded/collapsed
 * - MAP_MARKER_CLICKED: When a map marker is clicked
 * - OPEN_LOCATION_PANEL: Request to open location details panel
 * - ENTITY_SELECTED: When an entity is selected
 * - PANEL_OPENED: When a detail panel opens
 * - CARD_DELETED: When a card is removed
 * - BUDGET_CHANGED: When budget/financial data changes
 * - DETAILS_VIEWED: When entity details are viewed
 */

type Handler<T = any> = (payload: T) => void;

class EventBus {
  private eventMap = new Map<string, Set<Handler>>();

  /**
   * Subscribe to an event
   * @param eventType The event type to listen for
   * @param handler The callback function to execute
   * @returns Unsubscribe function
   */
  on<T = any>(eventType: string, handler: Handler<T>): () => void {
    const handlers = this.eventMap.get(eventType) ?? new Set();
    handlers.add(handler as Handler);
    this.eventMap.set(eventType, handlers);

    // Return unsubscribe function
    return () => this.off(eventType, handler);
  }

  /**
   * Unsubscribe from an event
   * @param eventType The event type
   * @param handler The callback function to remove
   */
  off(eventType: string, handler: Handler): void {
    this.eventMap.get(eventType)?.delete(handler);
  }

  /**
   * Emit an event
   * @param eventType The event type
   * @param payload Data to pass to handlers
   */
  emit<T = any>(eventType: string, payload: T): void {
    const handlers = this.eventMap.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(payload);
        } catch (error) {
          console.error(`[EventBus] Error in handler for "${eventType}":`, error);
        }
      });
    }
  }

  /**
   * Clear all event listeners (useful for cleanup/testing)
   */
  clear(): void {
    this.eventMap.clear();
  }

  /**
   * Get all registered event types (debugging)
   */
  getEventTypes(): string[] {
    return Array.from(this.eventMap.keys());
  }
}

// Export singleton instance
export const bus = new EventBus();

// Export class for testing
export { EventBus };

// Type-safe event payload interfaces
export interface CardExpandedEvent {
  id: string;
  entityId: string;
  expanded: boolean;
}

export interface MapMarkerClickedEvent {
  entityId: string;
  lat: number;
  lng: number;
}

export interface OpenLocationPanelEvent {
  city: any; // Entity or city object
}

export interface EntitySelectedEvent {
  entityId: string;
  moduleId?: string;
}

export interface PanelOpenedEvent {
  entityId: string;
}

export interface CardDeletedEvent {
  id: string;
}

export interface BudgetChangedEvent {
  budget: number;
  entityId?: string;
}

export interface DetailsViewedEvent {
  entityId: string;
}
