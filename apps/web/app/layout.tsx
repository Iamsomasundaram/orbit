import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ORBIT Milestone 12.2",
  description: "ORBIT platform hardening with reliable submission and review actions, deterministic fallback safety, richer telemetry, browser automation coverage, and committee playback observability.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
