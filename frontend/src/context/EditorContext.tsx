import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { Editor } from "slate";
import { useSlateEditor } from "../hooks/useSlateEditor";
import { getVisibleData } from "../lib/editorUtils";
import type { AnalysisResultsData, IssueRangeMeta } from "../types";
import { debounce } from "@/lib/debounce";

interface EditorState {
  editorContent: string;
  analysisResults: AnalysisResultsData | null;
  analysisMap: Map<string, number> | null;
  isLoading: boolean;
  error: string | null;
}

interface EditorContextType extends EditorState {
  editor: Editor;
  setEditorContent: (content: string) => void;
  triggerAnalysis: (editor: Editor, scrollContainer: HTMLElement) => void;
  issueRangeMapRef: React.MutableRefObject<Map<string, IssueRangeMeta>>;
  setAnalysisResults: (results: AnalysisResultsData | null) => void;
  setIsLoading: (loading: boolean) => void;
}

const EditorContext = createContext<EditorContextType | undefined>(undefined);

export const EditorProvider = ({ children }: { children: ReactNode }) => {
  const editor = useSlateEditor();
  const issueRangeMapRef = useRef<Map<string, IssueRangeMeta>>(new Map());

  const [state, setState] = useState<EditorState>({
    editorContent: "",
    analysisResults: null,
    analysisMap: null,
    isLoading: false,
    error: null,
  });

  const setEditorContent = useCallback((content: string) => {
    setState((prev) => ({ ...prev, editorContent: content }));
  }, []);

  const fetchAnalysis = async (text: string) => {
    const res = await fetch("http://localhost:7860/analyze/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": "12345",
      },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      const status = res.status;
      throw new Error(
        status >= 500
          ? "Server error, please try again later."
          : `API error: Status ${status}`
      );
    }

    return await res.json();
  };

  const debouncedAnalysis = useRef(
    debounce(async (editor: Editor, scrollContainer: HTMLElement) => {
      const { visibleText, pathMap } = getVisibleData(editor, scrollContainer);

      if (!visibleText.trim()) {
        // If the editor is empty, clear results and stop loading.
        setState((prev) => ({
          ...prev,
          isLoading: false,
          analysisResults: null,
          analysisMap: null,
          error: null,
        }));
        return;
      }

      try {
        const json = await fetchAnalysis(visibleText);

        // This race condition check is excellent. Keep it.
        const currentTextInEditor = getVisibleData(
          editor,
          scrollContainer
        ).visibleText;
        if (visibleText !== currentTextInEditor) {
          // Don't turn off loading, as a newer request is in flight
          return;
        }

        // Update results and turn off loading
        setState((prev) => ({
          ...prev,
          isLoading: false,
          analysisResults: json.analysis_results,
          analysisMap: pathMap,
          error: null,
        }));
      } catch (err: any) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err.message || "Analysis failed.",
          analysisMap: null,
        }));
      }
    }, 1000)
  ).current;

  const triggerAnalysis = useCallback(
    (editor: Editor, scrollContainer: HTMLElement) => {
      debouncedAnalysis(editor, scrollContainer);
    },
    [debouncedAnalysis]
  );

  return (
    <EditorContext.Provider
      value={{
        ...state,
        editor,
        setEditorContent,
        triggerAnalysis,
        issueRangeMapRef,
        setAnalysisResults: (results) =>
          setState((prev) => ({ ...prev, analysisResults: results })),
        setIsLoading: (loading) =>
          setState((prev) => ({ ...prev, isLoading: loading })),
      }}
    >
      {children}
    </EditorContext.Provider>
  );
};

export const useEditorContext = () => {
  const context = useContext(EditorContext);
  if (!context)
    throw new Error("useEditorContext must be used within an EditorProvider");
  return context;
};
