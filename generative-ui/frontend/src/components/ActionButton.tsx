import { motion } from "framer-motion";
import { Loader2, LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ActionButtonProps {
  label: string;
  onClick: () => void | Promise<void>;
  variant?: "primary" | "secondary" | "ghost";
  icon?: LucideIcon;
  iconPosition?: "left" | "right";
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
}

export const ActionButton = ({
  label,
  onClick,
  variant = "primary",
  icon: Icon,
  iconPosition = "left",
  loading = false,
  disabled = false,
  fullWidth = false,
}: ActionButtonProps) => {
  const variants = {
    primary: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_20px_rgba(212,255,0,0.3)] hover:shadow-[0_0_30px_rgba(212,255,0,0.5)]",
    secondary: "border-2 border-primary bg-transparent text-primary hover:bg-primary/10",
    ghost: "bg-transparent text-primary hover:underline hover:bg-primary/5",
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={fullWidth ? "w-full" : ""}
    >
      <Button
        onClick={onClick}
        disabled={disabled || loading}
        className={`
          ${variants[variant]}
          ${fullWidth ? "w-full" : ""}
          relative overflow-hidden rounded-lg px-6 py-3 
          font-semibold transition-all duration-300
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {loading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <>
            {Icon && iconPosition === "left" && <Icon className="mr-2 h-5 w-5" />}
            <span>{label}</span>
            {Icon && iconPosition === "right" && <Icon className="ml-2 h-5 w-5" />}
          </>
        )}
        
        {/* Ripple effect on click */}
        <motion.span
          className="absolute inset-0 bg-foreground/20"
          initial={{ scale: 0, opacity: 0.5 }}
          whileTap={{ scale: 2, opacity: 0 }}
          transition={{ duration: 0.5 }}
        />
      </Button>
    </motion.div>
  );
};
