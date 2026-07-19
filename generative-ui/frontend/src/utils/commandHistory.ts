/**
 * Command History - Universal Undo/Redo System
 *
 * Implements the Command pattern for reversible actions.
 * Every user action becomes a Command that can be undone and redone.
 *
 * This satisfies Raskin's "modeless interface" principle by making
 * all actions safely reversible, encouraging exploration.
 *
 * Usage:
 * ```ts
 * import { run, undo, redo } from '@/utils/commandHistory';
 *
 * run({
 *   label: 'Expand Tokyo card',
 *   do: () => setExpanded(true),
 *   undo: () => setExpanded(false),
 * });
 * ```
 */

export interface Command {
  /**
   * Execute the command (forward action)
   */
  do: () => void;

  /**
   * Reverse the command (undo action)
   */
  undo: () => void;

  /**
   * Optional label for debugging/display
   */
  label?: string;

  /**
   * Optional timestamp
   */
  timestamp?: number;
}

class CommandHistory {
  private stack: Command[] = [];
  private index: number = -1;
  private maxSize: number = 50;

  /**
   * Execute a command and add it to history
   */
  run(command: Command): void {
    // Add timestamp
    const commandWithTime: Command = {
      ...command,
      timestamp: Date.now(),
    };

    // Execute the command
    try {
      commandWithTime.do();
    } catch (error) {
      console.error('[CommandHistory] Error executing command:', error);
      throw error;
    }

    // Remove any commands after current index (when running new command after undo)
    this.stack.splice(this.index + 1);

    // Add to stack
    this.stack.push(commandWithTime);
    this.index++;

    // Limit stack size
    if (this.stack.length > this.maxSize) {
      this.stack.shift();
      this.index--;
    }

    console.log(
      `[CommandHistory] Executed: "${commandWithTime.label || 'Unnamed'}" (${this.index + 1}/${
        this.stack.length
      })`
    );
  }

  /**
   * Undo the last command
   * @returns true if undo was successful, false if nothing to undo
   */
  undo(): boolean {
    if (this.index < 0) {
      console.log('[CommandHistory] Nothing to undo');
      return false;
    }

    const command = this.stack[this.index];

    try {
      command.undo();
      this.index--;
      console.log(
        `[CommandHistory] Undid: "${command.label || 'Unnamed'}" (${this.index + 1}/${
          this.stack.length
        })`
      );
      return true;
    } catch (error) {
      console.error('[CommandHistory] Error undoing command:', error);
      return false;
    }
  }

  /**
   * Redo the next command
   * @returns true if redo was successful, false if nothing to redo
   */
  redo(): boolean {
    if (this.index >= this.stack.length - 1) {
      console.log('[CommandHistory] Nothing to redo');
      return false;
    }

    this.index++;
    const command = this.stack[this.index];

    try {
      command.do();
      console.log(
        `[CommandHistory] Redid: "${command.label || 'Unnamed'}" (${this.index + 1}/${
          this.stack.length
        })`
      );
      return true;
    } catch (error) {
      console.error('[CommandHistory] Error redoing command:', error);
      this.index--;
      return false;
    }
  }

  /**
   * Get current history state (for debugging)
   */
  getState(): {
    canUndo: boolean;
    canRedo: boolean;
    currentIndex: number;
    stackSize: number;
    recentCommands: string[];
  } {
    return {
      canUndo: this.index >= 0,
      canRedo: this.index < this.stack.length - 1,
      currentIndex: this.index,
      stackSize: this.stack.length,
      recentCommands: this.stack
        .slice(Math.max(0, this.index - 2), this.index + 3)
        .map((cmd) => cmd.label || 'Unnamed'),
    };
  }

  /**
   * Clear command history
   */
  clear(): void {
    this.stack = [];
    this.index = -1;
    console.log('[CommandHistory] History cleared');
  }

  /**
   * Get command at specific index (for debugging)
   */
  getCommand(index: number): Command | undefined {
    return this.stack[index];
  }
}

// Export singleton instance
const history = new CommandHistory();

export const run = (command: Command): void => history.run(command);
export const undo = (): boolean => history.undo();
export const redo = (): boolean => history.redo();
export const getHistoryState = () => history.getState();
export const clearHistory = () => history.clear();

// Export class for testing
export { CommandHistory };
