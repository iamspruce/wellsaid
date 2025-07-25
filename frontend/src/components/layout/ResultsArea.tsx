// File: contentArea/ResultsArea.tsx
"use client";

import { useLocation } from "react-router-dom";
import ParaphraserResults from "../results/ParaphraserResults";
import GrammarResults from "../results/GrammarResults";
import type { AnalysisResultsData, DisplayIssue } from "@/types";

interface ResultsAreaProps {
  analysis: {
    results: AnalysisResultsData | null;
    isLoading: boolean;
    error: string | null;
  };
  interaction: {
    selectedIssueId: string | null;
    onIssueClick: (issueId: string) => void;
    onApplySuggestion: (issue: DisplayIssue, suggestion: string) => void;
    onUndoSuggestion: (issueId: string) => void;
    appliedSuggestions?: Set<string>;
  };
  filter: {
    filterType: string;
    setFilterType: (type: string) => void;
  };
}

const ResultsArea = ({ analysis, interaction, filter }: ResultsAreaProps) => {
  const location = useLocation();
  const tool = location.pathname.split("/")[1] || "home";

  const { results, isLoading, error } = analysis;
  const {
    selectedIssueId,
    onIssueClick,
    onApplySuggestion,
    onUndoSuggestion,
    appliedSuggestions,
  } = interaction;
  const { filterType, setFilterType } = filter;

  return (
    <div className="bg-card h-full border rounded-2xl shadow-sm overflow-hidden">
      {tool === "home" ? (
        <GrammarResults
          analysisResults={results || null}
          isLoading={isLoading}
          error={error}
          selectedIssueId={selectedIssueId}
          onIssueClick={onIssueClick}
          onApplySuggestion={onApplySuggestion}
          onUndoSuggestion={onUndoSuggestion}
          appliedSuggestions={new Set(appliedSuggestions)} // backward compatibility
          filterType={filterType}
          setFilterType={setFilterType}
        />
      ) : tool === "paraphraser" ? (
        <ParaphraserResults
          text={results?.paraphraser || ""}
          isLoading={isLoading}
          error={error}
        />
      ) : (
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 bg-[var(--muted)]">
              <span className="text-2xl">📝</span>
            </div>
            <h3 className="text-lg font-semibold text-[var(--foreground)] mb-2">
              Tool not available
            </h3>
            <p className="text-sm text-[var(--muted-foreground)]">
              No results available for this tool.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsArea;
