import { useEffect } from 'react';

interface KeyboardShortcuts {
  onNumberKey?: (num: number) => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  onSpace?: () => void;
  onEnter?: () => void;
  enabled?: boolean;
}

export function useKeyboardShortcuts({
  onNumberKey,
  onArrowLeft,
  onArrowRight,
  onSpace,
  onEnter,
  enabled = true,
}: KeyboardShortcuts) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts if user is typing in an input/textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Number keys 1-4 for option selection
      if (onNumberKey && e.key >= '1' && e.key <= '4') {
        const num = parseInt(e.key);
        e.preventDefault();
        onNumberKey(num);
      }

      // Arrow keys for navigation
      if (onArrowLeft && e.key === 'ArrowLeft') {
        e.preventDefault();
        onArrowLeft();
      }

      if (onArrowRight && e.key === 'ArrowRight') {
        e.preventDefault();
        onArrowRight();
      }

      // Spacebar
      if (onSpace && e.key === ' ') {
        e.preventDefault();
        onSpace();
      }

      // Enter key
      if (onEnter && e.key === 'Enter') {
        e.preventDefault();
        onEnter();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onNumberKey, onArrowLeft, onArrowRight, onSpace, onEnter, enabled]);
}
