"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useState } from "react";
import Link from "next/link";
import { RefreshCw, Search, ChevronRight, AlertTriangle } from "lucide-react";

interface Claim {
  id: string;
  claim_text: string;
  category: string;
  created_at: string;
}

interface Contradiction {
  id: string;
  original_claim: Claim;
  contradicting_claim: Claim;
  confidence_score: number;
  explanation: string;
}

const MOCK_CONTRADICTIONS = [
  {
    id: "c1",
    original_claim: { claim_text: "I have never voted to increase state sales tax during my career.", category: "Taxes", created_at: "2026-03-12T10:00:00Z" },
    contradicting_claim: { claim_text: "We must increase state revenue by raising the sales tax rate to 5%.", category: "Taxes", created_at: "2023-10-18T10:00:00Z" },
    confidence_score: 0.942,
    explanation: "Statement B asserts that the politician has never voted for sales tax increases, which conflicts with their prior explicit proposal to raise state sales tax."
  }
];

export default function ContradictionsPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const { data: contradictions, isLoading } = useQuery<Contradiction[]>({
    queryKey: ["all-contradictions", searchTerm],
    queryFn: () => {
      let url = "/admin/contradictions/queue?status=verified"; // Pull verified ones for public
      if (searchTerm) {
        url += `&q=${encodeURIComponent(searchTerm)}`;
      }
      return apiFetch<Contradiction[]>(url).catch(() => MOCK_CONTRADICTIONS);
    },
    initialData: MOCK_CONTRADICTIONS
  });

  return (
    <div className="flex-1 bg-[#0f0f11] py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      <div className="mb-8 pb-4 border-b border-gray-800">
        <h2 className="text-2xl font-bold font-serif leading-7 text-white sm:text-3xl">
          Verified Inconsistencies
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          A neutral public record tracking statements by the same speaker that have been flagged as semantically incompatible.
        </p>
      </div>

      {/* Search Filter */}
      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Filter inconsistencies by keyword..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded bg-[#141417] border border-gray-800 focus:border-orange-500 outline-none text-sm text-white"
        />
      </div>

      {/* Inconsistency List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 text-gray-500 animate-spin" />
        </div>
      ) : contradictions && contradictions.length > 0 ? (
        <div className="space-y-6">
          {contradictions.map((c) => (
            <div key={c.id} className="bg-[#141417] border border-gray-850 rounded-xl p-6 hover:border-gray-800 transition-all">
              <div className="flex items-center justify-between mb-4 border-b border-gray-850 pb-3">
                <span className="text-[10px] bg-orange-950 text-orange-400 font-bold px-2 py-0.5 rounded border border-orange-900/50 uppercase tracking-wider">
                  Category: {c.original_claim.category || "General"}
                </span>
                <span className="text-xs text-gray-500">
                  NLI Confidence: <span className="text-orange-400 font-semibold">{(c.confidence_score * 100).toFixed(1)}%</span>
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <span className="text-[9px] text-gray-500 font-bold uppercase tracking-wider block mb-1">Statement A</span>
                  <p className="text-sm italic text-gray-300 pl-3 border-l border-gray-800 bg-[#0f0f11]/20 py-1">
                    "{c.original_claim.claim_text}"
                  </p>
                </div>
                <div>
                  <span className="text-[9px] text-gray-500 font-bold uppercase tracking-wider block mb-1">Statement B</span>
                  <p className="text-sm italic text-gray-300 pl-3 border-l border-orange-550 bg-[#0f0f11]/20 py-1">
                    "{c.contradicting_claim.claim_text}"
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pt-4 border-t border-gray-850 gap-4">
                <p className="text-xs text-gray-450 flex-1 leading-relaxed">
                  <span className="font-bold text-white">Analysis:</span> {c.explanation}
                </p>
                <Link
                  href={`/contradictions/${c.id}`}
                  className="text-xs font-semibold bg-gray-900 hover:bg-gray-800 border border-gray-800 text-white px-4 py-2 rounded-md flex items-center justify-center gap-1.5 transition-all h-fit"
                >
                  Examine Source Transcripts
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">No inconsistency records match your search.</div>
      )}
    </div>
  );
}
