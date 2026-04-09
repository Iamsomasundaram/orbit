import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        orbit: {
          ink: "#10231b",
          mist: "#edf4ee",
          moss: "#a7c4a0",
          ember: "#de6b48",
          pine: "#285943",
          gold: "#d6aa55"
        },
      },
      boxShadow: {
        panel: "0 20px 45px rgba(16, 35, 27, 0.12)",
      },
      fontFamily: {
        sans: ["'Segoe UI'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
