import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ORBIT Milestone 13",
  description:
    "ORBIT adaptive committee architecture with llm-first execution, deterministic fallback safety, tiered specialist routing, richer telemetry, and boardroom playback observability.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
