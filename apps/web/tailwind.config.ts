import type { Config } from "tailwindcss";

// Design tokens — ported from the founders' clickable prototype (Sprint 4).
//
// The prototype's palette is a tighter, paper-and-ink variant of the brief's
// navy/white/slate/gold scheme. Existing Sprint 1-3 pages (inbox, dashboard)
// keep working because every token they use (navy, slate-100/200/400/600,
// gold, gold-700) still exists; only the DEFAULT shades shift to the
// prototype's values. The added cream/paper/ink/alarm/warn families are
// available for any new component but not required by old ones.
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
          50: "#E6EAF1",
          100: "#C6D0E0",
          500: "#2A3A5F",
          700: "#1A2A4A",
          900: "#0F1A33",
          deep: "#0F1A33",
          rail: "#14213D",
          soft: "#2A3A5F",
        },
        cream: "#F5F0E8",
        paper: {
          DEFAULT: "#FAF7F2",
          tint: "#EFE8DA",
          warm: "#F2EBDC",
        },
        ink: {
          DEFAULT: "#16181D",
          soft: "#2C2F38",
        },
        slate: {
          DEFAULT: "#6B6E78",
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          400: "#94A3B8",
          600: "#475569",
          800: "#1E293B",
          soft: "#8C8F98",
          pale: "#C5C0BB",
          line: "#E5DFD5",
        },
        gold: {
          DEFAULT: "#B08D57",
          100: "#F6EBC8",
          500: "#B08D57",
          700: "#8C6F44",
          dark: "#8C6F44",
          soft: "#D4B988",
          pale: "#E8DDC8",
        },
        success: {
          DEFAULT: "#2D6A4F",
          soft: "#5A8B70",
          bg: "#E8F0EB",
        },
        alarm: {
          DEFAULT: "#9C2A2A",
          soft: "#B85555",
          bg: "#F4E5E5",
        },
        warn: {
          DEFAULT: "#C68B3D",
          bg: "#F6EBD9",
        },
      },
      fontFamily: {
        sans: [
          "DM Sans",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        serif: ["Fraunces", "ui-serif", "Georgia", "serif"],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      borderRadius: {
        sm: "3px",
        md: "5px",
        lg: "8px",
      },
      boxShadow: {
        "card-sm": "0 1px 2px rgba(26, 42, 74, 0.04)",
        "card-md":
          "0 2px 8px rgba(26, 42, 74, 0.06), 0 1px 2px rgba(26, 42, 74, 0.04)",
        "card-lg":
          "0 12px 32px rgba(26, 42, 74, 0.10), 0 4px 12px rgba(26, 42, 74, 0.05)",
        "card-xl": "0 24px 60px rgba(26, 42, 74, 0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
