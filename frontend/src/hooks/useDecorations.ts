import { useState, useCallback, useEffect } from "react";
import { Editor, Node, Path, Text, Range as SlateRange } from "slate";
import { debounce } from "@/lib/debounce";
import {
  getUnifiedIssuesFromResults,
  type UnifiedIssue,
} from "@/lib/getUnifiedIssuesFromResults";
import type {
  AnalysisResultsData,
  CustomText,
  IssueRangeMeta,
  MergedDecoration,
  OffsetResult,
} from "@/types";

// Define a raw decoration type before merging
type RawDecoration = {
  range: SlateRange;
  type: UnifiedIssue["type"];
  message: string;
  suggestions: string[];
  issueId: string;
  originalIssue: any;
};

export const calculateOffsets = (
  issue: UnifiedIssue,
  blockStartOffset: number,
  nodeStartOffsetInBlock: number,
  node: Node
): OffsetResult | null => {
  if (!Text.isText(node) || typeof node.text !== "string") return null;

  const issueStartInBlock = issue.start - blockStartOffset;
  const relativeStart = issueStartInBlock - nodeStartOffsetInBlock;
  const relativeEnd = relativeStart + issue.length;

  if (relativeEnd <= 0 || relativeStart >= node.text.length) return null;

  return {
    start: Math.max(0, relativeStart),
    end: Math.min(node.text.length, relativeEnd),
  };
};

function mergeOverlappingDecorations(
  decorations: RawDecoration[]
): MergedDecoration[] {
  if (decorations.length < 2) {
    return decorations.map((d) => ({
      range: d.range,
      types: [d.type],
      messages: [d.message],
      suggestions: [d.suggestions],
      issueIds: [d.issueId],
      originalIssues: [d.originalIssue],
    }));
  }

  decorations.sort((a, b) => {
    const pathCompare = Path.compare(a.range.anchor.path, b.range.anchor.path);
    if (pathCompare !== 0) return pathCompare;

    const startDiff = a.range.anchor.offset - b.range.anchor.offset;
    if (startDiff !== 0) return startDiff;

    return b.range.focus.offset - a.range.focus.offset;
  });

  const merged: MergedDecoration[] = [];
  let current = {
    range: { ...decorations[0].range },
    types: [decorations[0].type],
    messages: [decorations[0].message],
    suggestions: [decorations[0].suggestions],
    issueIds: [decorations[0].issueId],
    originalIssues: [decorations[0].originalIssue],
  };

  for (let i = 1; i < decorations.length; i++) {
    const next = decorations[i];

    const isOverlapping =
      Path.equals(current.range.anchor.path, next.range.anchor.path) &&
      current.range.focus.offset >= next.range.anchor.offset;

    const isSameType =
      current.types.length === 1 && current.types[0] === next.type;

    const isSameIssue = current.issueIds.includes(next.issueId);

    if (isOverlapping && (isSameType || isSameIssue)) {
      current.range.focus.offset = Math.max(
        current.range.focus.offset,
        next.range.focus.offset
      );

      if (!current.issueIds.includes(next.issueId)) {
        current.types.push(next.type);
        current.messages.push(next.message);
        current.suggestions.push(next.suggestions);
        current.issueIds.push(next.issueId);
        current.originalIssues.push(next.originalIssue);
      }
    } else {
      merged.push(current);
      current = {
        range: { ...next.range },
        types: [next.type],
        messages: [next.message],
        suggestions: [next.suggestions],
        issueIds: [next.issueId],
        originalIssues: [next.originalIssue],
      };
    }
  }

  merged.push(current);
  return merged;
}

export const useDecorations = (
  editor: Editor,
  analysisResults: AnalysisResultsData | null | undefined,
  analysisMap: Map<string, number> | null,
  filterType: string,
  issueRangeMapRef: React.MutableRefObject<Map<string, IssueRangeMeta>>,
  appliedSuggestions: Set<string>
) => {
  const [decorations, setDecorations] = useState<MergedDecoration[]>([]);

  const calculateDecorations = useCallback(
    debounce(() => {
      if (!analysisResults || !analysisMap) {
        setDecorations([]);
        return;
      }

      const allIssues = getUnifiedIssuesFromResults(
        analysisResults,
        filterType
      );
      const activeIssues = allIssues.filter(
        (issue) => !appliedSuggestions.has(issue.issueId)
      );

      const rawDecorations: RawDecoration[] = [];
      issueRangeMapRef.current.clear();

      for (const [node, path] of Editor.nodes(editor, {
        at: [],
        match: (n) => Text.isText(n),
      })) {
        const blockPath = path.slice(0, 1);
        const blockPathKey = String(blockPath[0]);
        const blockStartOffset = analysisMap.get(blockPathKey);

        if (blockStartOffset === undefined) {
          if (process.env.NODE_ENV === "development") {
            console.warn(`Missing offset for blockPath: ${blockPathKey}`);
          }
          continue;
        }

        let nodeStartOffsetInBlock = 0;
        const [parent] = Editor.parent(editor, path);
        for (const child of parent.children) {
          if (child === node) break;
          if (Text.isText(child)) {
            nodeStartOffsetInBlock += child.text.length;
          }
        }

        const nodeDecorations = activeIssues
          .map((issue) => {
            const offsets = calculateOffsets(
              issue,
              blockStartOffset,
              nodeStartOffsetInBlock,
              node
            );
            if (!offsets) return null;

            issueRangeMapRef.current.set(issue.issueId, {
              path,
              originalIssue: issue.originalIssue,
            });

            return {
              range: {
                anchor: { path, offset: offsets.start },
                focus: { path, offset: offsets.end },
              },
              type: issue.type,
              message: issue.message,
              suggestions: issue.suggestions,
              issueId: issue.issueId,
              originalIssue: issue.originalIssue,
            };
          })
          .filter((d): d is RawDecoration => d !== null);

        rawDecorations.push(...nodeDecorations);
      }

      const merged = mergeOverlappingDecorations(rawDecorations);
      setDecorations(merged);
    }, 300),
    [
      analysisResults,
      analysisMap,
      editor,
      filterType,
      issueRangeMapRef,
      appliedSuggestions,
    ]
  );

  useEffect(() => {
    calculateDecorations();
    return () => calculateDecorations.cancel();
  }, [calculateDecorations]);

  const decorate = useCallback(
    (selectedIssueId: string | null) =>
      ([node, path]: [Node, Path]) => {
        if (!Text.isText(node)) return [];

        return decorations
          .filter((dec) => Path.equals(dec.range.anchor.path, path))
          .map((dec) => {
            const isSelected = selectedIssueId
              ? dec.issueIds.includes(selectedIssueId)
              : false;
            const rangeWithProps: SlateRange & Partial<CustomText> = {
              ...dec.range,
              types: dec.types,
              messages: dec.messages,
              suggestions: dec.suggestions.flat(),
              issueIds: dec.issueIds,
              isGrammarError: dec.types.includes("grammar"),
              isInclusiveLanguageError: dec.types.includes("inclusive"),
              isSynonymSuggestion: dec.types.includes("synonym"),
              isReadabilityIssue: dec.types.includes("readability"),
              isSelected,
            };
            return rangeWithProps;
          });
      },
    [decorations]
  );

  return { decorate, decorations };
};
