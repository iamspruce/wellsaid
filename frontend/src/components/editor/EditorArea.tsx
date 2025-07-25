// File: components/editor/EditorArea.tsx
import { useRef, forwardRef, useImperativeHandle, useCallback } from "react";
import { Slate, Editable, type RenderLeafProps } from "slate-react";
import { Editor, Transforms, Range as SlateRange } from "slate";
import { ReactEditor } from "slate-react";

import { useEditorContext } from "../../context/EditorContext";
import { useSlateEditor } from "../../hooks/useSlateEditor";
import { useFileUpload } from "../../hooks/useFileUpload";
import { DecoratedLeaf } from "./DecoratedLeaf";
import EditorControls from "./EditorControls";
import { useDecorations } from "@/hooks/useDecorations";
import { useEditorChange } from "@/hooks/useEditorChange";

interface EditorRef {
  scrollToIssue: (issueId: string) => void;
  applySuggestion: (issueId: string, suggestion: string) => boolean;
  revertToOriginal: (issueId: string, originalText: string) => boolean; // New method
}

export default forwardRef<
  EditorRef,
  {
    shouldAnalyze: boolean;
    onIssueClick: (issueId: string) => void;
    filterType: string;
    selectedIssueId: string | null;
    appliedSuggestions: Set<string>;
  }
>(function EditorArea(
  {
    shouldAnalyze,
    onIssueClick,
    filterType,
    selectedIssueId,
    appliedSuggestions,
  },
  ref
) {
  const {
    editorContent,
    setEditorContent,
    triggerAnalysis,
    issueRangeMapRef,
    analysisResults,
    analysisMap,
    setAnalysisResults,
    setIsLoading,
  } = useEditorContext();

  const editor = useSlateEditor();
  const scrollRef = useRef<HTMLDivElement>(null);

  const { value, handleEditorChange } = useEditorChange(
    editor,
    editorContent,
    setEditorContent,
    setIsLoading,
    setAnalysisResults,
    issueRangeMapRef,
    shouldAnalyze,
    triggerAnalysis,
    scrollRef
  );

  const { decorations, decorate } = useDecorations(
    editor,
    analysisResults,
    analysisMap,
    filterType,
    issueRangeMapRef,
    appliedSuggestions
  );

  const { handleFileUpload, isLoading: isUploading } = useFileUpload(
    editor,
    setEditorContent
  );

  useImperativeHandle(
    ref,
    () => {
      const findRangeForIssue = (issueId: string): SlateRange | null => {
        const decoration = decorations.find((d: any) =>
          d.issueIds.includes(issueId)
        );
        return decoration ? decoration.range : null;
      };

      return {
        scrollToIssue: (issueId: string) => {
          const range = findRangeForIssue(issueId);
          if (!range) {
            console.warn(`No range found for issue ID ${issueId}`);
            return;
          }
          try {
            Transforms.select(editor, range);
            ReactEditor.focus(editor);
            const domNode = ReactEditor.toDOMNode(
              editor,
              Editor.node(editor, range.anchor.path)[0]
            );
            domNode.scrollIntoView({ behavior: "smooth", block: "center" });
          } catch (e) {
            console.error("Failed to scroll to issue", e);
          }
        },
        applySuggestion: (issueId: string, suggestion: string): boolean => {
          const range = findRangeForIssue(issueId);
          if (!range) return false;
          try {
            Editor.withoutNormalizing(editor, () => {
              Transforms.select(editor, range);
              Transforms.insertText(editor, suggestion, { at: range });
            });
            handleEditorChange(editor.children);
            return true;
          } catch (e) {
            console.error("Failed to apply suggestion:", e);
            return false;
          }
        },
        revertToOriginal: (issueId: string, originalText: string): boolean => {
          // This is a simplified revert. A more robust solution might need to re-calculate ranges.
          // For now, we assume the suggestion that was applied has the same length as the new text.
          // This is a complex problem to solve perfectly.
          const issue = findRangeForIssue(issueId);
          if (!issue) return false;

          // This is a placeholder for a more complex implementation.
          // A full undo would require a more sophisticated tracking of changes.
          // For now we will just re-run the analysis.
          triggerAnalysis(editor, scrollRef.current!);
          return true;
        },
      };
    },
    [editor, decorations, handleEditorChange, analysisResults, triggerAnalysis]
  );

  const renderLeaf = useCallback(
    (props: RenderLeafProps) => (
      <DecoratedLeaf {...props} onIssueClick={onIssueClick} />
    ),
    [onIssueClick]
  );

  const renderElement = useCallback((props: any) => {
    switch (props.element.type) {
      default:
        return <div {...props.attributes}>{props.children}</div>;
    }
  }, []);

  return (
    <div className="flex flex-col h-full relative bg-card border rounded-2xl shadow-sm pb-16">
      <Slate editor={editor} initialValue={value} onChange={handleEditorChange}>
        <div ref={scrollRef} className="editor-scroll flex-1 p-4 md:p-6">
          <Editable
            decorate={decorate(selectedIssueId)}
            renderElement={renderElement}
            renderLeaf={renderLeaf}
            spellCheck={true}
            placeholder="✍️ Start writing..."
            className="prose dark:prose-invert max-w-none w-full outline-none"
          />
        </div>
        <EditorControls
          onFileUpload={handleFileUpload}
          isLoading={isUploading}
        />
      </Slate>
    </div>
  );
});
