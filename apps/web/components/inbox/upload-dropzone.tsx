"use client";

import { Camera, UploadCloud, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { uploadDocument } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatBytes } from "@/lib/format";

const ACCEPT = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
const MAX_BYTES = 50 * 1024 * 1024;

interface QueueItem {
  id: string;
  file: File;
  channel: "web_upload" | "mobile_capture";
  progress: number;
  status: "queued" | "uploading" | "done" | "error";
  error?: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onUploaded?: () => void;
}

export function UploadDropzone({ open, onClose, onUploaded }: Props) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);
  const cameraInput = useRef<HTMLInputElement | null>(null);

  const run = useCallback(
    async (items: QueueItem[]) => {
      let success = 0;
      for (const item of items) {
        if (item.status !== "queued") continue;
        setQueue((q) =>
          q.map((it) => (it.id === item.id ? { ...it, status: "uploading" } : it)),
        );
        try {
          await maybeCompress(item.file);
          await uploadDocument(item.file, item.channel, (pct) => {
            setQueue((q) =>
              q.map((it) =>
                it.id === item.id ? { ...it, progress: pct } : it,
              ),
            );
          });
          setQueue((q) =>
            q.map((it) =>
              it.id === item.id
                ? { ...it, status: "done", progress: 100 }
                : it,
            ),
          );
          success += 1;
        } catch (e: unknown) {
          setQueue((q) =>
            q.map((it) =>
              it.id === item.id
                ? {
                    ...it,
                    status: "error",
                    error: e instanceof Error ? e.message : "upload failed",
                  }
                : it,
            ),
          );
        }
      }
      if (success > 0) onUploaded?.();
    },
    [onUploaded],
  );

  const enqueue = useCallback(
    (files: FileList | File[], channel: "web_upload" | "mobile_capture") => {
      const next: QueueItem[] = [];
      for (const f of Array.from(files)) {
        if (!ACCEPT.includes(f.type)) {
          next.push({
            id: crypto.randomUUID(),
            file: f,
            channel,
            progress: 0,
            status: "error",
            error: "unsupported file type",
          });
          continue;
        }
        if (f.size > MAX_BYTES) {
          next.push({
            id: crypto.randomUUID(),
            file: f,
            channel,
            progress: 0,
            status: "error",
            error: `exceeds ${formatBytes(MAX_BYTES)}`,
          });
          continue;
        }
        next.push({
          id: crypto.randomUUID(),
          file: f,
          channel,
          progress: 0,
          status: "queued",
        });
      }
      setQueue((q) => [...q, ...next]);
      void run(next);
    },
    [run],
  );

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) enqueue(e.dataTransfer.files, "web_upload");
  };

  return (
    <Dialog open={open} onClose={onClose} title="Upload notices" className="max-w-xl">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          dragOver ? "border-navy bg-navy-50" : "border-slate-300 bg-slate-50",
        )}
      >
        <UploadCloud className="h-8 w-8 text-slate-500" aria-hidden />
        <p className="text-sm text-slate-700">
          Drop PDF or image files here, or pick them
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <Button
            type="button"
            size="sm"
            onClick={() => fileInput.current?.click()}
          >
            Choose files
          </Button>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={() => cameraInput.current?.click()}
          >
            <Camera className="mr-1 h-4 w-4" aria-hidden /> Use camera
          </Button>
        </div>
        <p className="text-xs text-slate-500">Max {formatBytes(MAX_BYTES)} per file.</p>
      </div>
      <input
        ref={fileInput}
        type="file"
        accept={ACCEPT.join(",")}
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files) enqueue(e.target.files, "web_upload");
          e.target.value = "";
        }}
      />
      {/* `capture="environment"` opens the rear camera on iOS Safari + Android Chrome. */}
      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          if (e.target.files) enqueue(e.target.files, "mobile_capture");
          e.target.value = "";
        }}
      />

      {queue.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {queue.map((it) => (
            <li
              key={it.id}
              className="flex items-center justify-between gap-3 rounded border border-slate-200 px-3 py-2 text-sm"
            >
              <div className="min-w-0">
                <p className="truncate text-navy">{it.file.name}</p>
                <p className="text-xs text-slate-500">
                  {formatBytes(it.file.size)}
                  {it.status === "error" && it.error ? ` · ${it.error}` : null}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {it.status === "uploading" ? (
                  <div className="h-1.5 w-24 overflow-hidden rounded bg-slate-200">
                    <div
                      className="h-full bg-navy transition-all"
                      style={{ width: `${it.progress}%` }}
                    />
                  </div>
                ) : null}
                <span
                  className={cn(
                    "text-xs",
                    it.status === "done" && "text-emerald-700",
                    it.status === "error" && "text-red-700",
                  )}
                >
                  {it.status}
                </span>
                <button
                  type="button"
                  onClick={() => setQueue((q) => q.filter((x) => x.id !== it.id))}
                  className="text-slate-400 hover:text-navy"
                  aria-label="Remove"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </Dialog>
  );
}

async function maybeCompress(file: File): Promise<File> {
  // Only compress images, leave PDFs alone.
  if (!file.type.startsWith("image/")) return file;
  if (typeof window === "undefined") return file;
  try {
    const { default: imageCompression } = await import("browser-image-compression");
    return await imageCompression(file, {
      maxSizeMB: 4,
      maxWidthOrHeight: 2400,
      useWebWorker: true,
      preserveExif: false,
    });
  } catch {
    // If the lib isn't available, skip compression silently.
    return file;
  }
}
