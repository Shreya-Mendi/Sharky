import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DealScope — AI-Powered Business Intelligence",
  description: "Turn venture pitch data into actionable business intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[var(--bg-primary)] text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
