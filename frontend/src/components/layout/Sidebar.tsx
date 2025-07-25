// File: src/components/layout/Sidebar.tsx
import { Button } from "@/components/ui/button";
import {
  MoonIcon,
  SunIcon,
  SpellCheck,
  Repeat,
  Languages,
  FileText,
} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

interface SidebarProps {
  toggleTheme: () => void;
  currentTheme: string;
}

const Sidebar = ({ toggleTheme, currentTheme }: SidebarProps) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menu = [
    { label: "Grammar checker", path: "/", icon: SpellCheck },
    { label: "Paraphraser", path: "/paraphraser", icon: Repeat },
    { label: "Translator", path: "/translator", icon: Languages },
    { label: "Summariser", path: "/summariser", icon: FileText },
  ];

  return (
    <aside className="w-60  h-full flex flex-col p-4 shadow-l rounded-lg transition-colors duration-200">
      {/* Navigation Menu */}
      <nav className="flex flex-col gap-2 flex-grow">
        {menu.map(({ label, path, icon: Icon }) => (
          <Button
            key={label}
            variant={location.pathname === path ? "secondary" : "ghost"}
            className={`justify-start w-full flex gap-3 items-center rounded-lg py-2 px-3 text-base font-medium
              transition-all duration-300 ease-in-out transform
              ${
                location.pathname === path
                  ? "bg-card-foreground text-accent shadow-lg scale-105"
                  : "text-sidebar-foreground hover:scale-[1.02]"
              }`}
            onClick={() => navigate(path)}
          >
            <Icon size={18} /> {label}
          </Button>
        ))}
      </nav>

      {/* Theme Toggle Button */}
      <div className="mt-auto pt-4 border-t border-sidebar-border">
        <Button
          variant="outline"
          className="w-full flex gap-3 items-center border-sidebar-border text-sidebar-foreground rounded-lg shadow-md
            hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-300 ease-in-out transform hover:scale-[1.02]"
          onClick={toggleTheme}
        >
          {currentTheme === "dark" ? (
            <SunIcon size={18} />
          ) : (
            <MoonIcon size={18} />
          )}
          {currentTheme === "dark" ? "Light Mode" : "Dark Mode"}
        </Button>
      </div>
    </aside>
  );
};

export default Sidebar;
