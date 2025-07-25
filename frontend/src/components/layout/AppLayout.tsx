// File: src/components/layout/AppLayout.tsx
import type { ReactNode } from "react";
import { useState, useEffect } from "react";
import Sidebar from "./Sidebar";

const AppLayout = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("theme") || "light";
    }
    return "light";
  });

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.classList.remove("light", "dark");
      document.documentElement.classList.add(theme);
      localStorage.setItem("theme", theme);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === "light" ? "dark" : "light"));
  };

  return (
    <div className={`flex h-screen bg-background text-foreground ${theme}`}>
      <Sidebar toggleTheme={toggleTheme} currentTheme={theme} />
      <section className="flex-1  text-foreground">{children}</section>
    </div>
  );
};

export default AppLayout;
