import Link from "next/link";
import { Suspense } from "react";

import { GlobalSearchForm } from "@/components/app-frame/GlobalSearchForm";
import { SessionControls } from "@/components/app-frame/SessionControls";
import { SidebarNav } from "@/components/app-frame/SidebarNav";

type AppFrameProps = {
  children: React.ReactNode;
};

function SearchFormFallback() {
  return (
    <div className="flex min-w-[240px] max-w-xl flex-1 gap-2">
      <div className="h-10 flex-1 rounded border border-standard bg-bg-control" />
      <div className="h-10 w-20 rounded border border-emphasis bg-accent-subtle" />
    </div>
  );
}

export function AppFrame({ children }: AppFrameProps) {
  return (
    <div className="min-h-screen bg-bg-base text-ink-primary">
      <div className="mx-auto flex min-h-screen w-full max-w-[1400px]">
        <aside className="sidebar-shell w-[248px] px-4 py-6">
          <div className="sidebar-logo mb-8 px-4 py-3 text-sm font-bold tracking-[0.18em] text-white">
            <Link href="/">Pocket Nori</Link>
          </div>

          <SidebarNav />
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          <header className="flex flex-wrap items-center justify-between gap-3 border-b border-standard bg-bg-surface-raised px-6 py-4">
            <Suspense fallback={<SearchFormFallback />}>
              <GlobalSearchForm />
            </Suspense>
            <SessionControls />
          </header>

          <main className="flex-1 px-6 py-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
