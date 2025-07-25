import { useState, useCallback } from "react";
import { Node, Editor, type Descendant } from "slate";
import type { AnalysisResultsData, IssueRangeMeta } from "@/types";
import { debounce } from "@/lib/debounce";

export const stringToNodes = (text: string): Descendant[] =>
  text.split("\n").map((line) => ({
    type: "paragraph",
    children: [{ text: line }],
  }));

export const useEditorChange = (
  editor: Editor,
  editorContent: string,
  setEditorContent: (content: string) => void,
  setIsLoading: (loading: boolean) => void,
  setAnalysisResults: (results: AnalysisResultsData | null) => void,
  issueRangeMapRef: React.MutableRefObject<Map<string, IssueRangeMeta>>,
  shouldAnalyze: boolean,
  triggerAnalysis: (editor: Editor, scrollRef: HTMLDivElement) => void,
  scrollRef: React.RefObject<HTMLDivElement | null>
) => {
  const [value, setValue] = useState<Descendant[]>(
    stringToNodes(editorContent)
  );

  const handleEditorChange = useCallback(
    debounce((newValue: Descendant[]) => {
      setValue(newValue);
      const newText = newValue
        .map((n) => Node.string(n))
        .join("\n")
        .trim();

      if (editorContent !== newText) {
        setEditorContent(newText);
        setIsLoading(true);
        setAnalysisResults(null);
        issueRangeMapRef.current.clear();
        if (shouldAnalyze && editor && scrollRef?.current) {
          triggerAnalysis(editor, scrollRef.current);
        }
      } else {
      }
    }, 500),
    [
      editorContent,
      setEditorContent,
      setIsLoading,
      setAnalysisResults,
      issueRangeMapRef,
      shouldAnalyze,
      editor,
      triggerAnalysis,
      scrollRef,
    ]
  );

  return { value, handleEditorChange };
};
