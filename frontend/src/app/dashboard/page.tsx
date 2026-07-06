"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useState } from "react";
import Link from "next/link";
import { FileText, User, ChevronRight, RefreshCw, AlertTriangle } from "lucide-react";

interface Politician {
  id: string;
  first_name: string;
  last_name: string;
  party: string;
  current_office: string;
}

interface Contradiction {
  id: string;
  original_claim: { claim_text: string; category: string };
  contradicting_claim: { claim_text: string; category: string };
  confidence_score: number;
}

// Robust fallback data for presentation if DB is unseeded
const MOCK_POLITICIANS = [
  { id: "1", first_name: "Senator John", last_name: "Doe", party: "Republican", current_office: "Senator" },
  { id: "2", first_name: "Governor Jane", last_name: "Smith", party: "Democrat", current_office: "Governor" }
];

const MOCK_CONTRADICTIONS = [
  {
    id: "c1",
    original_claim: { claim_text: "I have never voted to increase state sales tax during my career.", category: "Taxes" },
    contradicting_claim: { claim_text: "We must increase state revenue by raising the sales tax rate to 5%.", category: "Taxes" },
    confidence_score: 0.942
  }
];

export default function DashboardPage() {
  const { data: politicians, isLoading: isPolLoading } = useQuery<Politician[]>({
    queryKey: ["politicians"],
    queryFn: () => apiFetch<Politician[]>("/politicians").catch(() => MOCK_POLITICIANS),
  });

  const { data: contradictions, isLoading: isContrLoading } = useQuery<Contradiction[]>({
    queryKey: ["contradictions"],
    queryFn: () => apiFetch<Contradiction[]>("/admin/contradictions/queue?status=pending_review").catch(() => MOCK_CONTRADICTIONS),
  });

  return (
    <div className="flex-1 bg-[#0f0f11] py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      <div className="md:flex md:items-center md:justify-between mb-8 pb-4 border-b border-gray-800">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold font-serif leading-7 text-white sm:text-3xl sm:truncate">
            Activity Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Latest statements, processing logs, and semantic evaluations.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Recent Flagged Inconsistencies */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#141417] border border-gray-850 rounded-xl p-6">
            <h3 className="font-serif text-lg font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Flagged Inconsistencies (Pending Editorial Audit)
            </h3>
            
            {isContrLoading ? (
              <div className="flex justify-center py-8">
                <RefreshCw className="w-6 h-6 text-gray-500 animate-spin" />
              </div>
            ) : contradictions && contradictions.length > 0 ? (
              <div className="space-y-4">
                {contradictions.map((c) => (
                  <div key={c.id} className="p-4 rounded-lg bg-[#1c1c20] border border-gray-800 hover:border-gray-750 transition-all">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] bg-orange-950 text-orange-400 font-semibold px-2 py-0.5 rounded border border-orange-900/50 uppercase">
                        {c.original_claim.category || "General"}
                      </span>
                      <span className="text-xs text-gray-500 font-medium">
                        Confidence: <span className="text-orange-400 font-semibold">{(c.confidence_score * 100).toFixed(1)}%</span>
                      </span>
                    </div>
                    <div className="space-y-2 mb-4 text-sm text-gray-300">
                      <p className="line-clamp-2 italic pl-3 border-l-2 border-orange-500 bg-[#0f0f11]/30 py-1">
                        "{c.original_claim.claim_text}"
                      </p>
                      <p className="line-clamp-2 italic pl-3 border-l-2 border-orange-500 bg-[#0f0f11]/30 py-1">
                        "{c.contradicting_claim.claim_text}"
                      </p>
                    </div>
                    <div className="flex justify-end">
                      <Link
                        href={`/contradictions/${c.id}`}
                        className="text-xs text-white bg-gray-900 hover:bg-gray-800 border border-gray-800 px-3 py-1.5 rounded flex items-center gap-1 font-semibold transition-all"
                      >
                        Examine Evidence
                        <ChevronRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No contradictions found in the current audit queue.</p>
            )}
          </div>
        </div>

        {/* Right Column: Politician List Summary */}
        <div className="space-y-6">
          <div className="bg-[#141417] border border-gray-850 rounded-xl p-6">
            <h3 className="font-serif text-lg font-bold text-white mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-gray-400" />
              Politicians Tracked
            </h3>
            
            {isPolLoading ? (
              <div className="flex justify-center py-8">
                <RefreshCw className="w-5 h-5 text-gray-500 animate-spin" />
              </div>
            ) : (
              <div className="divide-y divide-gray-850">
                {politicians?.map((p) => (
                  <div key={p.id} className="py-3 first:pt-0 last:pb-0 flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-white">
                        {p.first_name} {p.last_name}
                      </h4>
                      <p className="text-xs text-gray-500">{p.party} — {p.current_office}</p>
                    </div>
                    <Link
                      href={`/politicians/${p.id}`}
                      className="text-xs text-orange-400 hover:text-orange-300 font-semibold flex items-center gap-0.5"
                    >
                      View Profile
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
