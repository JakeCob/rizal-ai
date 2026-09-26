"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import { shortcutFor } from "@/lib/runner/shortcuts";

export type ShortcutHandlers = {
  onPick?: (index: number) => void;
  onUnpick?: () => void;
  onEnter?: () => void;
};

/**
 * One window keydown listener for the life of the component, calling the
 * latest handlers (kept in a ref so the listener never re-attaches). A key
 * whose action has no handler here is left alone, so several components can
 * each take the keys they own. Never moves focus.
 */
export function useShortcuts(handlers: ShortcutHandlers) {
  const latest = useRef(handlers);
  useLayoutEffect(() => {
    latest.current = handlers;
  });

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const sheetOpen = document.querySelector('[data-slot="sheet-content"][data-open]') !== null;
      const shortcut = shortcutFor(event, { sheetOpen });
      if (!shortcut) return;
      const { onPick, onUnpick, onEnter } = latest.current;
      if (shortcut.action === "pick" && onPick) onPick(shortcut.index);
      else if (shortcut.action === "unpick" && onUnpick) onUnpick();
      else if (shortcut.action === "enter" && onEnter) onEnter();
      else return;
      if (shortcut.preventDefault) event.preventDefault();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}
