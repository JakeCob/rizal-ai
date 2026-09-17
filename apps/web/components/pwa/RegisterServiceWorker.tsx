"use client";

import { useEffect } from "react";

/** Registers the app-shell service worker in production builds only. */
export function RegisterServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch(() => {
      /* The app works without the shell cache. */
    });
  }, []);
  return null;
}
