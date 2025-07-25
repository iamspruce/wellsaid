// File: components/SuggestionCard.tsx
"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  RefreshCw,
  AlertTriangle,
  Users,
  BookOpen,
  ArrowRight,
  Lightbulb,
  Clock,
  Undo2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { DisplayIssue } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import ConfidenceIndicator from "./confidence-indicator";

interface EnhancedSuggestionCardsProps {
  issues: DisplayIssue[];
  selectedIssueId: string | null;
  onIssueClick?: (issueId: string) => void;
  onApplySuggestion?: (issue: DisplayIssue, suggestion: string) => void;
  appliedSuggestions?: Set<string>;
  onUndoSuggestion?: (issueId: string) => void;
}

const getIssueConfig = (type: string) => {
  switch (type) {
    case "grammar":
      return {
        icon: CheckCircle2,
        label: "Grammar",
        color: "text-[color:var(--highlight-grammar-underline)]",
        bgColor: "bg-[color:var(--highlight-grammar-bg)]",
        borderColor: "border-[color:var(--highlight-grammar-underline)]",
        badgeColor:
          "bg-[color:var(--highlight-grammar-bg)] text-[color:var(--highlight-grammar-underline)]",
      };
    case "synonym":
      return {
        icon: RefreshCw,
        label: "Word Choice",
        color: "text-[color:var(--highlight-synonym-underline)]",
        bgColor: "bg-[color:var(--highlight-synonym-bg)]",
        borderColor: "border-[color:var(--highlight-synonym-underline)]",
        badgeColor:
          "bg-[color:var(--highlight-synonym-bg)] text-[color:var(--highlight-synonym-underline)]",
      };
    case "readability":
      return {
        icon: BookOpen,
        label: "Readability",
        color: "text-[color:var(--highlight-readability-underline)]",
        bgColor: "bg-[color:var(--highlight-readability-bg)]",
        borderColor: "border-[color:var(--highlight-readability-underline)]",
        badgeColor:
          "bg-[color:var(--highlight-readability-bg)] text-[color:var(--highlight-readability-underline)]",
      };
    case "inclusive":
      return {
        icon: Users,
        label: "Inclusive Language",
        color: "text-[color:var(--highlight-inclusive-underline)]",
        bgColor: "bg-[color:var(--highlight-inclusive-bg)]",
        borderColor: "border-[color:var(--highlight-inclusive-underline)]",
        badgeColor:
          "bg-[color:var(--highlight-inclusive-bg)] text-[color:var(--highlight-inclusive-underline)]",
      };
    default:
      return {
        icon: AlertTriangle,
        label: "Issue",
        color: "text-gray-500 dark:text-gray-300",
        bgColor: "bg-gray-50 dark:bg-gray-800",
        borderColor: "border-gray-200 dark:border-gray-600",
        badgeColor:
          "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300",
      };
  }
};

const getSeverityConfig = (severity: string) => {
  switch (severity?.toLowerCase()) {
    case "critical":
      return {
        color: "bg-red-100 text-red-800",
        tooltip:
          "This issue requires immediate attention; it significantly impacts clarity or professionalism.",
      };
    case "major":
      return {
        color: "bg-orange-100 text-orange-800",
        tooltip:
          "This is a significant issue that should be addressed to improve overall writing quality.",
      };
    case "minor":
      return {
        color: "bg-yellow-100 text-yellow-800",
        tooltip: "This is a minor suggestion that can refine your writing.",
      };
    default:
      return {
        color: "bg-gray-100 text-gray-800",
        tooltip: "This is a general issue with moderate impact.",
      };
  }
};

const SuggestionCards = ({
  issues,
  selectedIssueId,
  onIssueClick,
  onApplySuggestion,
  appliedSuggestions = new Set(),
  onUndoSuggestion,
}: EnhancedSuggestionCardsProps) => {
  const [recentlyApplied, setRecentlyApplied] = useState<Set<string>>(
    new Set()
  );
  const [expandedSuggestions, setExpandedSuggestions] = useState<Set<string>>(
    new Set()
  );

  useEffect(() => {
    if (selectedIssueId) {
      const element = document.getElementById(`issue-${selectedIssueId}`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [selectedIssueId]);

  const handleApplySuggestion = (issue: DisplayIssue, suggestion: string) => {
    onApplySuggestion?.(issue, suggestion);
    setRecentlyApplied((prev) => new Set([...prev, issue.id]));

    setTimeout(() => {
      setRecentlyApplied((prev) => {
        const newSet = new Set(prev);
        newSet.delete(issue.id);
        return newSet;
      });
    }, 3000);
  };

  const toggleExpandSuggestions = (issueId: string) => {
    setExpandedSuggestions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(issueId)) {
        newSet.delete(issueId);
      } else {
        newSet.add(issueId);
      }
      return newSet;
    });
  };
  if (issues.length === 0) {
    return (
      <div className="text-center py-12 bg-[var(--card)] text-[var(--card-foreground)]">
        <CheckCircle2 className="w-16 h-16 text-green-500 dark:text-green-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Great writing!</h3>
        <p className="text-sm text-[var(--muted-foreground)]">
          No issues found with the current filter.
        </p>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {issues.map((issue, index) => {
          const config = getIssueConfig(issue.type);
          const severityConfig = getSeverityConfig(issue.severity);
          const Icon = config.icon;
          const isSelected = issue.id === selectedIssueId;
          const isApplied = appliedSuggestions.has(issue.id);
          const isRecentlyApplied = recentlyApplied.has(issue.id);

          const primarySuggestion =
            issue.suggested_segment || issue.suggestions?.[0];
          const otherSuggestions = issue.suggestions?.filter(
            (s) => s !== primarySuggestion
          );
          const isExpanded = expandedSuggestions.has(issue.id);

          const confidence = Math.floor(Math.random() * 30) + 70;

          return (
            <Card
              id={`issue-${issue.id}`}
              key={issue.id}
              className={`group cursor-pointer transition-all duration-300 ${
                isSelected
                  ? `ring-2 ring-primary shadow-lg ${config.bgColor}`
                  : isApplied
                  ? "bg-green-100 border-green-300 shadow-md"
                  : "hover:shadow-md border-border"
              }`}
              onClick={() => onIssueClick?.(issue.id)}
            >
              <CardContent className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-full ${config.bgColor} ${
                        config.borderColor
                      } border transition-all duration-200 ${
                        isApplied ? "bg-green-200 border-green-400" : ""
                      }`}
                    >
                      <Icon
                        className={`w-4 h-4 ${
                          isApplied ? "text-green-700" : config.color
                        }`}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-foreground text-sm">
                          {config.label}
                        </h3>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge
                              variant="secondary"
                              className={`text-xs ${severityConfig.color}`}
                            >
                              {issue.severity}
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{severityConfig.tooltip}</p>
                          </TooltipContent>
                        </Tooltip>
                        {!isApplied && (
                          <ConfidenceIndicator
                            confidence={confidence}
                            size="sm"
                          />
                        )}
                        {isApplied && (
                          <Badge className="bg-green-600 text-white text-xs px-2 py-0.5 rounded-full">
                            Applied
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {issue.message}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-xs text-muted-foreground font-medium">
                      #{index + 1}
                    </div>
                    {isRecentlyApplied && !isApplied && (
                      <div className="flex items-center gap-1 text-xs text-green-600">
                        <Clock className="w-3 h-3 mr-1" />
                        <span>Just applied</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Original vs Primary Suggestion */}
                <div className="bg-muted rounded-lg p-3 mb-3">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                    <Lightbulb className="w-3 h-3" />
                    <span>How to improve:</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 items-center">
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">
                        Original:
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-sm ${
                          isApplied
                            ? "line-through text-muted-foreground bg-muted"
                            : "line-through text-destructive bg-destructive/10"
                        }`}
                      >
                        {issue.original_segment}
                      </span>
                    </div>
                    <div className="text-center">
                      <ArrowRight className="w-4 h-4 text-muted-foreground mx-auto" />
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">
                        Suggestion:
                      </div>
                      {primarySuggestion ? (
                        <span
                          className={`px-2 py-1 rounded font-medium text-sm ${
                            isApplied
                              ? "text-green-800 bg-green-200"
                              : "text-green-700 bg-green-50"
                          }`}
                        >
                          {primarySuggestion}
                        </span>
                      ) : (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="px-2 py-1 rounded text-muted-foreground bg-muted italic cursor-help">
                              Manual Review Recommended
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>
                              This issue highlights a potential concern but
                              doesn't have an automated suggestion.
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                  </div>
                </div>

                {/* Context */}
                <div className="mb-4">
                  <div className="text-xs text-muted-foreground mb-1">
                    Original Text in Context:
                  </div>
                  <div className="text-sm text-foreground leading-relaxed bg-card border rounded-lg p-3">
                    <span className="text-muted-foreground">
                      {issue.context_before}
                    </span>
                    <span
                      className={`font-semibold px-1 rounded ${
                        isApplied
                          ? "bg-green-100 text-green-800"
                          : `${config.color} ${config.bgColor}`
                      }`}
                    >
                      {issue.original_segment}
                    </span>
                    <span className="text-muted-foreground">
                      {issue.context_after}
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                {issue.explanation &&
                issue.explanation !== "No additional explanation provided." &&
                issue.explanation !==
                  "Consider using more inclusive language." ? (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-xs text-blue-600 font-medium mb-1">
                      Reasoning:
                    </div>
                    <p className="text-sm text-blue-800 mb-2">
                      {issue.explanation}
                    </p>
                    {issue.source && issue.type === "inclusive" && (
                      <div className="text-xs text-blue-700">
                        <a
                          href={issue.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline hover:no-underline"
                        >
                          Learn more about this guideline
                        </a>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mb-4 p-3 bg-muted border border-border rounded-lg text-sm text-muted-foreground">
                    No detailed reasoning provided for this suggestion.
                  </div>
                )}

                {/* Buttons */}
                <div className="flex flex-wrap gap-2">
                  {isApplied ? (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 px-3 text-xs font-medium border-orange-300 text-orange-700 hover:bg-orange-50 bg-transparent"
                          onClick={(e) => {
                            e.stopPropagation();
                            onUndoSuggestion?.(issue.id);
                          }}
                        >
                          <Undo2 className="w-3 h-3 mr-1" />
                          Undo
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Undo this suggestion</p>
                      </TooltipContent>
                    </Tooltip>
                  ) : (
                    <>
                      {primarySuggestion && (
                        <Button
                          size="sm"
                          className="h-8 px-3 text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApplySuggestion(issue, primarySuggestion);
                          }}
                        >
                          Apply: {primarySuggestion}
                        </Button>
                      )}
                      {otherSuggestions && otherSuggestions?.length > 0 && (
                        <>
                          {!isExpanded ? (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-3 text-xs font-medium border-border hover:bg-muted"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleExpandSuggestions(issue.id);
                              }}
                            >
                              Show {otherSuggestions.length}{" "}
                              {otherSuggestions.length === 1
                                ? "alternative"
                                : "alternatives"}
                              <ChevronDown className="w-3 h-3 ml-1" />
                            </Button>
                          ) : (
                            <>
                              <div className="w-full flex flex-wrap gap-2 mt-2">
                                {otherSuggestions.map((suggestion, idx) => (
                                  <Button
                                    key={idx}
                                    variant="outline"
                                    size="sm"
                                    className="h-8 px-3 text-xs font-medium border-border hover:bg-muted"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleApplySuggestion(issue, suggestion);
                                    }}
                                  >
                                    Apply: {suggestion}
                                  </Button>
                                ))}
                              </div>
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-8 px-3 text-xs font-medium border-border hover:bg-muted mt-2"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleExpandSuggestions(issue.id);
                                }}
                              >
                                Collapse <ChevronUp className="w-3 h-3 ml-1" />
                              </Button>
                            </>
                          )}
                        </>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </TooltipProvider>
  );
};

export default SuggestionCards;
