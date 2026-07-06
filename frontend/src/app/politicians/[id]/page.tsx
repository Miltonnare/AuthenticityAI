"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, User, Calendar, ExternalLink, RefreshCw, AlertTriangle } from "lucide-react";

interface Politician {
  id: string;
  first_name: string;
  last_name: string;
  party: string;
  current_office: string;
  bio: string;
}

interface Claim {
  id: string;
  claim_text: string;
  category: string;
  created_at: string;
  speech_id: string;
}

// Fallback data
const MOCK_POLITICIAN = {
  id: "1",
  first_name: "John",
  last_name: "Doe",
  party: "Republican",
  current_office: "Senator",
  bio: "Senator John Doe has served in public office for over a decade. His focus areas include state revenues, economic growth, and regional trade infrastructure."
};

const MOCK_TIMELINE_CLAIMS: Claim[] = [
  {
    id: "claim-101",
    claim_text: "I have never voted to increase state sales tax during my career.",
    category: "Taxes",
    created_at: "2026-03-12T10:00:00Z",
    speech_id: "speech-1"
  },
  {
    id: "claim-102",
    claim_text: "We must increase state revenue by raising the sales tax rate to 5%.",
    category: "Taxes",
    created_at: "2023-10-18T10:00:00Z",
    speech_id: "speech-2"
  }
];

export default function PoliticianProfilePage() {
  const params = useParams();
  const id = params.id as string;

  const { data: politician, isLoading: isPolLoading } = useQuery<Politician>({
    queryKey: ["politician", id],
    queryFn: () => apiFetch<Politician>(`/politicians/${id}`).catch(() => MOCK_POLITICIAN),
  });

  const { data: claims, isLoading: isClaimsLoading } = useQuery<Claim[]>({
    queryKey: ["politician-timeline", id],
    queryFn: () => apiFetch<Claim[]>(`/politicians/${id}/timeline`).catch(() => MOCK_TIMELINE_CLAIMS),
  });

  if (isPolLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#0f0f11]">
        <RefreshCw className="w-8 h-8 text-gray-500 animate-spin" />
      </div>
    );
  }

  const p = politician || MOCK_POLITICIAN;

  return (
    <div className="flex-1 bg-[#0f0f11] py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full">
      <div className="mb-6">
        <Link
          href="/politicians"
          className="text-xs font-semibold text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Directory
        </Link>
      </div>

      {/* Profile Header */}
      <div className="bg-[#141417] border border-gray-850 rounded-xl p-6 mb-8 flex flex-col md:flex-row gap-6 items-start">
        <div className="w-16 h-16 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-450 font-serif text-2xl font-bold">
          {p.first_name[0]}{p.last_name[0]}
        </div>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <h1 className="font-serif text-2xl sm:text-3xl font-bold text-white">
              {p.first_name} {p.last_name}
            </h1>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
                p.party.toLowerCase() === "democrat"
                  ? "bg-blue-950/40 text-blue-400 border-blue-900/30"
                  : p.party.toLowerCase() === "republican"
                  ? "bg-red-950/40 text-red-400 border-red-900/30"
                  : "bg-gray-800 text-gray-300 border-gray-700"
              }`}
            >
              {p.party}
            </span>
          </div>
          <p className="text-sm text-gray-400 font-medium mb-4">{p.current_office}</p>
          <p className="text-gray-300 text-sm leading-relaxed max-w-3xl">{p.bio}</p>
        </div>
      </div>

      {/* Statement Timeline */}
      <h2 className="font-serif text-xl font-bold text-white mb-6">Statement Evolution Timeline</h2>
      
      {isClaimsLoading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-6 h-6 text-gray-500 animate-spin" />
        </div>
      ) : claims && claims.length > 0 ? (
        <div className="relative border-l border-gray-800 ml-4 pl-8 space-y-8">
          {claims.map((claim) => {
            // In our mock fallback, claim-101 and claim-102 have a contradiction link.
            const hasContradiction = claim.id === "claim-101" || claim.id === "claim-102";
            
            return (
              <div key={claim.id} className="relative">
                {/* Timeline Dot */}
                <span className="absolute -left-[41px] top-1.5 flex h-6 h-6 items-center justify-center rounded-full bg-[#0f0f11] border-2 border-gray-800">
                  <span className={`h-2 w-2 rounded-full ${hasContradiction ? "bg-orange-500" : "bg-gray-500"}`} />
                </span>

                <div className="bg-[#141417] border border-gray-850 rounded-xl p-5 hover:border-gray-800 transition-all">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-xs text-gray-450">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{new Date(claim.created_at).toLocaleDateString()}</span>
                      <span className="text-gray-600">|</span>
                      <span className="text-orange-400 font-semibold">{claim.category || "General"}</span>
                    </div>
                    {hasContradiction && (
                      <span className="inline-flex items-center gap-1 text-[10px] bg-orange-950/40 border border-orange-900/30 text-orange-400 px-2.5 py-0.5 rounded font-semibold uppercase tracking-wider">
                        <AlertTriangle className="w-3 h-3" />
                        Inconsistency Flagged
                      </span>
                    )}
                  </div>
                  
                  <p className="text-gray-200 text-sm font-medium italic mb-4">
                    "{claim.claim_text}"
                  </p>

                  <div className="flex items-center justify-between pt-3 border-t border-gray-850">
                    <span className="text-xs text-gray-500">
                      Source: Ingested Speech Segment
                    </span>
                    <div className="flex gap-3">
                      {hasContradiction && (
                        <Link
                          href="/contradictions/c1"
                          className="text-xs font-semibold text-orange-400 hover:text-orange-300 flex items-center gap-1"
                        >
                          Compare Statements
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">No statements have been ingested for this politician yet.</div>
      )}
    </div>
  );
}
