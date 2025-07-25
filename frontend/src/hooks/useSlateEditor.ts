import { useMemo } from "react";
import { createEditor } from "slate";
import { withReact } from "slate-react";
import { withHistory } from "slate-history";

export const useSlateEditor = () => {
  const editor = useMemo(() => withHistory(withReact(createEditor())), []);
  return editor;
};
