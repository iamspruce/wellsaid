// File: components/layout/ContentArea.tsx
import { useRef, useState, useCallback } from "react";
import EditorArea from "../editor/EditorArea";
import { useEditorContext } from "@/context/EditorContext";
import ResultsArea from "./ResultsArea";
import { toast } from "sonner";
import type { DisplayIssue } from "@/types";

interface EditorMethods {
  scrollToIssue: (issueId: string) => void;
  applySuggestion: (issueId: string, suggestion: string) => boolean;
  // Add a method to revert to original text
  revertToOriginal: (issueId: string, originalText: string) => boolean;
}

interface ContentAreaProps {
  shouldAnalyze: boolean;
}

const ContentArea = ({ shouldAnalyze }: ContentAreaProps) => {
  const editorRef = useRef<EditorMethods>(null);
  const { analysisResults, isLoading, error } = useEditorContext();

  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("grammar");
  const [appliedSuggestions, setAppliedSuggestions] = useState<
    Map<string, string>
  >(new Map());
  const appliedSuggestionIds = new Set(appliedSuggestions.keys());

  const handleEditorIssueClick = useCallback((issueId: string) => {
    setSelectedIssueId(issueId);
  }, []);

  const handleResultsIssueClick = useCallback((issueId: string) => {
    setSelectedIssueId(issueId);
    editorRef.current?.scrollToIssue(issueId);
  }, []);

  const handleApplySuggestion = useCallback(
    async (issue: DisplayIssue, suggestion: string) => {
      const originalText = issue.original_segment;
      const success = editorRef.current?.applySuggestion(issue.id, suggestion);
      if (success) {
        setAppliedSuggestions((prev) =>
          new Map(prev).set(issue.id, originalText)
        );
        toast.success("Suggestion applied!");
      } else {
        toast.error(
          "Could not apply suggestion. The original text may have changed."
        );
      }
    },
    []
  );

  const handleUndoSuggestion = useCallback(
    async (issueId: string) => {
      const originalText = appliedSuggestions.get(issueId);
      if (
        originalText &&
        editorRef.current?.revertToOriginal(issueId, originalText)
      ) {
        setAppliedSuggestions((prev) => {
          const newMap = new Map(prev);
          newMap.delete(issueId);
          return newMap;
        });
        toast.info("Suggestion undone.");
      } else {
        toast.error("Could not undo suggestion.");
      }
    },
    [appliedSuggestions]
  );

  return (
    <main className="flex flex-col lg:flex-row h-full gap-6 p-4 md:p-6 bg-background">
      <section className="flex-1 h-full min-h-[400px] lg:min-h-0">
        <EditorArea
          ref={editorRef}
          shouldAnalyze={shouldAnalyze}
          onIssueClick={handleEditorIssueClick}
          filterType={filterType}
          selectedIssueId={selectedIssueId}
          appliedSuggestions={appliedSuggestionIds}
        />
      </section>

      <aside className="w-full lg:w-96 h-full lg:max-h-full overflow-hidden">
        <ResultsArea
          analysis={{
            results: analysisResults,
            isLoading,
            error,
          }}
          interaction={{
            selectedIssueId,
            appliedSuggestions: new Set(appliedSuggestions.keys()),
            onIssueClick: handleResultsIssueClick,
            onApplySuggestion: handleApplySuggestion,
            onUndoSuggestion: handleUndoSuggestion,
          }}
          filter={{
            filterType,
            setFilterType,
          }}
        />
      </aside>
    </main>
  );
};

export default ContentArea;
