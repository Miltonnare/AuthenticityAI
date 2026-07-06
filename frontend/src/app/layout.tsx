import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import Link from "next/link";
import ClientNav from "./client-nav";

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
        className={`${inter.variable} ${playfair.variable} font-sans bg-[#0f0f11] text-gray-100 min-h-screen flex flex-col`}
      >
        <Providers>
          {/* Header */}
          <header className="border-b border-gray-800 bg-[#0f0f11]/80 backdrop-blur-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
              <div className="flex items-center gap-8">
                <Link href="/" className="flex items-center gap-2">
                  <span className="font-serif text-2xl font-bold tracking-tight text-white">
                    Authenticity<span className="text-orange-500 font-sans">.</span>
                  </span>
                </Link>
                <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-400">
                  <Link href="/dashboard" className="hover:text-white transition-colors">
                    Dashboard
                  </Link>
                  <Link href="/politicians" className="hover:text-white transition-colors">
                    Politicians
                  </Link>
                  <Link href="/contradictions" className="hover:text-white transition-colors">
                    Inconsistencies
                  </Link>
                </nav>
              </div>
              <ClientNav />
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 flex flex-col">{children}</main>

          {/* Footer */}
          <footer className="border-t border-gray-800 bg-[#0c0c0e] py-8">
            <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
              <p>© {new Date().getFullYear()} Authenticity Project. Driven by open-source NLI intelligence.</p>
              <p className="mt-2 text-xs">
                This platform is dedicated to transparency, neutral statement comparisons, and verifiable citations.
              </p>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
