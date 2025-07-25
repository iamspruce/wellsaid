import type { Path, Range as SlateRange, Text } from "slate";
import type { RenderLeafProps } from "slate-react";

//
// ========== Analysis Result Types ==========
//

export interface GrammarIssue {
  offset: number;
  length: number;
  original_segment: string;
  suggested_segment: string;
  context_before: string;
  context_after: string;
  full_original_sentence_context: string;
  display_context: string;
  message: string;
  type: string;
  line: number;
  column: number;
  severity: string;
  explanation: string;
}

export interface InclusiveIssue {
  id: string;
  term: string;
  type: string;
  note: string;
  suggestions: string[];
  context: string;
  formatted_context: string;
  start_char: number;
  end_char: number;
  source: string;
  gender: string | null;
}

export interface SynonymSuggestion {
  original_word: string;
  start_char: number;
  end_char: number;
  suggestions: string[];
  context: string;
  pos: string;
}

export interface ReadabilityIssue {
  offset: number;
  length: number;
  original_segment: string;
  context_before: string;
  context_after: string;
  full_original_sentence_context: string;
  display_context: string;
  message: string;
  type: string;
  line: number;
  column: number;
  severity: string;
  explanation: string;
}

export interface ReadabilityScore {
  score: number;
  label: string;
  description: string;
  interpretation: {
    name: string;
    color: string;
    note: string;
  };
}

export interface ReadabilityStatistics {
  sentence_count: number;
  word_count: number;
  syllable_count: number;
  average_words_per_sentence: number;
}

export interface ReadabilitySection {
  overall_summary: {
    level: string;
    note: string;
  };
  detailed_scores: Record<string, ReadabilityScore>;
  statistics: ReadabilityStatistics;
  readability_issues?: ReadabilityIssue[];
}

export interface VoiceData {
  voice: string;
  passive_ratio: number;
  passive_sentences_count: number;
  total_sentences_count: number;
}

export interface ToneData {
  tone: string;
}

export interface AnalysisResult<T> {
  status: "success" | "error" | "skipped";
  data?: T;
  message?: string;
}

export interface AnalysisResultsData {
  original_text?: string;
  grammar?: AnalysisResult<{
    issues: GrammarIssue[];
    original_text: string;
    corrected_text_suggestion: string;
  }>;
  inclusive_language?: AnalysisResult<{ issues: InclusiveIssue[] }>;
  synonyms?: AnalysisResult<{ suggestions: SynonymSuggestion[] }>;
  readability?: AnalysisResult<ReadabilitySection>;
  tone?: AnalysisResult<ToneData>;
  voice?: AnalysisResult<VoiceData>;
  paraphraser: string;
}

//
// ========== Editor Display Types ==========
//

export interface DisplayIssue {
  id: string;
  type: string;
  message: string;
  severity: string;
  context_before: string;
  context_after: string;
  original_segment: string;
  suggested_segment?: string;
  suggestions?: string[];
  full_original_sentence_context: string;
  explanation?: string;
  line?: number;
  column?: number;
  source?: string;
  pos?: string;
  term?: string;
  note?: string;
  range: SlateRange;
}

export type EditorIssueType =
  | "grammar"
  | "inclusive"
  | "synonym"
  | "readability";

export interface SuggestionMetadata {
  message: string;
  messages: string[];
  suggestions: string[];
  range: SlateRange;
  position: { top: number; left: number };
  type: EditorIssueType;
  types: EditorIssueType[];
  issueIndex: number;
}

export interface SuggestionModalProps {
  message: string;
  suggestions: string[];
  range: SlateRange;
  position: { top: number; left: number };
  type: EditorIssueType;
  types: EditorIssueType[];
  messages: string[];
  issueIndex: number;
  onClose: () => void;
  onApply: (replacement: string, range: SlateRange) => void;
}

export interface DecoratedLeafProps extends RenderLeafProps {
  onSuggestionClick?: (suggestion: SuggestionMetadata) => void;
  onIssueClick?: (issueId: string) => void;
  selectedIssueId?: string | null;
  className?: string;
  style?: React.CSSProperties;
}

export type MergedDecoration = {
  range: SlateRange;
  types: EditorIssueType[];
  messages: string[];
  suggestions: string[][];
  issueIds: string[];
  originalIssues: any[];
};

export type CustomText = Text & {
  types: EditorIssueType[];
  messages: string[];
  suggestions: string[];
  issueIndices: number[];
  issueIds: string[];
  range: SlateRange;
  originalLengths: number[];
  insertionPosition?: "start" | "end" | "none";
  originalIssues: any[];
  isGrammarError: boolean;
  isInclusiveLanguageError: boolean;
  isSynonymSuggestion: boolean;
  isReadabilityIssue: boolean;
  isSelected: boolean;
};

//
// ========== Component Prop Types ==========
//

export interface ResultsAreaProps {
  analysisResults: AnalysisResultsData | null;
  isLoading: boolean;
  error: string | null;
}

export interface EditorAreaProps {
  analysisResults: AnalysisResultsData | null | undefined;
  onVisibleTextChanged: (text: string) => void;
  shouldAnalyze: boolean;
}

export interface ContentAreaProps {
  analysisResults: AnalysisResultsData | null;
  isLoading: boolean;
  error: string | null;
  onVisibleTextChanged: (text: string) => void;
  shouldAnalyze: boolean;
}

export interface EditorControlsProps {
  onFileUpload: (file: File) => void;
  isLoading: boolean;
}

//
// ========== Context Types ==========
//

export interface AnalysisContextType {
  activeIssueIndex: number | null;
  setActiveIssueIndex: (index: number | null) => void;
  analysisResults: AnalysisResultsData | null;
  isLoading: boolean;
  error: string | null;
  triggerAnalysis: (text: string) => Promise<void>;
}

export interface EditorContextType {
  editorContent: string;
  setEditorContent: (content: string) => void;
}

//
// ========== Utility Types ==========
//

export interface OffsetResult {
  start: number;
  end: number;
}

export interface IssueRangeMeta {
  path: Path;
  originalIssue: any;
}
