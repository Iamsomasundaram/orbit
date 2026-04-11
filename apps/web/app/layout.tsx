import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ORBIT Milestone 10",
  description: "Parallel llm-backed ORBIT committee execution with deterministic fallback and multi-portfolio workspace support.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
