/**
 * Behaviors for the pure key mapping (plan 010, Keyboard):
 * - digits 1 to 9 map to index 0 to 8 (a bank tile or an option); 0 and other
 *   keys map to nothing
 * - Backspace unpicks; Enter is claimed and prevented
 * - nothing is claimed with Ctrl, Meta, Alt or Shift held, while an IME is
 *   composing, in an editable target, inside a dialog, or while a sheet is
 *   open; a held Enter (repeat) is ignored
 * - Enter on a focused button or link is left to native activation, except a
 *   focused radio option that is already chosen (aria-checked="true"), where
 *   Enter is claimed so it checks; on an unchosen option native activation
 *   chooses it first
 */
import { describe, expect, it } from "vitest";
import { shortcutFor, type KeyInput } from "./shortcuts";

const CLOSED = { sheetOpen: false };

function key(k: string, extra: Partial<KeyInput> = {}): KeyInput {
  return {
    key: k,
    ctrlKey: false,
    metaKey: false,
    altKey: false,
    shiftKey: false,
    isComposing: false,
    repeat: false,
    target: document.body,
    ...extra,
  };
}

function el(html: string, selector: string): Element {
  const host = document.createElement("div");
  host.innerHTML = html;
  document.body.appendChild(host);
  const found = host.querySelector(selector);
  if (!found) throw new Error(selector);
  return found;
}

describe("shortcutFor", () => {
  it("maps digits 1 to 9 to indexes 0 to 8", () => {
    expect(shortcutFor(key("1"), CLOSED)).toEqual({ action: "pick", index: 0, preventDefault: false });
    expect(shortcutFor(key("5"), CLOSED)).toEqual({ action: "pick", index: 4, preventDefault: false });
    expect(shortcutFor(key("9"), CLOSED)).toEqual({ action: "pick", index: 8, preventDefault: false });
  });

  it("maps 0 and other keys to nothing", () => {
    expect(shortcutFor(key("0"), CLOSED)).toBeNull();
    expect(shortcutFor(key("a"), CLOSED)).toBeNull();
    expect(shortcutFor(key("Escape"), CLOSED)).toBeNull();
    expect(shortcutFor(key(" "), CLOSED)).toBeNull();
  });

  it("maps Backspace to unpick and Enter to enter, both prevented", () => {
    expect(shortcutFor(key("Backspace"), CLOSED)).toEqual({ action: "unpick", preventDefault: true });
    expect(shortcutFor(key("Enter"), CLOSED)).toEqual({ action: "enter", preventDefault: true });
  });

  it.each(["ctrlKey", "metaKey", "altKey", "shiftKey"] as const)("ignores keys with %s held", (modifier) => {
    for (const k of ["1", "Backspace", "Enter"]) expect(shortcutFor(key(k, { [modifier]: true }), CLOSED)).toBeNull();
  });

  it("ignores keys while an IME is composing", () => {
    expect(shortcutFor(key("Enter", { isComposing: true }), CLOSED)).toBeNull();
    expect(shortcutFor(key("1", { isComposing: true }), CLOSED)).toBeNull();
  });

  it("ignores a held Enter", () => {
    expect(shortcutFor(key("Enter", { repeat: true }), CLOSED)).toBeNull();
  });

  it("ignores editable targets", () => {
    for (const [html, sel] of [
      ["<input>", "input"],
      ["<textarea></textarea>", "textarea"],
      ["<select><option>a</option></select>", "select"],
      ['<div contenteditable="true"><span>x</span></div>', "span"],
    ]) {
      expect(shortcutFor(key("1", { target: el(html, sel) }), CLOSED)).toBeNull();
      expect(shortcutFor(key("Backspace", { target: el(html, sel) }), CLOSED)).toBeNull();
    }
  });

  it("ignores targets inside a dialog", () => {
    const target = el('<div role="dialog"><button>x</button></div>', "button");
    expect(shortcutFor(key("1", { target }), CLOSED)).toBeNull();
    expect(shortcutFor(key("Enter", { target: el('<div role="dialog"><p>x</p></div>', "p") }), CLOSED)).toBeNull();
  });

  it("ignores every key while a sheet is open", () => {
    const open = { sheetOpen: true };
    expect(shortcutFor(key("1"), open)).toBeNull();
    expect(shortcutFor(key("Backspace"), open)).toBeNull();
    expect(shortcutFor(key("Enter"), open)).toBeNull();
  });

  it("leaves Enter on a focused button or link to native activation", () => {
    expect(shortcutFor(key("Enter", { target: el("<button>Check</button>", "button") }), CLOSED)).toBeNull();
    expect(shortcutFor(key("Enter", { target: el('<a href="/">Close</a>', "a") }), CLOSED)).toBeNull();
  });

  it("claims and prevents Enter on the focused, chosen radio option", () => {
    const target = el('<button role="radio" aria-checked="true">A</button>', "button");
    expect(shortcutFor(key("Enter", { target }), CLOSED)).toEqual({ action: "enter", preventDefault: true });
  });

  it("leaves Enter on a focused, unchosen radio option to native activation", () => {
    const target = el('<button role="radio" aria-checked="false">B</button>', "button");
    expect(shortcutFor(key("Enter", { target }), CLOSED)).toBeNull();
  });

  it("still maps digits and Backspace when a button has focus", () => {
    const target = el("<button>Marami</button>", "button");
    expect(shortcutFor(key("2", { target }), CLOSED)).toEqual({ action: "pick", index: 1, preventDefault: false });
    expect(shortcutFor(key("Backspace", { target }), CLOSED)).toEqual({ action: "unpick", preventDefault: true });
  });

  it("treats a null target like the page", () => {
    expect(shortcutFor(key("Enter", { target: null }), CLOSED)).toEqual({ action: "enter", preventDefault: true });
  });
});
