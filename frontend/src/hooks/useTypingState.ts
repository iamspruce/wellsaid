import { useRef, useCallback, useEffect } from "react";

/**
 * A hook to track user's typing state and trigger a callback when typing stops.
 *
 * @param onStop - The callback function to execute when typing has stopped.
 * @param delay - The debounce delay in milliseconds.
 * @returns An object with an `onUserType` function to be called on content change.
 */
export const useTypingState = (onStop: () => void, delay: number = 1500) => {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cleanup the timeout when the component unmounts
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const onUserType = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      onStop();
    }, delay);
  }, [onStop, delay]);

  return { onUserType };
};
