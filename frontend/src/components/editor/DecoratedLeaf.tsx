import React from "react";
import { Text } from "slate";
import type { CustomText, DecoratedLeafProps } from "@/types";

const isDecoratedText = (leaf: Text): leaf is CustomText => {
  return (leaf as CustomText).types !== undefined;
};

const highlightConfig = {
  grammar: {
    bg: "var(--highlight-grammar-bg)",
    underline: "var(--highlight-grammar-underline)",
    priority: 1,
  },
  inclusive: {
    bg: "var(--highlight-inclusive-bg)",
    underline: "var(--highlight-inclusive-underline)",
    priority: 2,
  },
  readability: {
    bg: "var(--highlight-readability-bg)",
    underline: "var(--highlight-readability-underline)",
    priority: 3,
  },
  synonym: {
    bg: "var(--highlight-synonym-bg)",
    underline: "var(--highlight-synonym-underline)",
    priority: 4,
  },
};

type IssueType = keyof typeof highlightConfig;

function getHighlightStyle(types: IssueType[]) {
  let bestType: IssueType = types[0] || "grammar";
  let highestPriority = Infinity;

  for (const type of types) {
    if (
      highlightConfig[type] &&
      highlightConfig[type].priority < highestPriority
    ) {
      highestPriority = highlightConfig[type].priority;
      bestType = type;
    }
  }
  return highlightConfig[bestType];
}

export const DecoratedLeaf: React.FC<
  Omit<DecoratedLeafProps, "selectedIssueId">
> = React.memo(({ attributes, children, leaf, onIssueClick }) => {
  if (!isDecoratedText(leaf) || leaf.types.length === 0) {
    return <span {...attributes}>{children}</span>;
  }

  const { types, messages = [], issueIds = [], isSelected = false } = leaf;
  const { bg, underline } = getHighlightStyle(types);

  const handleClick = (e: React.MouseEvent<HTMLSpanElement>) => {
    e.stopPropagation();
    if (onIssueClick && issueIds.length > 0) {
      onIssueClick(issueIds[0]);
    }
  };

  const dynamicStyles: React.CSSProperties = {
    backgroundColor: bg,
    textDecoration: "none",
    boxShadow: `inset 0 -1px 0 0 ${underline}`, // thinner underline
    cursor: "pointer",
    outline: isSelected ? "2px solid #3b82f6" : "none",
    transition: "outline 0.2s ease", // subtle focus effect
  };

  return (
    <span
      {...attributes}
      className="px-[1px] py-[1px] rounded-[2px]" // subtle padding and rounding
      style={dynamicStyles}
      onClick={handleClick}
      data-tooltip-id="editor-tooltip"
      data-tooltip-html={messages.join("<br />")}
    >
      {children}
    </span>
  );
});

DecoratedLeaf.displayName = "DecoratedLeaf";
