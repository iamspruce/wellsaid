import { useCallback } from "react";
import { Editor, Transforms, Node } from "slate";

export function usePaste(
  editor: Editor,
  setEditorContent: (content: string) => void
) {
  const applyTransformWithSelection = useCallback(
    (fn: () => void) => {
      const prevSelection = editor.selection;
      Editor.withoutNormalizing(editor, () => {
        fn();
        if (prevSelection) Transforms.select(editor, prevSelection);
      });
    },
    [editor]
  );

  const handlePaste = useCallback(
    (event: React.ClipboardEvent) => {
      event.preventDefault();
      const text = event.clipboardData.getData("text/plain");
      applyTransformWithSelection(() => {
        const point = editor.selection?.focus || Editor.end(editor, []);
        Transforms.insertText(editor, text, { at: point });
      });
      setEditorContent(Node.string(editor));
    },
    [editor, setEditorContent, applyTransformWithSelection]
  );

  return { handlePaste };
}
