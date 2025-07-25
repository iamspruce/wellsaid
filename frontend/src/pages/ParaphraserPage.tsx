import { useState } from "react";
import ContentArea from "@/components/layout/ContentArea";
import ParaphraserResults from "@/components/results/ParaphraserResults";
import { useEditorContext } from "@/context/EditorContext";

const ParaphraserPage = () => {
  const { editorContent } = useEditorContext(); // 🔥 Use context directly
  const [result, setResult] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleParaphrase = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:7860/paraphrase/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": "12345",
        },
        body: JSON.stringify({ text: editorContent }), // ← From context
      });

      const data = await res.json();
      setResult(data.paraphrased_text || "");
    } catch (err: any) {
      setError(err.message || "Failed to paraphrase");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full">
      <ContentArea shouldAnalyze={false} />
      <div className="p-4">
        <button
          onClick={handleParaphrase}
          disabled={isLoading}
          className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700"
        >
          {isLoading ? "Paraphrasing..." : "Paraphrase"}
        </button>

        {result && <ParaphraserResults text={result} />}
        {error && <p className="text-red-600 mt-2">{error}</p>}
      </div>
    </div>
  );
};

export default ParaphraserPage;
