/**
 * UI Context - Selection & Focus Management
 *
 * Provides global state for:
 * - Currently selected entity (noun)
 * - Currently focused module/card (for quick actions)
 * - Hover context (for contextual menus)
 *
 * This enables:
 * - Direct manipulation (click to select)
 * - Keyboard navigation (arrow keys move selection)
 * - Context-aware quick actions (based on what's selected/hovered)
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { bus } from '@/utils/eventBus';

interface UIContextState {
  // Selection state
  selectedEntityId: string | null;
  selectedModuleId: string | null;

  // Hover state
  hoveredModuleId: string | null;

  // Multi-select state (for comparison)
  selectedEntityIds: string[];

  // Panel state
  locationPanelCity: any | null;

  // Actions
  setSelected: (entityId: string | null, moduleId?: string | null) => void;
  setHovered: (moduleId: string | null) => void;
  toggleMultiSelect: (entityId: string) => void;
  clearMultiSelect: () => void;
  setLocationPanel: (city: any | null) => void;
}

const UIContext = createContext<UIContextState | undefined>(undefined);

export const UIProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null);
  const [hoveredModuleId, setHoveredModuleId] = useState<string | null>(null);
  const [selectedEntityIds, setSelectedEntityIds] = useState<string[]>([]);
  const [locationPanelCity, setLocationPanelCityState] = useState<any | null>(null);

  const setSelected = useCallback((entityId: string | null, moduleId: string | null = null) => {
    setSelectedEntityId(entityId);
    setSelectedModuleId(moduleId);

    // Emit event for other components to react
    if (entityId) {
      bus.emit('ENTITY_SELECTED', { entityId, moduleId: moduleId || undefined });
    }
  }, []);

  const setHovered = useCallback((moduleId: string | null) => {
    setHoveredModuleId(moduleId);
  }, []);

  const toggleMultiSelect = useCallback((entityId: string) => {
    setSelectedEntityIds((prev) => {
      if (prev.includes(entityId)) {
        return prev.filter((id) => id !== entityId);
      } else {
        return [...prev, entityId];
      }
    });
  }, []);

  const clearMultiSelect = useCallback(() => {
    setSelectedEntityIds([]);
  }, []);

  const setLocationPanel = useCallback((city: any | null) => {
    console.log('[UIContext] setLocationPanel called with:', city?.id || 'null', city);
    setLocationPanelCityState(city);
    if (city) {
      bus.emit('OPEN_LOCATION_PANEL', { city });
    }
  }, []);

  const value: UIContextState = {
    selectedEntityId,
    selectedModuleId,
    hoveredModuleId,
    selectedEntityIds,
    locationPanelCity,
    setSelected,
    setHovered,
    toggleMultiSelect,
    clearMultiSelect,
    setLocationPanel,
  };

  return <UIContext.Provider value={value}>{children}</UIContext.Provider>;
};

export const useUIContext = (): UIContextState => {
  const context = useContext(UIContext);
  if (!context) {
    // Return safe defaults when not wrapped in UIProvider (for backward compatibility)
    return {
      selectedEntityId: null,
      selectedModuleId: null,
      hoveredModuleId: null,
      selectedEntityIds: [],
      locationPanelCity: null,
      setSelected: () => {},
      setHovered: () => {},
      toggleMultiSelect: () => {},
      clearMultiSelect: () => {},
      setLocationPanel: () => {},
    };
  }
  return context;
};
