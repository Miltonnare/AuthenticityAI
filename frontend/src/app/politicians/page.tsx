"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useState } from "react";
import Link from "next/link";
import { User, Search, RefreshCw } from "lucide-react";

interface Politician {
  id: string;
  first_name: string;
  last_name: string;
  party: string;
  current_office: string;
  bio: string;
  image_url: string;
}

const MOCK_POLITICIANS: Politician[] = [
  { id: "1", first_name: "John", last_name: "Doe", party: "Republican", current_office: "Senator", bio: "Bio details here.", image_url: "" },
  { id: "2", first_name: "Jane", last_name: "Smith", party: "Democrat", current_office: "Governor", bio: "Bio details here.", image_url: "" }
];

export default function PoliticiansPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [partyFilter, setPartyFilter] = useState("all");

  const { data: politicians, isLoading } = useQuery<Politician[]>({
    queryKey: ["politicians", searchTerm, partyFilter],
    queryFn: () => {
      let url = "/politicians";
      const params = [];
      if (searchTerm) params.push(`q=${encodeURIComponent(searchTerm)}`);
      if (partyFilter !== "all") params.push(`party=${encodeURIComponent(partyFilter)}`);
      if (params.length > 0) url += `?${params.join("&")}`;
      return apiFetch<Politician[]>(url);
    },
    initialData: MOCK_POLITICIANS // seed initial visual data for fallback presentation
  });

  return (
    <div className="flex-1 bg-[#0f0f11] py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      <div className="mb-8 pb-4 border-b border-gray-800">
        <h2 className="text-2xl font-bold font-serif leading-7 text-white sm:text-3xl">
          Politician Directory
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Search tracked public officials and browse their statement history.
          Select an official to view their statement evolution timeline.
        </p>
      </div>

      {/* Filters bar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded bg-[#141417] border border-gray-800 focus:border-orange-500 outline-none text-sm text-white"
          />
        </div>
        <select
          value={partyFilter}
          onChange={(e) => setPartyFilter(e.target.value)}
          className="bg-[#141417] border border-gray-800 text-gray-300 rounded px-4 py-2 text-sm outline-none cursor-pointer focus:border-orange-500"
        >
          <option value="all">All Parties</option>
          <option value="Democrat">Democrat</option>
          <option value="Republican">Republican</option>
          <option value="Independent">Independent</option>
        </select>
      </div>

      {/* Grid of politicians */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 text-gray-500 animate-spin" />
        </div>
      ) : politicians && politicians.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {politicians.map((p) => (
            <div
              key={p.id}
              className="bg-[#141417] border border-gray-850 rounded-xl overflow-hidden hover:border-gray-700 transition-all flex flex-col justify-between"
            >
              <div className="p-6">
                <div className="w-12 h-12 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400 mb-4 font-serif text-lg font-bold">
                  {p.first_name[0]}{p.last_name[0]}
                </div>
                <h3 className="font-serif text-lg font-bold text-white mb-1">
                  {p.first_name} {p.last_name}
                </h3>
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
                <p className="text-xs text-gray-400 mt-4 leading-relaxed line-clamp-3">
                  {p.bio || "No biography details added yet."}
                </p>
              </div>
              <div className="border-t border-gray-850 bg-[#0c0c0e]/30 px-6 py-4">
                <Link
                  href={`/politicians/${p.id}`}
                  className="w-full text-center block text-xs font-semibold bg-gray-900 hover:bg-gray-800 border border-gray-800 py-2 rounded-md transition-all text-white"
                >
                  Examine Timeline
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">No politicians match the selected search criteria.</div>
      )}
    </div>
  );
}
