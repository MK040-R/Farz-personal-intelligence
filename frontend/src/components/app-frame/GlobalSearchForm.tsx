"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export function GlobalSearchForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");

  useEffect(() => {
    setQuery(searchParams.get("q") ?? "");
  }, [searchParams]);

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        const trimmed = query.trim();
        const params = new URLSearchParams();
        if (trimmed) {
          params.set("q", trimmed);
        }
        router.push(`/search${params.toString() ? `?${params.toString()}` : ""}`);
      }}
      className="flex min-w-[240px] max-w-xl flex-1 gap-2"
    >
      <input
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
        }}
        placeholder="Search all meetings"
        className="w-full rounded border border-standard bg-bg-control px-3 py-2 text-sm text-ink-primary outline-none focus:border-emphasis"
        aria-label="Global search"
      />
      <button
        type="submit"
        className="rounded border border-emphasis bg-accent-subtle px-3 py-2 text-sm font-medium text-accent"
      >
        Search
      </button>
    </form>
  );
}
