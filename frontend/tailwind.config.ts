// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}", "./public/index.html"],
  darkMode: "class", // Enable dark mode using class strategy
  theme: {
    extend: {
      colors: {
        // Base tokens
        background: "var(--color-background)",
        foreground: "var(--color-foreground)",

        // Cards & Popovers
        card: "var(--color-card)",
        "card-foreground": "var(--color-card-foreground)",
        popover: "var(--color-popover)",
        "popover-foreground": "var(--color-popover-foreground)",

        // Brand colors
        primary: "var(--color-primary)",
        "primary-foreground": "var(--color-primary-foreground)",
        secondary: "var(--color-secondary)",
        "secondary-foreground": "var(--color-secondary-foreground)",

        // Utility tones
        muted: "var(--color-muted)",
        "muted-foreground": "var(--color-muted-foreground)",
        accent: "var(--color-accent)",
        "accent-foreground": "var(--color-accent-foreground)",
        destructive: "var(--color-destructive)",

        // Borders and rings
        border: "var(--color-border)",
        input: "var(--color-input)",
        ring: "var(--color-ring)",

        // Charts (if using graphs)
        "chart-1": "var(--color-chart-1)",
        "chart-2": "var(--color-chart-2)",
        "chart-3": "var(--color-chart-3)",
        "chart-4": "var(--color-chart-4)",
        "chart-5": "var(--color-chart-5)",

        // Sidebar-specific
        sidebar: "var(--color-sidebar)",
        "sidebar-foreground": "var(--color-sidebar-foreground)",
        "sidebar-primary": "var(--color-sidebar-primary)",
        "sidebar-primary-foreground": "var(--color-sidebar-primary-foreground)",
        "sidebar-accent": "var(--color-sidebar-accent)",
        "sidebar-accent-foreground": "var(--color-sidebar-accent-foreground)",
        "sidebar-border": "var(--color-sidebar-border)",
        "sidebar-ring": "var(--color-sidebar-ring)",

        // Editor-specific (optional)
        "editor-background": "var(--editor-background)",
        "editor-text": "var(--editor-text)",
        "grammar-help-background": "var(--grammar-help-background)",
        "grammar-help-border": "var(--grammar-help-border)",
        "suggestion-card-background": "var(--suggestion-card-background)",
        "suggestion-card-border": "var(--suggestion-card-border)",
        "suggestion-card-text": "var(--suggestion-card-text)",
        "suggestion-card-muted-text": "var(--suggestion-card-muted-text)",
        "suggestion-card-original-text": "var(--suggestion-card-original-text)",
        "suggestion-card-suggestion-text":
          "var(--suggestion-card-suggestion-text)",
        "button-outline-border": "var(--button-outline-border)",
        "button-outline-text": "var(--button-outline-text)",
        "button-ghost-text": "var(--button-ghost-text)",
        "button-secondary-background": "var(--button-secondary-background)",
        "button-secondary-text": "var(--button-secondary-text)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
      },
    },
  },
  plugins: [],
};

export default config;
