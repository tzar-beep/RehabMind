"use client";

import { ImagePlus, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { ApiError, apiFetch } from "@/lib/api/client";
import { PersonalWordSchema, type PersonalWord } from "@/lib/api/schemas";

/**
 * A patient's own words: photos of their people, pets and things, each with the word they
 * practise. Used by carers (family) and clinicians; `apiBase` is the matching endpoint.
 */
export function OwnWords({
  apiBase,
  patientName,
  words,
}: {
  apiBase: string;
  patientName: string;
  words: PersonalWord[];
}) {
  const router = useRouter();
  const fileId = useId();
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState<string | null>(null);

  useEffect(
    () => () => void (preview && URL.revokeObjectURL(preview)),
    [preview],
  );

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formEl = event.currentTarget;
    const data = new FormData(formEl);
    const photo = data.get("photo");
    if (!(photo instanceof File) || photo.size === 0) {
      setError("Choose a photo first.");
      return;
    }
    setBusy(true);
    setError(null);
    setAdded(null);
    try {
      const word = await apiFetch(
        apiBase,
        { method: "POST", body: data },
        PersonalWordSchema,
      );
      setAdded(word!.word);
      formEl.reset();
      setPreview(null);
      router.refresh();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "That didn't save. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function remove(word: PersonalWord) {
    await apiFetch(`${apiBase}/${word.id}`, { method: "DELETE" });
    router.refresh();
  }

  return (
    <div className="flex flex-col gap-5">
      {words.length > 0 ? (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {words.map((w) => (
            <li
              key={w.id}
              className="flex flex-col gap-2 rounded-card border border-line bg-surface p-3"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={w.image_url}
                alt=""
                className="aspect-square w-full rounded-control bg-canvas object-cover"
              />
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-lg font-bold">{w.word}</p>
                  {w.also_accepted.length > 0 && (
                    <p className="text-sm text-ink-muted">
                      Also: {w.also_accepted.join(", ")}
                    </p>
                  )}
                  {w.added_by && (
                    <p className="text-sm text-ink-muted">
                      Added by {w.added_by}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => remove(w)}
                  aria-label={`Remove ${w.word}`}
                  title="Remove (deletes the photo)"
                  className="inline-flex size-target shrink-0 items-center justify-center rounded-control text-ink-muted hover:bg-danger-soft hover:text-danger"
                >
                  <Trash2 aria-hidden="true" size={18} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-ink-muted">
          No own words yet. Photos of {patientName}&rsquo;s family, pets and
          things at home make practice personal.
        </p>
      )}

      <form
        onSubmit={add}
        className="grid gap-4 rounded-card border border-line bg-surface p-5 md:grid-cols-[auto_1fr]"
      >
        <label
          htmlFor={fileId}
          className="relative flex aspect-square w-40 cursor-pointer flex-col items-center justify-center gap-2 overflow-hidden rounded-card border-2 border-dashed border-line-strong bg-canvas text-ink-muted hover:border-accent hover:text-accent"
        >
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={preview}
              alt=""
              className="absolute inset-0 size-full object-cover"
            />
          ) : (
            <>
              <ImagePlus aria-hidden="true" size={32} />
              <span className="text-sm font-bold">Choose a photo</span>
            </>
          )}
          <input
            id={fileId}
            name="photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              setPreview(f ? URL.createObjectURL(f) : null);
            }}
          />
        </label>
        <div className="flex flex-col gap-3">
          <p className="font-bold">Add a word</p>
          <TextField
            label="The word to practise"
            hint="A name or a thing, as they would say it: “Priya”, “Rex”, “my garden”."
            name="word"
            autoComplete="off"
            maxLength={40}
            required
          />
          <TextField
            label="Other ways to say it (optional)"
            hint="Separate with commas: “my daughter, Pri”."
            name="also"
            autoComplete="off"
            maxLength={200}
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" busy={busy}>
              Add word
            </Button>
            <span className="text-sm text-ink-muted">
              The photo is kept private: only {patientName}, their family and
              their care team can see it. Location data is removed.
            </span>
          </div>
          {error && <Alert tone="error">{error}</Alert>}
          {added && (
            <Alert tone="success">
              “{added}” was added. It will appear in {patientName}&rsquo;s
              practice.
            </Alert>
          )}
        </div>
      </form>
    </div>
  );
}
