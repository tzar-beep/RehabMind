"use client";

import { Check, Volume2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  SpeechAcceptedSchema,
  SpeechStatusSchema,
  type ResponseResult,
} from "@/lib/api/schemas";

import { say, useCanSpeak } from "./Choices";

const MAX_SECONDS = 15;
const POLL_MS = 700;
const POLL_LIMIT_MS = 60_000;
const MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/ogg;codecs=opus",
  "audio/mp4",
];

type Phase =
  | { kind: "idle" }
  | { kind: "recording"; seconds: number }
  | { kind: "processing" }
  | { kind: "confirm"; heard: string; recordingId: string }
  | { kind: "retry"; message: string };

const TRY_AGAIN = "That didn’t work. Please try again, or type your answer.";

export function speechSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof MediaRecorder !== "undefined" &&
    !!navigator.mediaDevices?.getUserMedia
  );
}

function MicIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="40"
      height="40"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

/**
 * Large, single-purpose recording control. Audio goes straight to the server and is
 * never stored in the browser beyond the current recording.
 */
export function SpeechRecorder({
  exerciseId,
  hintsUsed,
  latencyMs,
  onResult,
  onUnavailable,
}: {
  exerciseId: string;
  hintsUsed: number;
  latencyMs: () => number;
  onResult: (result: ResponseResult) => void;
  onUnavailable: (message: string) => void;
}) {
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const speakable = useCanSpeak();
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const latency = useRef(0);

  useEffect(
    () => () => {
      if (timer.current) clearInterval(timer.current);
      recorder.current?.stream.getTracks().forEach((t) => t.stop());
    },
    [],
  );

  async function start() {
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onUnavailable(
        "The microphone isn’t available. You can type your answer instead.",
      );
      return;
    }
    latency.current = latencyMs();
    const mimeType = MIME_TYPES.find((t) => MediaRecorder.isTypeSupported(t));
    const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    chunks.current = [];
    rec.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunks.current, {
        type: rec.mimeType || "audio/webm",
      });
      chunks.current = [];
      void send(blob);
    };
    recorder.current = rec;
    rec.start();
    setPhase({ kind: "recording", seconds: 0 });
    timer.current = setInterval(() => {
      setPhase((p) => {
        if (p.kind !== "recording") return p;
        if (p.seconds + 1 >= MAX_SECONDS) stop();
        return { kind: "recording", seconds: p.seconds + 1 };
      });
    }, 1000);
  }

  function stop() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    if (recorder.current?.state === "recording") recorder.current.stop();
    setPhase({ kind: "processing" });
  }

  async function send(blob: Blob) {
    const form = new FormData();
    form.append("audio", blob, "answer");
    form.append("latency_ms", String(Math.round(latency.current)));
    form.append("hints_used", String(hintsUsed));
    try {
      const accepted = await apiFetch(
        `/practice/exercises/${exerciseId}/speech`,
        { method: "POST", body: form },
        SpeechAcceptedSchema,
      );
      const deadline = Date.now() + POLL_LIMIT_MS;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, POLL_MS));
        const s = await apiFetch(
          `/practice/speech/${accepted!.recording_id}`,
          {},
          SpeechStatusSchema,
        );
        if (s!.status === "done" && s!.result) return onResult(s!.result);
        if (s!.status === "confirm" && s!.heard)
          return setPhase({
            kind: "confirm",
            heard: s!.heard,
            recordingId: accepted!.recording_id,
          });
        if (s!.status === "no_speech")
          return setPhase({
            kind: "retry",
            message: "I didn’t catch that. Try again, or type your answer.",
          });
        if (s!.status === "failed") break;
      }
      setPhase({ kind: "retry", message: TRY_AGAIN });
    } catch (e) {
      setPhase({
        kind: "retry",
        message:
          e instanceof ApiError && e.status !== 500 ? e.message : TRY_AGAIN,
      });
    }
  }

  /** "Is that what you said?" Speech recognisers tend to hear the expected word, so a
   * match only counts once the patient agrees with it. */
  async function answer(recordingId: string, saidIt: boolean) {
    setPhase({ kind: "processing" });
    try {
      const s = await apiFetch(
        `/practice/speech/${recordingId}/confirm`,
        { method: "POST", json: { said_it: saidIt } },
        SpeechStatusSchema,
      );
      if (s!.status === "done" && s!.result) return onResult(s!.result);
      setPhase({
        kind: "retry",
        message: saidIt
          ? TRY_AGAIN
          : "Thanks for telling me. Try again, or type your answer.",
      });
    } catch (e) {
      setPhase({
        kind: "retry",
        message:
          e instanceof ApiError && e.status !== 500 ? e.message : TRY_AGAIN,
      });
    }
  }

  if (phase.kind === "confirm") {
    return (
      <div
        role="group"
        aria-labelledby="heard-question"
        className="flex flex-col items-center gap-4 lg:items-start"
      >
        <p id="heard-question" className="text-xl">
          I heard{" "}
          <span lang="en" className="text-3xl font-bold">
            “{phase.heard}”
          </span>
          . Is that what you said?
        </p>
        {speakable && (
          <button
            type="button"
            onClick={() => say(phase.heard)}
            className="inline-flex min-h-target items-center gap-2 rounded-control border-2 border-accent px-4 font-bold text-accent transition-colors hover:bg-accent-soft"
          >
            <Volume2 aria-hidden="true" size={22} />
            Hear it
          </button>
        )}
        <div className="flex flex-wrap gap-3">
          <Button size="lg" onClick={() => answer(phase.recordingId, true)}>
            <Check aria-hidden="true" size={24} />
            Yes
          </Button>
          <Button
            size="lg"
            variant="secondary"
            onClick={() => answer(phase.recordingId, false)}
          >
            <X aria-hidden="true" size={24} />
            No, try again
          </Button>
        </div>
      </div>
    );
  }

  if (phase.kind === "processing") {
    return (
      <p role="status" className="py-6 text-center text-xl text-ink-muted">
        Checking your answer…
      </p>
    );
  }

  if (phase.kind === "recording") {
    return (
      <div className="flex flex-col items-center gap-4 lg:items-start">
        <p role="status" className="text-xl font-bold">
          Listening…{" "}
          <span className="tabular-nums">
            0:{String(phase.seconds).padStart(2, "0")}
          </span>
        </p>
        <button
          type="button"
          onClick={stop}
          className="flex size-28 items-center justify-center rounded-full bg-danger text-white ring-8 ring-danger-soft motion-safe:animate-pulse"
        >
          <span className="text-xl font-bold">
            Stop<span className="sr-only"> recording</span>
          </span>
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 lg:items-start">
      {phase.kind === "retry" && <Alert tone="warning">{phase.message}</Alert>}
      <button
        type="button"
        onClick={start}
        className="flex size-28 flex-col items-center justify-center gap-1 rounded-full bg-accent text-white hover:bg-accent-hover"
      >
        <MicIcon />
        <span className="sr-only">Start speaking</span>
      </button>
      <p className="text-lg font-bold" aria-hidden="true">
        Tap to speak
      </p>
    </div>
  );
}
