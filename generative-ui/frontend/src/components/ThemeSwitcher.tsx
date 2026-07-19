import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Palette, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Theme } from "@/hooks/useTheme";

interface ThemeOption {
  id: Theme;
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

const themes: ThemeOption[] = [
  {
    id: "dark",
    name: "Dark (Default)",
    colors: {
      primary: "#7dd3fc",  // Soft sky blue
      secondary: "#181b22",
      accent: "#7dd3fc",   // Soft sky blue
    },
  },
  {
    id: "ocean",
    name: "Ocean",
    colors: {
      primary: "#7dd3fc",
      secondary: "#0c1e2e",
      accent: "#38bdf8",
    },
  },
  {
    id: "sunset",
    name: "Sunset",
    colors: {
      primary: "#f9a8d4",
      secondary: "#1a0f0a",
      accent: "#c4b5fd",
    },
  },
  {
    id: "forest",
    name: "Forest",
    colors: {
      primary: "#22c55e",
      secondary: "#0a1f0f",
      accent: "#84cc16",
    },
  },
];

interface ThemeSwitcherProps {
  currentTheme: Theme;
  onThemeChange: (theme: Theme) => void;
}

export const ThemeSwitcher = ({ currentTheme, onThemeChange }: ThemeSwitcherProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            className="absolute bottom-full right-0 mb-4 w-80 rounded-xl border border-border bg-card p-4 shadow-2xl backdrop-blur-xl"
          >
            <h3 className="mb-3 text-sm font-semibold text-foreground">Choose Theme</h3>
            <div className="grid grid-cols-2 gap-2">
              {themes.map((theme) => (
                <motion.button
                  key={theme.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    onThemeChange(theme.id);
                    setIsOpen(false);
                  }}
                  className={`relative rounded-lg border-2 p-3 text-left transition-all ${
                    currentTheme === theme.id
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="mb-2 flex items-center gap-2">
                    <div className="flex gap-1">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: theme.colors.primary }}
                      />
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: theme.colors.accent }}
                      />
                    </div>
                    {currentTheme === theme.id && (
                      <Check className="ml-auto h-4 w-4 text-primary" />
                    )}
                  </div>
                  <p className="text-xs font-medium text-foreground">{theme.name}</p>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
        <Button
          onClick={() => setIsOpen(!isOpen)}
          size="icon"
          className="h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 hover:shadow-[0_0_30px_rgba(212,255,0,0.5)]"
        >
          <Palette className="h-6 w-6" />
        </Button>
      </motion.div>
    </div>
  );
};
