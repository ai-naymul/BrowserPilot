/**
 * Keyboard Navigation Hook
 *
 * Provides keyboard shortcuts for direct manipulation:
 * - Arrow keys: Move selection between entities
 * - E: Expand/collapse selected card
 * - C: Compare (when 2+ entities selected)
 * - Cmd/Ctrl+Z: Undo
 * - Cmd/Ctrl+Shift+Z: Redo
 *
 * Usage:
 * ```ts
 * useKeyboardNav({
 *   entities,
 *   onSelectEntity,
 *   onCompare,
 * });
 * ```
 */

import { useEffect } from 'react';
import { useUIContext } from '@/contexts/UIContext';
import { bus } from '@/utils/eventBus';
import { undo, redo } from '@/utils/commandHistory';

interface UseKeyboardNavProps {
  entities?: any[];
  enabled?: boolean;
}

export function useKeyboardNav({ entities = [], enabled = true }: UseKeyboardNavProps = {}) {
  const { selectedEntityId, selectedEntityIds, setSelected, toggleMultiSelect } = useUIContext();

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Cmd/Ctrl + Z = Undo
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        const success = undo();
        if (success) {
          console.log('[Keyboard] Undo performed');
        }
        return;
      }

      // Cmd/Ctrl + Shift + Z = Redo
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        const success = redo();
        if (success) {
          console.log('[Keyboard] Redo performed');
        }
        return;
      }

      // Arrow keys: Navigate between entities
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.preventDefault();

        if (entities.length === 0) return;

        const currentIndex = selectedEntityId
          ? entities.findIndex(e => e.id === selectedEntityId)
          : -1;

        let nextIndex = currentIndex;

        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
          nextIndex = (currentIndex + 1) % entities.length;
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
          nextIndex = currentIndex <= 0 ? entities.length - 1 : currentIndex - 1;
        }

        if (nextIndex >= 0 && nextIndex < entities.length) {
          const entity = entities[nextIndex];
          setSelected(entity.id, `metric_card_${entity.id}`);
          console.log('[Keyboard] Selected:', entity.public_identifier || entity.id);
        }
        return;
      }

      // E: Expand/collapse selected card
      if (e.key === 'e' || e.key === 'E') {
        e.preventDefault();

        if (selectedEntityId) {
          bus.emit('CARD_EXPAND_REQUESTED', { entityId: selectedEntityId });
          console.log('[Keyboard] Toggle expand for:', selectedEntityId);
        }
        return;
      }

      // C: Compare selected entities
      if (e.key === 'c' || e.key === 'C') {
        e.preventDefault();

        if (selectedEntityIds.length >= 2) {
          bus.emit('COMPARE_REQUESTED', { entityIds: selectedEntityIds });
          console.log('[Keyboard] Compare requested for:', selectedEntityIds);
        } else {
          console.log('[Keyboard] Need 2+ entities selected for comparison');
        }
        return;
      }

      // Space: Toggle multi-select
      if (e.key === ' ' && selectedEntityId) {
        e.preventDefault();
        toggleMultiSelect(selectedEntityId);
        console.log('[Keyboard] Toggled multi-select for:', selectedEntityId);
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, entities, selectedEntityId, selectedEntityIds, setSelected, toggleMultiSelect]);
}
