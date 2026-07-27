import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import Link from "next/link";
import ClientNav from "./client-nav";
import { Home, Users, Flame, Award } from "lucide-react";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "Authenticity | Political Accountability Platform",
  description: "A neutral, AI-driven registry mapping politician statement consistency.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${playfair.variable} font-sans bg-[#09090b] text-[#f4f4f5] min-h-screen flex`}
      >
        <Providers>
          {/* Main Layout Grid */}
          <div className="flex w-full min-h-screen">
            {/* Sidebar Shell - Fixed on Desktop, hidden on mobile */}
            <aside className="hidden lg:flex w-64 flex-col border-r border-[#202024] bg-[#0c0c0e] shrink-0 sticky top-0 h-screen">
              {/* Branding */}
              <div className="h-16 px-6 border-b border-[#202024] flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2">
                  <span className="font-serif text-xl font-bold tracking-tight text-white">
                    Authenticity<span className="text-orange-500 font-sans">.</span>
                  </span>
                </Link>
                <span className="text-[10px] bg-orange-950/50 text-orange-400 border border-orange-900/30 px-1.5 py-0.5 rounded font-semibold">
                  v1.2.0
                </span>
              </div>

              {/* Navigation */}
              <nav className="flex-1 px-4 py-6 space-y-1">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-400 hover:text-white rounded-lg hover:bg-[#141416] transition-all"
                >
                  <Home className="w-4 h-4" />
                  Dashboard
                </Link>
                <Link
                  href="/politicians"
                  className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-400 hover:text-white rounded-lg hover:bg-[#141416] transition-all"
                >
                  <Users className="w-4 h-4" />
                  Politicians
                </Link>
                <Link
                  href="/contradictions"
                  className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-400 hover:text-white rounded-lg hover:bg-[#141416] transition-all"
                >
                  <Flame className="w-4 h-4" />
                  Inconsistencies
                </Link>
              </nav>

              {/* Footer System Info */}
              <div className="p-4 border-t border-[#202024] bg-[#09090b]/40 text-center">
                <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold flex items-center justify-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-orange-500" />
                  Evidence-First Registry
                </span>
              </div>
            </aside>

            {/* Content Shell */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Header */}
              <header className="h-16 border-b border-[#202024] bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8">
                <div className="flex items-center gap-4">
                  {/* Mobile Logo */}
                  <Link href="/" className="lg:hidden flex items-center gap-1">
                    <span className="font-serif text-lg font-bold tracking-tight text-white">
                      Authenticity<span className="text-orange-500 font-sans">.</span>
                    </span>
                  </Link>
                  
                  {/* Navigation breadcrumbs indicator */}
                  <div className="hidden sm:flex items-center gap-2 text-xs text-gray-500 font-medium">
                    <span>Registry</span>
                    <span>/</span>
                    <span className="text-gray-300">Live Workspace</span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <ClientNav />
                </div>
              </header>

              {/* Main Content Area */}
              <main className="flex-1 flex flex-col bg-[#09090b]">
                {children}
              </main>

              {/* Footer */}
              <footer className="border-t border-[#202024] bg-[#0c0c0e] py-6 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-gray-500">
                  <p>© {new Date().getFullYear()} Authenticity Project. Driven by open-source NLI intelligence.</p>
                  <p>Neutral comparisons, word-level video timestamps, and verifiable citations.</p>
                </div>
              </footer>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
