import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NoticeDesk",
  description:
    "Litigation-first tax operating system for Indian CA firms — GST and Income Tax.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen bg-slate-50 text-navy antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
