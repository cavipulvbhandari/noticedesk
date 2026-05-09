import type { Config } from "tailwindcss";

// Design tokens are the prototype's ground truth (noticedesk_prototype.html).
// Don't introduce new color names without updating the prototype first.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#1A2A4A",
          deep: "#0F1A33",
        },
        gold: {
          DEFAULT: "#B08D57",
          dark: "#8C6F44",
        },
        cream: "#F5F0E8",
        paper: "#FAF7F2",
        ink: "#16181D",
        slate: "#6B6E78",
        success: "#2D6A4F",
        alarm: "#9C2A2A",
        warn: "#C68B3D",
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "Fraunces", "Georgia", "serif"],
        sans: ["var(--font-dm-sans)", "DM Sans", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
