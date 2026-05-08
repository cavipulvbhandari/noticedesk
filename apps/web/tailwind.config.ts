import type { Config } from "tailwindcss";

// Design tokens: navy / white / slate / gold.
// These match the brand palette specified in the founders' brief; expand only
// with explicit approval. Don't add ad-hoc colors in components.
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
          DEFAULT: "#0B1F3A",
          50: "#E6EAF1",
          100: "#C6D0E0",
          500: "#1E3A6B",
          700: "#0B1F3A",
          900: "#06122A",
        },
        slate: {
          DEFAULT: "#475569",
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          400: "#94A3B8",
          600: "#475569",
          800: "#1E293B",
        },
        gold: {
          DEFAULT: "#C9A24A",
          100: "#F6EBC8",
          500: "#C9A24A",
          700: "#967429",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        serif: ["ui-serif", "Georgia", "serif"],
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
