"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Flame, FileText, CheckCircle, HelpCircle } from "lucide-react";

export default function LandingPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/dashboard?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center bg-[#0f0f11]">
      {/* Hero Section */}
      <section className="w-full max-w-5xl mx-auto px-4 py-20 text-center flex flex-col items-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-950/40 border border-orange-900/30 text-orange-400 text-xs font-semibold mb-6">
          <Flame className="w-3.5 h-3.5" />
          Neutral Statement Consistency Registry
        </div>
        <h1 className="font-serif text-4xl sm:text-6xl font-bold tracking-tight text-white max-w-3xl leading-[1.15] mb-6">
          Hold Public Assertions to the Test of Time.
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mb-10 leading-relaxed">
          Authenticity indexes statements, computes semantic vectors, and flags inconsistencies.
          No accusations, no bias—just facts, transcripts, and NLI verification.
        </p>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="w-full max-w-2xl flex items-center gap-2 mb-16">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="Search statements (e.g., taxes, carbon emission, health care)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3.5 rounded-lg bg-[#141417] border border-gray-800 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none text-white text-base transition-all"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3.5 bg-orange-600 hover:bg-orange-500 text-white font-semibold rounded-lg transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-orange-950/20"
          >
            Search
          </button>
        </form>

        {/* Core Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full border-t border-gray-900 pt-16">
          <div className="text-left">
            <div className="w-10 h-10 rounded-lg bg-orange-950/50 border border-orange-900/30 flex items-center justify-center text-orange-400 mb-4">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-lg font-bold text-white mb-2">1. Ingest & Transcribe</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Ingest press conferences, debates, and hearings. WhisperX provides word-level timestamps directly mapping statements to specific video clips.
            </p>
          </div>
          <div className="text-left">
            <div className="w-10 h-10 rounded-lg bg-orange-950/50 border border-orange-900/30 flex items-center justify-center text-orange-400 mb-4">
              <CheckCircle className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-lg font-bold text-white mb-2">2. Extract Claims</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Extract explicit claims, sanitizing filler statements. Dense vectors encode semantic meaning, indexing assertions by topic and core assertion.
            </p>
          </div>
          <div className="text-left">
            <div className="w-10 h-10 rounded-lg bg-orange-950/50 border border-orange-900/30 flex items-center justify-center text-orange-400 mb-4">
              <HelpCircle className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-lg font-bold text-white mb-2">3. Cross-Verify</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Natural Language Inference (NLI) compares new claims with historical statements, detecting contradictions based purely on language logic.
            </p>
          </div>
        </div>
      </section>

      {/* Info Callout Section */}
      <section className="w-full bg-[#0c0c0e] border-t border-gray-900 py-16">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="font-serif text-3xl font-bold text-white mb-6">
              Our Principles: Explanations Over Accusations
            </h2>
            <p className="text-gray-400 leading-relaxed mb-4">
              The platform never labels a public official a "liar" or calls statements "false." 
              Instead, it flags where statements appear semantically incompatible.
            </p>
            <p className="text-gray-400 leading-relaxed">
              Each flagged inconsistency features side-by-side statements, direct video clips with exact timestamps, and an AI confidence breakdown so you can judge the context yourself.
            </p>
            <div className="mt-8 flex gap-4">
              <Link
                href="/politicians"
                className="px-5 py-2.5 bg-gray-900 hover:bg-gray-800 border border-gray-800 text-white font-medium rounded-md transition-all text-sm"
              >
                Browse Politicians
              </Link>
              <Link
                href="/dashboard"
                className="px-5 py-2.5 bg-orange-650 hover:bg-orange-600 text-white font-medium rounded-md transition-all text-sm"
              >
                View Activity Dashboard
              </Link>
            </div>
          </div>
          <div className="rounded-xl bg-[#141417] border border-gray-800 p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-800">
              <div className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
              <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Live Processing Statistics</span>
            </div>
            <div className="space-y-6">
              <div>
                <span className="text-sm text-gray-500">Statements Monitored</span>
                <div className="text-3xl font-serif font-bold text-white mt-1">12,450+</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-500">Politicians Tracked</span>
                  <div className="text-xl font-bold text-white mt-0.5">84</div>
                </div>
                <div>
                  <span className="text-sm text-gray-500">NLI Comparisons Run</span>
                  <div className="text-xl font-bold text-white mt-0.5">148.9k</div>
                </div>
              </div>
              <div className="p-4 rounded bg-[#1c1c20] border border-gray-800">
                <span className="text-xs text-gray-400 font-semibold uppercase block mb-1">NLI Model Running</span>
                <span className="text-xs font-mono text-orange-400">cross-encoder/nli-deberta-v3-xsmall</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
