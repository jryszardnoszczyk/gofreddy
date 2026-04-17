import { useEffect, useCallback, useRef } from "react";
import { X } from "lucide-react";

interface VideoLightboxProps {
  url: string;
  open: boolean;
  onClose: () => void;
}

export function VideoLightbox({ url, open, onClose }: VideoLightboxProps) {
  const backdropRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <button
        onClick={onClose}
        className="absolute top-4 right-4 rounded-full bg-zinc-800/80 p-2 text-zinc-300 transition-colors hover:bg-zinc-700 hover:text-white"
        aria-label="Close"
      >
        <X className="h-5 w-5" />
      </button>
      <video
        controls
        autoPlay
        src={url}
        className="max-h-[85vh] max-w-[90vw] rounded-lg bg-black"
        preload="metadata"
      >
        <track kind="captions" />
      </video>
    </div>
  );
}

interface ImageLightboxProps {
  url: string;
  open: boolean;
  onClose: () => void;
  alt?: string;
}

export function ImageLightbox({ url, open, onClose, alt }: ImageLightboxProps) {
  const backdropRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <button
        onClick={onClose}
        className="absolute top-4 right-4 rounded-full bg-zinc-800/80 p-2 text-zinc-300 transition-colors hover:bg-zinc-700 hover:text-white"
        aria-label="Close"
      >
        <X className="h-5 w-5" />
      </button>
      <img
        src={url}
        alt={alt ?? "Preview"}
        className="max-h-[85vh] max-w-[90vw] rounded-lg object-contain"
        referrerPolicy="no-referrer"
      />
    </div>
  );
}
