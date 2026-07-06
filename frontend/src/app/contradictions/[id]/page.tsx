"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/auth-store";
import { ArrowLeft, Play, ShieldAlert, CheckCircle, Trash2, Calendar, HelpCircle, RefreshCw } from "lucide-react";

interface Claim {
  id: string;
  claim_text: string;
  category: string;
  created_at: string;
}

interface Contradiction {
  id: string;
  original_claim_id: string;
  contradicting_claim_id: string;
  original_claim: Claim;
  contradicting_claim: Claim;
  confidence_score: number;
  explanation: string;
  review_status: string;
}

// Fallback Mock data
const MOCK_CONTRADICTION: Contradiction = {
  id: "c1",
  original_claim_id: "claim-102",
  contradicting_claim_id: "claim-101",
  original_claim: {
    id: "claim-102",
    claim_text: "We must increase state revenue by raising the sales tax rate to 5%.",
    category: "Taxes",
    created_at: "2023-10-18T10:00:00Z"
  },
  contradicting_claim: {
    id: "claim-101",
    claim_text: "I have never voted to increase state sales tax during my career.",
    category: "Taxes",
    created_at: "2026-03-12T10:00:00Z"
  },
  confidence_score: 0.942,
  explanation: "Statement B (delivered in 2026) asserts that the politician has 'never voted' or supported sales tax rate hikes. However, Statement A (delivered in 2023) is a direct, explicit proposal arguing in favor of increasing the state sales tax rate to 5%. The assertions are semantically incompatible.",
  review_status: "pending_review"
};

export default function ContradictionDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();
  const { user } = useAuthStore();

  const { data: contradiction, isLoading, refetch } = useQuery<Contradiction>({
    queryKey: ["contradiction", id],
    queryFn: () => apiFetch<Contradiction>(`/contradictions/${id}`).catch(() => MOCK_CONTRADICTION),
  });

  const reviewMutation = useMutation({
    mutationFn: (status: "verified" | "dismissed") =>
      apiFetch(`/admin/contradictions/${id}/review`, {
        method: "POST",
        json: { review_status: status },
      }),
    onSuccess: () => {
      refetch();
      router.push("/dashboard");
    },
    onError: (err) => {
      alert(`Failed to review contradiction: ${err.message}`);
    }
  });

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#0f0f11]">
        <RefreshCw className="w-8 h-8 text-gray-500 animate-spin" />
      </div>
    );
  }

  const c = contradiction || MOCK_CONTRADICTION;
  const isModerator = user?.role === "admin" || user?.role === "journalist";

  return (
    <div className="flex-1 bg-[#0f0f11] py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full">
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/dashboard"
          className="text-xs font-semibold text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </Link>
        <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider bg-gray-900 border border-gray-800 px-3 py-1 rounded">
          Record ID: #{c.id}
        </span>
      </div>

      {/* Intro Header */}
      <div className="bg-[#141417] border border-gray-850 rounded-xl p-6 mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold text-white mb-2">Statement Comparison Analysis</h1>
          <p className="text-sm text-gray-400">
            NLI evaluation has detected a potential semantic contradiction between two statements.
          </p>
        </div>
        <div className="bg-orange-950/40 border border-orange-900/40 rounded-lg p-4 text-center">
          <span className="text-xs text-orange-400 font-semibold block mb-1">NLI Inconsistency Confidence</span>
          <span className="text-3xl font-bold text-white font-mono">{(c.confidence_score * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Side-by-Side statements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* Statement A */}
        <div className="bg-[#141417] border border-gray-850 rounded-xl overflow-hidden flex flex-col justify-between">
          <div className="p-6">
            <span className="text-[10px] bg-gray-800 text-gray-400 font-bold px-2 py-0.5 rounded uppercase tracking-wider mb-4 inline-block">
              Statement A (Earlier)
            </span>
            <p className="text-lg italic font-serif font-semibold text-white leading-relaxed mb-6">
              "{c.original_claim.claim_text}"
            </p>
            <div className="space-y-3 text-xs text-gray-450">
              <div className="flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5 text-gray-500" />
                <span>Delivered: {new Date(c.original_claim.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <HelpCircle className="w-3.5 h-3.5 text-gray-500" />
                <span>Context: Congressional / Executive Assembly Hearing</span>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-850 bg-[#0c0c0e]/30 px-6 py-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">Video Timestamp: 01:14:22</span>
            <button className="text-xs font-semibold text-white bg-gray-900 border border-gray-800 hover:bg-gray-800 px-3 py-1.5 rounded flex items-center gap-1.5 transition-all cursor-pointer">
              <Play className="w-3 h-3 text-orange-500 fill-orange-500" />
              Play Segment
            </button>
          </div>
        </div>

        {/* Statement B */}
        <div className="bg-[#141417] border border-gray-850 rounded-xl overflow-hidden flex flex-col justify-between">
          <div className="p-6">
            <span className="text-[10px] bg-orange-950 text-orange-400 font-bold px-2 py-0.5 rounded border border-orange-900/50 uppercase tracking-wider mb-4 inline-block">
              Statement B (Latter)
            </span>
            <p className="text-lg italic font-serif font-semibold text-white leading-relaxed mb-6">
              "{c.contradicting_claim.claim_text}"
            </p>
            <div className="space-y-3 text-xs text-gray-450">
              <div className="flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5 text-gray-500" />
                <span>Delivered: {new Date(c.contradicting_claim.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <HelpCircle className="w-3.5 h-3.5 text-gray-500" />
                <span>Context: Live Television / Press Broadcast</span>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-850 bg-[#0c0c0e]/30 px-6 py-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">Video Timestamp: 12:45</span>
            <button className="text-xs font-semibold text-white bg-gray-900 border border-gray-800 hover:bg-gray-800 px-3 py-1.5 rounded flex items-center gap-1.5 transition-all cursor-pointer">
              <Play className="w-3 h-3 text-orange-500 fill-orange-500" />
              Play Segment
            </button>
          </div>
        </div>
      </div>

      {/* Explanation Box */}
      <div className="bg-[#141417] border border-gray-850 rounded-xl p-6 mb-8">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3">AI Logical Reconciliation Explanation</h3>
        <p className="text-sm text-gray-300 leading-relaxed">{c.explanation}</p>
      </div>

      {/* Editorial Actions (Audit Queue check) */}
      {isModerator && c.review_status === "pending_review" && (
        <div className="bg-[#1b1714] border border-orange-900/30 rounded-xl p-6">
          <div className="flex items-center gap-2 text-orange-400 mb-3">
            <ShieldAlert className="w-5 h-5" />
            <h3 className="text-sm font-bold uppercase tracking-wider">Editorial Moderation Actions</h3>
          </div>
          <p className="text-xs text-gray-400 mb-6">
            This flagged mismatch is currently hidden from the public portal. Approve this to list it as a verified consistency mismatch on the politician timeline, or dismiss it.
          </p>
          <div className="flex gap-4">
            <button
              onClick={() => reviewMutation.mutate("verified")}
              disabled={reviewMutation.isPending}
              className="px-4 py-2 bg-orange-650 hover:bg-orange-600 text-white rounded font-semibold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <CheckCircle className="w-4 h-4" />
              Approve Inconsistency
            </button>
            <button
              onClick={() => reviewMutation.mutate("dismissed")}
              disabled={reviewMutation.isPending}
              className="px-4 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 rounded font-semibold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4 text-red-500" />
              Dismiss (Archive)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
