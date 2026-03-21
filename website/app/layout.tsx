import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "F1 Telemetry Intelligence System",
  description:
    "Real-time race analysis focused on overtaking, defense, and driver decision-making.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
