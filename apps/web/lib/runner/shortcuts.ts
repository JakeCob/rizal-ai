/**
 * Keyboard shortcuts for the runner and practice (plan 010): digits 1 to 9
 * pick a bank tile or an option by position, Backspace removes the last
 * picked tile, Enter checks or continues. This is the pure mapping from a
 * key event to an action; components/runner/useShortcuts.ts wires it to the
 * window. The listeners stay on at every width (a phone with a keyboard gets
 * them too); only the hint is desktop.
 */

export type KeyInput = {
  key: string;
  ctrlKey: boolean;
  metaKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
  isComposing: boolean;
  repeat: boolean;
  target: EventTarget | null;
};

export type ShortcutContext = {
  /** A bottom sheet (the word gloss) is open: it owns the keyboard. */
  sheetOpen: boolean;
};

export type Shortcut =
  | { action: "pick"; index: number; preventDefault: false }
  | { action: "unpick"; preventDefault: true }
  | { action: "enter"; preventDefault: true };

const EDITABLE = 'input, textarea, select, [contenteditable=""], [contenteditable="true"]';

export function shortcutFor(event: KeyInput, ctx: ShortcutContext): Shortcut | null {
  if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey || event.isComposing) return null;
  if (ctx.sheetOpen) return null;
  const target = event.target instanceof Element ? event.target : null;
  if (target?.closest(EDITABLE) || target?.closest('[role="dialog"]')) return null;

  if (/^[1-9]$/.test(event.key)) return { action: "pick", index: Number(event.key) - 1, preventDefault: false };
  if (event.key === "Backspace") return { action: "unpick", preventDefault: true };
  if (event.key === "Enter") {
    if (event.repeat) return null;
    // A focused button or link activates natively on Enter; claiming it too
    // would run the action twice (two attempts for one Check). A radio
    // option that is already chosen is the exception: Enter there means
    // Check, and preventing the default stops a redundant click. On an
    // option not yet chosen, native activation chooses it first, so Check
    // never grades a different option than the one in focus.
    const radio = target?.closest('[role="radio"]');
    if (radio) return radio.getAttribute("aria-checked") === "true" ? { action: "enter", preventDefault: true } : null;
    if (target?.closest("button, a[href]")) return null;
    return { action: "enter", preventDefault: true };
  }
  return null;
}
