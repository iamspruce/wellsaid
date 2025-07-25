// confidence-indicator.tsx
"use client";

import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Shield, ShieldCheck, ShieldAlert } from "lucide-react";

interface ConfidenceIndicatorProps {
  confidence: number;
  size?: "sm" | "md" | "lg";
}

const ConfidenceIndicator = ({
  confidence,
  size = "md",
}: ConfidenceIndicatorProps) => {
  const getConfidenceConfig = (conf: number) => {
    if (conf >= 90) {
      return {
        label: "High Confidence",
        color: "bg-green-100 text-green-800 border-green-200",
        icon: ShieldCheck,
        iconColor: "text-green-600",
        description: "This suggestion is highly reliable",
      };
    } else if (conf >= 70) {
      return {
        label: "Medium Confidence",
        color: "bg-yellow-100 text-yellow-800 border-yellow-200",
        icon: Shield,
        iconColor: "text-yellow-600",
        description: "This suggestion is moderately reliable",
      };
    } else {
      return {
        label: "Low Confidence",
        color: "bg-red-100 text-red-800 border-red-200",
        icon: ShieldAlert,
        iconColor: "text-red-600",
        description: "This suggestion may need review",
      };
    }
  };

  const config = getConfidenceConfig(confidence);
  const Icon = config.icon;

  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-xs px-2.5 py-1.5",
    lg: "text-sm px-3 py-2",
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={`${config.color} ${sizeClasses[size]} flex items-center gap-1`}
          >
            <Icon className="w-3 h-3" />
            {confidence}%
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>{config.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ConfidenceIndicator;
