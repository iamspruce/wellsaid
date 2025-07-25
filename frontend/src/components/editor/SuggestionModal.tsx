import React from "react";
import type { SuggestionModalProps } from "@/types";
import { X } from "lucide-react";

// Labels per suggestion type
const typeLabels: Record<"grammar" | "inclusive" | "synonym", string> = {
  grammar: "Grammar",
  inclusive: "Inclusive Language",
  synonym: "Synonym",
};

// Use CSS vars defined in your theme (for light/dark mode compatibility)
const typeColors: Record<"grammar" | "inclusive" | "synonym", string> = {
  grammar: "bg-[var(--color-muted)] text-[var(--color-primary)]",
  inclusive: "bg-[var(--color-muted)] text-[var(--color-primary)]",
  synonym: "bg-[var(--color-muted)] text-[var(--color-primary)]",
};

export const SuggestionModal: React.FC<SuggestionModalProps> = ({
  message = "No message available",
  suggestions = [],
  range,
  position,
  type,
  types = [type],
  messages = [message],
  onClose,
  onApply,
}) => {
  const grouped: Record<string, { message: string; suggestions: string[] }> =
    {};

  types.forEach((t, i) => {
    if (!grouped[t]) {
      grouped[t] = { message: messages[i] || "No message", suggestions: [] };
    }
  });

  suggestions.forEach((sugg) => {
    types.forEach((t) => {
      if (!grouped[t].suggestions.includes(sugg)) {
        grouped[t].suggestions.push(sugg);
      }
    });
  });

  return (
    <div
      className="fixed inset-0 z-50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="absolute bg-muted text-[var(--color-foreground)] border border-[var(--color-muted)] rounded-lg shadow-2xl p-4 max-w-sm w-full z-[1000] animate-fade-in"
        style={{ top: position.top, left: position.left }}
      >
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-base font-semibold text-foreground">
            Suggestions
          </h3>
          <button
            onClick={onClose}
            className="text-muted hover:text-foreground"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
          {Object.entries(grouped).map(
            ([typeKey, { message, suggestions }]) => (
              <div key={typeKey} className="flex flex-col gap-1">
                <span
                  className={`text-xs font-medium inline-block px-2 py-1 rounded-full w-fit ${
                    typeColors[typeKey as keyof typeof typeColors]
                  }`}
                >
                  {typeLabels[typeKey as keyof typeof typeLabels] || typeKey}
                </span>
                <p className="text-sm text-muted-foreground">{message}</p>
                {suggestions.length > 0 ? (
                  <ul className="pl-2 mt-1 space-y-1">
                    {suggestions.map((sugg, i) => (
                      <li
                        key={`${typeKey}-${sugg}-${i}`}
                        onClick={() => onApply(sugg, range)}
                        className="cursor-pointer text-sm text-primary hover:underline"
                      >
                        {sugg}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm italic text-muted pl-2">
                    No suggestions available
                  </p>
                )}
              </div>
            )
          )}
        </div>

        <button
          onClick={onClose}
          className="mt-4 w-full text-sm bg-muted px-4 py-2 rounded hover:bg-muted-foreground"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default SuggestionModal;
