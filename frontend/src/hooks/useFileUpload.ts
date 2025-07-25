import { useCallback, useState } from "react";
import { Editor, Transforms, Node } from "slate";
import { readFileContent } from "@/lib/readFileContent";
import { stringToNodes } from "./useEditorChange";

export function useFileUpload(
  editor: Editor,
  setEditorContent: (content: string) => void
) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleFileUpload = useCallback(
    async (file: File) => {
      setIsLoading(true);
      setError(null);
      try {
        const text = await readFileContent(file);

        const nodes = stringToNodes(text); // ⬅️ split content into multiple blocks

        applyTransformWithSelection(() => {
          // Clear editor first
          Transforms.delete(editor, {
            at: {
              anchor: Editor.start(editor, []),
              focus: Editor.end(editor, []),
            },
          });

          // Insert paragraph nodes
          Transforms.insertNodes(editor, nodes, { at: [0] });
        });

        setEditorContent(Node.string(editor));
      } catch (err) {
        console.error("File upload failed:", err);
        setError("Failed to upload or process the file");
      } finally {
        setIsLoading(false);
      }
    },
    [editor, setEditorContent, applyTransformWithSelection]
  );

  return { isLoading, error, handleFileUpload };
}
