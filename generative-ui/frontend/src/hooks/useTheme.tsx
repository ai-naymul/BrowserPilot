import { useEffect, useState } from "react";

export type Theme = "dark" | "cyberpunk" | "ocean" | "sunset" | "forest" | "lavender";

const themeConfigs: Record<Theme, Record<string, string>> = {
  dark: {
    "--background": "220 18% 3%",        // Very dark neutral (#050608)
    "--foreground": "0 0% 96%",          // Soft white (#f5f5f7)
    "--card": "220 15% 11%",             // Subtle card surface (#181b22)
    "--card-foreground": "0 0% 96%",
    "--popover": "220 15% 11%",
    "--popover-foreground": "0 0% 96%",
    "--primary": "199 95% 74%",          // Soft sky blue (#7dd3fc)
    "--primary-foreground": "220 18% 3%",
    "--secondary": "220 13% 15%",        // Main panel background (#111318)
    "--secondary-foreground": "0 0% 96%",
    "--muted": "220 13% 15%",
    "--muted-foreground": "220 9% 58%",
    "--accent": "199 95% 74%",           // Soft sky blue (same as primary)
    "--accent-foreground": "220 18% 3%",
    "--destructive": "0 65% 60%",
    "--destructive-foreground": "0 0% 96%",
    "--border": "220 15% 18%",           // Subtle cool grey (#2a2f3a)
    "--input": "220 15% 18%",
    "--ring": "199 95% 74%",             // Sky blue focus ring
  },
  cyberpunk: {
    "--background": "280 100% 4%",
    "--foreground": "300 100% 95%",
    "--card": "280 100% 8%",
    "--card-foreground": "300 100% 95%",
    "--popover": "280 100% 8%",
    "--popover-foreground": "300 100% 95%",
    "--primary": "300 100% 50%",
    "--primary-foreground": "280 100% 4%",
    "--secondary": "280 100% 12%",
    "--secondary-foreground": "300 100% 95%",
    "--muted": "280 100% 12%",
    "--muted-foreground": "300 50% 60%",
    "--accent": "180 100% 50%",
    "--accent-foreground": "280 100% 4%",
    "--destructive": "0 84% 60%",
    "--destructive-foreground": "0 0% 98%",
    "--border": "280 50% 20%",
    "--input": "280 50% 20%",
    "--ring": "300 100% 50%",
  },
  ocean: {
    "--background": "200 50% 8%",
    "--foreground": "200 20% 98%",
    "--card": "200 50% 12%",
    "--card-foreground": "200 20% 98%",
    "--popover": "200 50% 12%",
    "--popover-foreground": "200 20% 98%",
    "--primary": "188 94% 43%",
    "--primary-foreground": "200 50% 8%",
    "--secondary": "200 50% 16%",
    "--secondary-foreground": "200 20% 98%",
    "--muted": "200 50% 16%",
    "--muted-foreground": "200 20% 60%",
    "--accent": "217 91% 60%",
    "--accent-foreground": "200 50% 8%",
    "--destructive": "0 84% 60%",
    "--destructive-foreground": "0 0% 98%",
    "--border": "200 30% 20%",
    "--input": "200 30% 20%",
    "--ring": "188 94% 43%",
  },
  sunset: {
    "--background": "20 70% 5%",
    "--foreground": "20 20% 98%",
    "--card": "20 70% 9%",
    "--card-foreground": "20 20% 98%",
    "--popover": "20 70% 9%",
    "--popover-foreground": "20 20% 98%",
    "--primary": "25 95% 53%",
    "--primary-foreground": "20 70% 5%",
    "--secondary": "20 70% 13%",
    "--secondary-foreground": "20 20% 98%",
    "--muted": "20 70% 13%",
    "--muted-foreground": "20 20% 60%",
    "--accent": "330 81% 60%",
    "--accent-foreground": "20 70% 5%",
    "--destructive": "0 84% 60%",
    "--destructive-foreground": "0 0% 98%",
    "--border": "20 40% 15%",
    "--input": "20 40% 15%",
    "--ring": "25 95% 53%",
  },
  forest: {
    "--background": "140 50% 6%",
    "--foreground": "140 20% 98%",
    "--card": "140 50% 10%",
    "--card-foreground": "140 20% 98%",
    "--popover": "140 50% 10%",
    "--popover-foreground": "140 20% 98%",
    "--primary": "142 71% 45%",
    "--primary-foreground": "140 50% 6%",
    "--secondary": "140 50% 14%",
    "--secondary-foreground": "140 20% 98%",
    "--muted": "140 50% 14%",
    "--muted-foreground": "140 20% 60%",
    "--accent": "82 83% 60%",
    "--accent-foreground": "140 50% 6%",
    "--destructive": "0 84% 60%",
    "--destructive-foreground": "0 0% 98%",
    "--border": "140 30% 15%",
    "--input": "140 30% 15%",
    "--ring": "142 71% 45%",
  },
  lavender: {
    "--background": "270 50% 8%",
    "--foreground": "270 20% 98%",
    "--card": "270 50% 12%",
    "--card-foreground": "270 20% 98%",
    "--popover": "270 50% 12%",
    "--popover-foreground": "270 20% 98%",
    "--primary": "271 81% 56%",
    "--primary-foreground": "270 50% 8%",
    "--secondary": "270 50% 16%",
    "--secondary-foreground": "270 20% 98%",
    "--muted": "270 50% 16%",
    "--muted-foreground": "270 20% 60%",
    "--accent": "330 81% 60%",
    "--accent-foreground": "270 50% 8%",
    "--destructive": "0 84% 60%",
    "--destructive-foreground": "0 0% 98%",
    "--border": "270 30% 18%",
    "--input": "270 30% 18%",
    "--ring": "271 81% 56%",
  },
};

export const useTheme = () => {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("app-theme");
    return (saved as Theme) || "dark";
  });

  useEffect(() => {
    const root = document.documentElement;
    const config = themeConfigs[theme];

    Object.entries(config).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });

    localStorage.setItem("app-theme", theme);
  }, [theme]);

  return { theme, setTheme };
};
