"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { LogOut, LayoutDashboard, ShieldAlert, User as UserIcon } from "lucide-react";

export default function ClientNav() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="flex items-center gap-4">
      {isAuthenticated ? (
        <>
          {user?.role === "admin" && (
            <Link
              href="/admin"
              className="text-xs font-semibold bg-orange-950/50 hover:bg-orange-950 text-orange-400 border border-orange-850 px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-all"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              Moderation Queue
            </Link>
          )}
          <div className="flex items-center gap-2 text-sm text-gray-300">
            <UserIcon className="w-4 h-4 text-gray-500" />
            <span className="hidden sm:inline font-medium">{user?.email}</span>
            <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded uppercase font-semibold">
              {user?.role}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="text-xs font-medium text-gray-400 hover:text-white border border-gray-800 hover:border-gray-700 px-3 py-1.5 rounded-md flex items-center gap-1 transition-all cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </>
      ) : (
        <Link
          href="/login"
          className="text-xs font-medium bg-white hover:bg-gray-150 text-black px-4 py-1.5 rounded-md font-semibold transition-all"
        >
          Sign In
        </Link>
      )}
    </div>
  );
}
