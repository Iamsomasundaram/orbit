import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ORBIT Milestone 14",
  description:
    "ORBIT evidence-based committee reasoning with claim-evidence-risk chains, confidence scoring, and audit-ready playback.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
