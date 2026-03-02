import React from "react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  href?: string;
}

export function Button({ 
  className, 
  variant = "primary", 
  size = "md", 
  children,
  href,
  ...props 
}: ButtonProps) {
  const baseStyles = "relative font-mono uppercase text-sm font-bold tracking-wider transition-all inline-flex items-center justify-center gap-3 overflow-hidden group";
  
  const variants = {
    primary: "bg-accent text-white shadow-[4px_4px_0_rgba(255,255,255,0.15)] hover:-translate-y-1 hover:-translate-x-1 hover:shadow-[6px_6px_0_rgba(255,62,0,0.4)] hover:bg-accent-hover",
    secondary: "bg-white text-black shadow-[4px_4px_0_rgba(255,62,0,0.5)] hover:-translate-y-1 hover:-translate-x-1 hover:shadow-[6px_6px_0_rgba(255,62,0,0.8)]",
    outline: "border-2 border-white/20 hover:border-accent hover:text-accent hover:bg-accent/5",
    ghost: "hover:bg-white/5 text-zinc-400 hover:text-white"
  };

  const sizes = {
    sm: "px-4 py-2 text-xs",
    md: "px-8 py-4",
    lg: "px-10 py-5 text-base",
  };

  const innerContent = (
    <>
      <span className="relative z-10 flex items-center gap-2">{children}</span>
      {variant === "primary" && (
        <div className="absolute inset-0 h-full w-full translate-y-[100%] bg-white/20 transition-transform duration-300 ease-out group-hover:translate-y-[0%]" />
      )}
    </>
  );

  const finalClassName = cn(baseStyles, variants[variant], sizes[size], className);

  if (href) {
    return (
      <Link href={href} className={finalClassName}>
        {innerContent}
      </Link>
    );
  }

  return (
    <button className={finalClassName} {...props}>
      {innerContent}
    </button>
  );
}
