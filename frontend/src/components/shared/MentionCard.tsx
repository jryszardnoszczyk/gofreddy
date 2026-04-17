import { ExternalLink } from "lucide-react";
import { cn } from "@/lib/cn";
import type { MentionItem } from "@/lib/api";

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

interface MentionCardProps {
  mention: MentionItem;
  selectable?: boolean;
  selected?: boolean;
  onSelect?: () => void;
}

export function MentionCard({ mention, selectable, selected, onSelect }: MentionCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border-subtle bg-surface p-3",
        selectable && "cursor-pointer hover:border-zinc-600",
        selected && "border-brand-500 bg-brand-500/5",
      )}
      onClick={selectable ? onSelect : undefined}
    >
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        {selectable && (
          <input
            type="checkbox"
            checked={selected ?? false}
            onChange={() => {}}
            className="h-3.5 w-3.5 rounded border-zinc-600 bg-surface-raised text-brand-500 focus:ring-brand-500"
          />
        )}
        <span className="rounded bg-zinc-800 px-1.5 py-0.5">{mention.source}</span>
        {mention.author_handle && <span>@{mention.author_handle}</span>}
        {mention.published_at && <span>{new Date(mention.published_at).toLocaleDateString()}</span>}
        {mention.sentiment_label && (
          <span className={cn(
            "rounded px-1.5 py-0.5",
            mention.sentiment_label === "positive" ? "bg-emerald-900/30 text-emerald-400" :
            mention.sentiment_label === "negative" ? "bg-red-900/30 text-red-400" :
            "bg-zinc-800 text-zinc-400"
          )}>
            {mention.sentiment_label}
          </span>
        )}
        {mention.intent && (
          <span className="rounded bg-blue-900/30 px-1.5 py-0.5 text-blue-400">
            {mention.intent}
          </span>
        )}
      </div>
      <p className="mt-2 text-sm text-zinc-300 line-clamp-3">{mention.content}</p>
      <div className="mt-2 flex items-center gap-3 text-xs text-zinc-600">
        {mention.engagement_total != null && mention.engagement_total > 0 && (
          <span>{mention.engagement_total.toLocaleString()} engagement</span>
        )}
        {mention.url && isValidUrl(mention.url) && (
          <a
            href={mention.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-brand-400 hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="h-3 w-3" />
            Source
          </a>
        )}
      </div>
    </div>
  );
}
