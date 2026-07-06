"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useState } from "react";
import { Shield, Play, HelpCircle, Calendar, PlusCircle, CheckCircle, RefreshCw } from "lucide-react";

interface Politician {
  id: string;
  first_name: string;
  last_name: string;
}

interface SpeechJob {
  id: string;
  title: string;
  media_type: string;
  status: string;
  date_delivered: string;
}

const MOCK_POLITICIANS: Politician[] = [
  { id: "1", first_name: "John", last_name: "Doe" },
  { id: "2", first_name: "Jane", last_name: "Smith" }
];

const MOCK_JOBS: SpeechJob[] = [
  { id: "job-1", title: "Speech on Sales Taxes", media_type: "youtube", status: "completed", date_delivered: "2026-03-12" },
  { id: "job-2", title: "Infrastructure Financing Hearing", media_type: "youtube", status: "completed", date_delivered: "2023-10-18" }
];

export default function AdminDashboardPage() {
  const [title, setTitle] = useState("");
  const [politicianId, setPoliticianId] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [dateDelivered, setDateDelivered] = useState("");
  const [mediaType, setMediaType] = useState("youtube");
  const [successMsg, setSuccessMsg] = useState("");

  const { data: politicians } = useQuery<Politician[]>({
    queryKey: ["admin-politicians"],
    queryFn: () => apiFetch<Politician[]>("/politicians").catch(() => MOCK_POLITICIANS),
  });

  const { data: jobs, refetch: refetchJobs } = useQuery<SpeechJob[]>({
    queryKey: ["admin-jobs"],
    queryFn: () => apiFetch<SpeechJob[]>("/admin/speeches/queue").catch(() => MOCK_JOBS),
  });

  const ingestMutation = useMutation({
    mutationFn: (newSpeech: any) =>
      apiFetch("/speeches", {
        method: "POST",
        json: newSpeech,
      }),
    onSuccess: () => {
      setSuccessMsg("Speech successfully added to processing queue.");
      setTitle("");
      setSourceUrl("");
      setDateDelivered("");
      refetchJobs();
      setTimeout(() => setSuccessMsg(""), 5000);
    },
    onError: (err: any) => {
      alert(`Ingestion failed: ${err.message}`);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !politicianId || !dateDelivered) {
      alert("Please fill all required fields");
      return;
    }
    ingestMutation.mutate({
      title,
      politician_id: politicianId,
      source_url: sourceUrl,
      media_type: mediaType,
      date_delivered: dateDelivered,
    });
  };

  return (
    <div className="flex-1 bg-[#0f0f11] py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      <div className="mb-8 pb-4 border-b border-gray-800">
        <h2 className="text-2xl font-bold font-serif leading-7 text-white sm:text-3xl flex items-center gap-2">
          <Shield className="w-8 h-8 text-orange-500" />
          Moderation & Ingestion Dashboard
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Submit political statements and track background transcription jobs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Ingest Speech Form */}
        <div className="bg-[#141417] border border-gray-850 rounded-xl p-6 lg:col-span-1 h-fit">
          <h3 className="font-serif text-lg font-bold text-white mb-4 flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-orange-400" />
            Ingest Political Speech
          </h3>

          {successMsg && (
            <div className="p-3 mb-4 bg-emerald-950/40 border border-emerald-900/30 text-emerald-400 text-xs rounded text-center">
              {successMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Speech Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Press Briefing on Taxes"
                className="w-full px-3 py-2 rounded bg-[#0f0f11] border border-gray-800 focus:border-orange-500 outline-none text-xs text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Speaker (Politician) *</label>
              <select
                required
                value={politicianId}
                onChange={(e) => setPoliticianId(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[#0f0f11] border border-gray-800 focus:border-orange-500 outline-none text-xs text-gray-300 cursor-pointer"
              >
                <option value="">Select Speaker</option>
                {politicians?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Media Source URL</label>
              <input
                type="text"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="e.g. https://www.youtube.com/watch?v=..."
                className="w-full px-3 py-2 rounded bg-[#0f0f11] border border-gray-800 focus:border-orange-500 outline-none text-xs text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Media Type</label>
                <select
                  value={mediaType}
                  onChange={(e) => setMediaType(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-[#0f0f11] border border-gray-800 focus:border-orange-500 outline-none text-xs text-gray-300 cursor-pointer"
                >
                  <option value="youtube">YouTube</option>
                  <option value="mp4">Local MP4</option>
                  <option value="manual">Manual text</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Date Delivered *</label>
                <input
                  type="date"
                  required
                  value={dateDelivered}
                  onChange={(e) => setDateDelivered(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-[#0f0f11] border border-gray-800 focus:border-orange-500 outline-none text-xs text-white"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={ingestMutation.isPending}
              className="w-full py-2.5 bg-orange-650 hover:bg-orange-600 disabled:bg-gray-800 text-white rounded font-semibold text-xs transition-all cursor-pointer mt-4 flex items-center justify-center gap-1.5"
            >
              {ingestMutation.isPending ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Queuing Job...
                </>
              ) : (
                "Submit to Queue"
              )}
            </button>
          </form>
        </div>

        {/* Processing Job Queue */}
        <div className="bg-[#141417] border border-gray-850 rounded-xl p-6 lg:col-span-2">
          <h3 className="font-serif text-lg font-bold text-white mb-4">
            Ingestion Pipeline status
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-450 border-collapse">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 uppercase tracking-wider">
                  <th className="pb-3 font-semibold">Title</th>
                  <th className="pb-3 font-semibold">Source</th>
                  <th className="pb-3 font-semibold">Date Delivered</th>
                  <th className="pb-3 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-850">
                {jobs?.map((job) => (
                  <tr key={job.id} className="hover:bg-[#1c1c20]/30 transition-all">
                    <td className="py-3 text-white font-medium">{job.title}</td>
                    <td className="py-3 font-mono">{job.media_type}</td>
                    <td className="py-3">{job.date_delivered}</td>
                    <td className="py-3 text-right">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                          job.status === "completed"
                            ? "bg-emerald-950/40 text-emerald-400 border-emerald-900/30"
                            : job.status === "processing"
                            ? "bg-blue-950/40 text-blue-400 border-blue-900/30"
                            : "bg-orange-950/40 text-orange-400 border-orange-900/30"
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
