/**
 * Behaviors for the keyboard hook:
 * - it attaches one keydown listener on window and detaches it on unmount
 * - a key calls the latest handler passed, not the first
 * - a key with no handler for its action is left alone (not prevented)
 * - an open sheet blocks every key
 * - a claimed Enter is prevented, so a focused, chosen radio does not also click
 */
import { fireEvent, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useShortcuts } from "./useShortcuts";

afterEach(() => {
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("useShortcuts", () => {
  it("attaches one window listener and detaches it on unmount", () => {
    const add = vi.spyOn(window, "addEventListener");
    const remove = vi.spyOn(window, "removeEventListener");
    const { unmount, rerender } = renderHook((props: { onEnter: () => void }) => useShortcuts(props), {
      initialProps: { onEnter: vi.fn() },
    });
    rerender({ onEnter: vi.fn() });
    const keydowns = add.mock.calls.filter(([type]) => type === "keydown");
    expect(keydowns).toHaveLength(1);
    unmount();
    expect(remove).toHaveBeenCalledWith("keydown", keydowns[0][1]);
  });

  it("calls the latest handler", () => {
    const first = vi.fn();
    const second = vi.fn();
    const { rerender } = renderHook((props: { onPick: (i: number) => void }) => useShortcuts(props), {
      initialProps: { onPick: first },
    });
    rerender({ onPick: second });
    fireEvent.keyDown(window, { key: "3" });
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledWith(2);
  });

  it("routes Backspace and Enter and prevents them", () => {
    const onUnpick = vi.fn();
    const onEnter = vi.fn();
    renderHook(() => useShortcuts({ onUnpick, onEnter }));
    expect(fireEvent.keyDown(window, { key: "Backspace" })).toBe(false);
    expect(fireEvent.keyDown(window, { key: "Enter" })).toBe(false);
    expect(onUnpick).toHaveBeenCalledTimes(1);
    expect(onEnter).toHaveBeenCalledTimes(1);
  });

  it("leaves a key alone when no handler takes it", () => {
    const onPick = vi.fn();
    renderHook(() => useShortcuts({ onPick }));
    expect(fireEvent.keyDown(window, { key: "Enter" })).toBe(true);
    expect(onPick).not.toHaveBeenCalled();
  });

  it("does nothing while a sheet is open", () => {
    const onEnter = vi.fn();
    const onPick = vi.fn();
    renderHook(() => useShortcuts({ onEnter, onPick }));
    const sheet = document.createElement("div");
    sheet.setAttribute("data-slot", "sheet-content");
    sheet.setAttribute("data-open", "");
    document.body.appendChild(sheet);
    fireEvent.keyDown(window, { key: "Enter" });
    fireEvent.keyDown(window, { key: "1" });
    expect(onEnter).not.toHaveBeenCalled();
    expect(onPick).not.toHaveBeenCalled();
  });

  it("prevents a claimed Enter on a focused, chosen radio", () => {
    const onEnter = vi.fn();
    renderHook(() => useShortcuts({ onEnter }));
    const radio = document.createElement("button");
    radio.setAttribute("role", "radio");
    radio.setAttribute("aria-checked", "true");
    document.body.appendChild(radio);
    expect(fireEvent.keyDown(radio, { key: "Enter" })).toBe(false);
    expect(onEnter).toHaveBeenCalledTimes(1);
  });
});
