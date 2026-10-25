"use client";

import { useSyncExternalStore } from "react";

const subscribe = () => () => {};
const canSpeak = () =>
  typeof window !== "undefined" && "speechSynthesis" in window;

/** Whether this device can read words aloud (false during server rendering). */
export function useCanSpeak(): boolean {
  return useSyncExternalStore(subscribe, canSpeak, () => false);
}

/** Reads text aloud with the device's own voice (nothing leaves the device). */
export function say(text: string, rate = 0.8) {
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-GB";
  u.rate = rate; // a little slower than conversation
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}
