"use client";

import type { AnalysisResultsData, DisplayIssue } from "@/types";
import { transformAnalysisResultsToDisplayIssues } from "@/lib/transformAnalysisResultsToDisplayIssues"; // Assumed to be updated to accept filterType
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Users,
  RefreshCw,
  BookOpen,
  AlertTriangle,
} from "lucide-react";
import SuggestionCards from "../SuggestionCard";
import { useEffect, useMemo } from "react";

interface GrammarResultsProps {
  analysisResults: AnalysisResultsData | null;
  isLoading: boolean;
  error: string | null;
  selectedIssueId: string | null;
  onIssueClick: (issueId: string) => void;
  onApplySuggestion: (issue: DisplayIssue, suggestion: string) => void;
  onUndoSuggestion: (issueId: string) => void;
  appliedSuggestions: Set<string>;
  filterType: string; // Updated type
  setFilterType: (
    type: "grammar" | "inclusive" | "readability" | "synonym"
  ) => void; // Updated type
}

const getFilterIcon = (type: string) => {
  switch (type) {
    case "grammar":
      return (
        <CheckCircle2 className="w-4 h-4 text-red-500 dark:text-red-400" />
      );
    case "inclusive":
      return <Users className="w-4 h-4 text-amber-500 dark:text-amber-400" />;
    case "synonym":
      return (
        <RefreshCw className="w-4 h-4 text-purple-500 dark:text-purple-400" />
      );
    case "readability":
      return <BookOpen className="w-4 h-4 text-blue-500 dark:text-blue-400" />;
    default:
      return null;
  }
};

const GrammarResults = ({
  analysisResults,
  isLoading,
  error,
  selectedIssueId,
  onIssueClick,
  onApplySuggestion,
  onUndoSuggestion,
  appliedSuggestions,
  filterType,
  setFilterType,
}: GrammarResultsProps) => {
  // Pass filterType down to transformAnalysisResultsToDisplayIssues for initial filtering
  const allIssuesForCurrentFilter = useMemo(() => {
    if (!analysisResults) return [];
    // IMPORTANT: Ensure transformAnalysisResultsToDisplayIssues accepts and passes 'filterType'
    // to getUnifiedIssuesFromResults.
    return transformAnalysisResultsToDisplayIssues(analysisResults);
  }, [analysisResults, filterType]);

  const filteredIssues = useMemo(() => {
    // This now only filters by appliedSuggestions, as type filtering happens upstream
    return allIssuesForCurrentFilter.filter(
      (issue) => !appliedSuggestions.has(issue.id)
    );
  }, [allIssuesForCurrentFilter, appliedSuggestions]);

  const issueStats = useMemo(
    () => ({
      // Update 'all' to reflect the current filtered type count
      all: filteredIssues.length, // This is now the count for the *currently selected type*
      grammar: allIssuesForCurrentFilter.filter(
        (issue) => issue.type === "grammar"
      ).length,
      inclusive: allIssuesForCurrentFilter.filter(
        (issue) => issue.type === "inclusive"
      ).length,
      synonym: allIssuesForCurrentFilter.filter(
        (issue) => issue.type === "synonym"
      ).length,
      readability: allIssuesForCurrentFilter.filter(
        (issue) => issue.type === "readability"
      ).length,
    }),
    [filteredIssues, allIssuesForCurrentFilter] // Depend on both for accurate counts
  );

  useEffect(() => {
    // Set default filter type to "grammar" if none is set
    if (!filterType) {
      setFilterType("grammar");
    }
  }, [filterType, setFilterType]);

  if (isLoading) {
    return (
      <div className="p-4 space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center text-destructive">
        <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--foreground)] mb-2">
          Analysis Error
        </h3>
        <p className="text-sm text-[var(--muted-foreground)]">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[var(--card)] text-[var(--foreground)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <h2 className="text-lg font-semibold">
          Suggestions{" "}
          <span className="text-[var(--muted-foreground)] font-normal">
            ({issueStats.all}){" "}
            {/* This now shows count for the active filter */}
          </span>
        </h2>
        <div>
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-[190px] rounded-lg border-[var(--border)] bg-[var(--input)] text-[var(--foreground)]">
              <div className="flex items-center gap-2">
                {getFilterIcon(filterType)}
                <SelectValue placeholder="Filter by type" />
              </div>
            </SelectTrigger>
            <SelectContent className="bg-[var(--popover)] text-[var(--popover-foreground)] border-[var(--border)]">
              {/* Removed "all" from the options */}
              {["grammar", "inclusive", "synonym", "readability"].map(
                (type) => (
                  <SelectItem key={type} value={type}>
                    <div className="flex justify-between w-full">
                      <span className="capitalize">{type}</span>
                      <Badge variant="secondary">
                        {issueStats[type as keyof typeof issueStats]}
                      </Badge>
                    </div>
                  </SelectItem>
                )
              )}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Results */}
      <div className="p-4 pt-2 pb-20 flex-1 overflow-y-auto">
        <SuggestionCards
          issues={filteredIssues}
          selectedIssueId={selectedIssueId}
          onIssueClick={onIssueClick}
          onApplySuggestion={onApplySuggestion}
          onUndoSuggestion={onUndoSuggestion}
          appliedSuggestions={appliedSuggestions}
        />
      </div>
    </div>
  );
};

export default GrammarResults;
