import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AgentProvider } from "@/context/AgentContext";
import { AppLayout } from "@/components/layout/AppLayout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Agentium | Neural Multi-Agent Platform",
  description: "Advanced multi-agent AI orchestration and training dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#030712] text-slate-200 antialiased selection:bg-indigo-500/30`}>
        <AgentProvider>
          <AppLayout>
            {children}
          </AppLayout>
        </AgentProvider>
      </body>
    </html>
  );
}
