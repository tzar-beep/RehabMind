"use client";

import { Check, MessageCircleHeart } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import { MessageSchema, type Message } from "@/lib/api/schemas";
import { formatDateTime } from "@/lib/format";

/** A short note the patient sees on their home page. Encouragement, not a chat. */
export function SendNote({
  patientId,
  name,
  sent,
}: {
  patientId: string;
  name: string;
  sent: Message[];
}) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await apiFetch(
        `/carer/patients/${patientId}/messages`,
        { method: "POST", json: { text } },
        MessageSchema,
      );
      setText("");
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "That didn't send.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={send} className="flex flex-col gap-2">
        <label htmlFor="note" className="font-bold">
          A note for {name}
        </label>
        <textarea
          id="note"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={200}
          rows={2}
          placeholder="So proud of you this week!"
          className="rounded-control border-2 border-line-strong bg-surface p-3 text-lg"
        />
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-ink-muted tabular-nums">
            {text.length}/200 · short and warm works best
          </span>
          <Button type="submit" busy={busy} disabled={!text.trim()}>
            <MessageCircleHeart aria-hidden="true" size={18} />
            Send
          </Button>
        </div>
        {error && <Alert tone="error">{error}</Alert>}
      </form>
      {sent.length > 0 && (
        <ul className="flex flex-col gap-2">
          {sent.slice(0, 3).map((m) => (
            <li
              key={m.id}
              className="flex items-start justify-between gap-3 text-sm"
            >
              <span>“{m.text}”</span>
              <span className="flex shrink-0 items-center gap-1 text-ink-muted">
                {m.seen && <Check aria-hidden="true" size={14} />}
                {m.seen ? "Seen" : formatDateTime(m.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
