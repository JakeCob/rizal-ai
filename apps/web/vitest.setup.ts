import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// jsdom does not implement scrolling: window.scrollTo only logs "not
// implemented" and Element.scrollIntoView is missing. The runner scrolls on
// every beat and exercise (tech debt 25), so give both a silent no-op; tests
// that assert on scrolling install their own spies.
window.scrollTo = (() => undefined) as typeof window.scrollTo;
if (typeof Element.prototype.scrollIntoView !== "function") {
  Element.prototype.scrollIntoView = () => undefined;
}

afterEach(() => {
  cleanup();
});
