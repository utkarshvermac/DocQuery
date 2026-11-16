import type { Config } from "tailwindcss";

// Palette: a library-reading-room scheme. Cool paper, deep pine ink, and a
// highlighter yellow reserved exclusively for citations - the one memorable
// element of the interface.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: { DEFAULT: "#F3F5F2", raised: "#FBFCFA", sunk: "#E8ECE7" },
        ink: { DEFAULT: "#1C2B27", soft: "#4A5A55", faint: "#7D8B86" },
        pine: { DEFAULT: "#145A4E", dark: "#0E4339", tint: "#DCEBE6" },
        mark: { DEFAULT: "#F6D55C", soft: "#FBEFB8" },
        rule: "#D5DBD6",
        danger: { DEFAULT: "#A4332B", tint: "#F8E4E1" },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "Georgia", "serif"],
      },
      keyframes: {
        flash: { "0%": { backgroundColor: "#F6D55C" }, "100%": { backgroundColor: "#FBFCFA" } },
        pulseDot: { "0%,80%,100%": { opacity: "0.25" }, "40%": { opacity: "1" } },
      },
      animation: {
        flash: "flash 1.2s ease-out",
        dot: "pulseDot 1.2s infinite ease-in-out",
      },
    },
  },
  plugins: [],
};
export default config;
