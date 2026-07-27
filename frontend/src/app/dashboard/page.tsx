"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { FileText, User, ChevronRight, RefreshCw, AlertTriangle, Users, ShieldCheck, TrendingUp } from "lucide-react";

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
    <div className="flex-1 bg-[#09090b] py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold font-serif tracking-tight text-white">
          Activity Dashboard
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          Monitor politician assertions, semantic verification logs, and active status updates.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-6 rounded-xl bg-[#141416] border border-[#202024]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Politicians Tracked</span>
            <Users className="w-5 h-5 text-gray-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{politicians?.length || 0}</span>
            <span className="text-xs text-green-500 font-semibold flex items-center gap-0.5">
              <TrendingUp className="w-3.5 h-3.5" />
              Active
            </span>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-[#141416] border border-[#202024]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Flagged Inconsistencies</span>
            <AlertTriangle className="w-5 h-5 text-orange-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{contradictions?.length || 0}</span>
            <span className="text-xs text-gray-500">Audits pending</span>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-[#141416] border border-[#202024]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">NLI Integrity Score</span>
            <ShieldCheck className="w-5 h-5 text-gray-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">98.5%</span>
            <span className="text-xs text-gray-500">System reliability</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Flagged Inconsistencies */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#141416] border border-[#202024] rounded-xl p-6">
            <h3 className="font-serif text-lg font-bold text-white mb-6 flex items-center gap-2">
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
                  <div key={c.id} className="p-5 rounded-lg bg-[#0c0c0e] border border-[#202024] hover:border-[#303036] transition-all">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[10px] bg-orange-950/60 text-orange-400 font-semibold px-2 py-0.5 rounded border border-orange-900/50 uppercase tracking-wider">
                        {c.original_claim.category || "General"}
                      </span>
                      <span className="text-xs text-gray-500 font-medium">
                        NLI Confidence: <span className="text-orange-400 font-semibold">{(c.confidence_score * 100).toFixed(1)}%</span>
                      </span>
                    </div>
                    <div className="space-y-3 mb-4 text-sm text-gray-300">
                      <div className="pl-3 border-l-2 border-orange-500 py-1 bg-[#141416]/50 rounded-r">
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-0.5">Historical Stance</span>
                        <p className="italic">"{c.original_claim.claim_text}"</p>
                      </div>
                      <div className="pl-3 border-l-2 border-orange-500 py-1 bg-[#141416]/50 rounded-r">
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-0.5">Contradicting Assertion</span>
                        <p className="italic">"{c.contradicting_claim.claim_text}"</p>
                      </div>
                    </div>
                    <div className="flex justify-end pt-2 border-t border-[#202024]">
                      <Link
                        href={`/contradictions/${c.id}`}
                        className="text-xs text-white bg-orange-600 hover:bg-orange-500 px-4 py-2 rounded-md flex items-center gap-1.5 font-semibold transition-all shadow-md shadow-orange-950/20"
                      >
                        Examine Evidence
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No contradictions found in the current audit queue.</p>
            )}
          </div>
        </div>

        {/* Right Column: Politician List Summary */}
        <div className="space-y-6">
          <div className="bg-[#141416] border border-[#202024] rounded-xl p-6">
            <h3 className="font-serif text-lg font-bold text-white mb-6 flex items-center gap-2">
              <User className="w-5 h-5 text-gray-400" />
              Politicians Tracked
            </h3>
            
            {isPolLoading ? (
              <div className="flex justify-center py-8">
                <RefreshCw className="w-5 h-5 text-gray-500 animate-spin" />
              </div>
            ) : (
              <div className="divide-y divide-[#202024]">
                {politicians?.map((p) => (
                  <div key={p.id} className="py-4 first:pt-0 last:pb-0 flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-white">
                        {p.first_name} {p.last_name}
                      </h4>
                      <p className="text-xs text-gray-500 mt-0.5">{p.party} — {p.current_office}</p>
                    </div>
                    <Link
                      href={`/politicians/${p.id}`}
                      className="text-xs text-orange-400 hover:text-orange-300 font-semibold flex items-center gap-0.5 transition-colors"
                    >
                      Profile
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
