import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle } from "lucide-react";

interface ParaphraserResultsProps {
  text: string | undefined;
  isLoading?: boolean;
  error?: string | null;
}

const ParaphraserResults = ({
  text,
  isLoading = false,
  error = null,
}: ParaphraserResultsProps) => {
  if (isLoading) {
    return (
      <div className="mt-4 p-4">
        <Skeleton className="h-6 w-1/2 mb-2" />
        <Skeleton className="h-4 w-full mb-1" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 flex items-center gap-2 text-sm">
        <AlertTriangle className="w-4 h-4" />
        Error loading paraphrased text: {error}
      </div>
    );
  }

  if (!text) {
    return (
      <div className="text-sm text-muted-foreground px-4 py-4">
        No paraphrased text available.
      </div>
    );
  }

  return (
    <div className="mt-4 p-4 bg-muted rounded-lg border text-foreground">
      <h3 className="font-semibold mb-2">Paraphrased Text:</h3>
      <p>{text}</p>
    </div>
  );
};

export default ParaphraserResults;
