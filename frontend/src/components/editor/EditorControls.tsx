import React, { useRef } from "react";
import { Upload } from "lucide-react";
import type { EditorControlsProps } from "@/types";

const EditorControls: React.FC<EditorControlsProps> = ({
  onFileUpload,
  isLoading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="absolute bottom-6 right-6 flex gap-3 z-10">
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => e.target.files && onFileUpload(e.target.files[0])}
        className="hidden"
        accept=".txt,.md"
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={isLoading}
        aria-label="Upload file"
        className="flex items-center justify-center px-4 py-2 bg-muted border-sidebar-border text-sidebar-foreground rounded-lg shadow-md
            hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-300 ease-in-out transform hover:scale-[1.02]"
      >
        <Upload size={16} className="mr-2" />
        {isLoading ? "Uploading..." : "Upload"}
      </button>
    </div>
  );
};

export default EditorControls;
