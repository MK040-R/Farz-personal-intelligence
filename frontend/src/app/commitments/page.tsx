"use client";

import { useEffect, useState } from "react";

import { getCommitments, resolveCommitment, type Commitment } from "@/lib/api";

export default function CommitmentsPage() {
  const [openItems, setOpenItems] = useState<Commitment[]>([]);
  const [resolvedItems, setResolvedItems] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [openData, resolvedData] = await Promise.all([
          getCommitments("open"),
          getCommitments("resolved"),
        ]);
        if (mounted) {
          setOpenItems(openData);
          setResolvedItems(resolvedData);
        }
      } catch (loadError) {
        if (mounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load commitments");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <h1 className="text-2xl font-semibold">Commitments</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          Live commitments list and status updates using `GET /commitments` and
          `PATCH /commitments/{"{id}"}`.
        </p>
      </section>

      {loading && <section className="card p-4 text-sm text-ink-secondary">Loading commitments...</section>}

      {error && (
        <section className="card border border-emphasis bg-accent-subtle p-4 text-sm text-accent">
          {error}
        </section>
      )}

      {!loading && (
        <section className="grid gap-4 lg:grid-cols-2">
          <article className="card p-5">
            <h2 className="text-lg font-semibold">Open</h2>
            <div className="mt-3 space-y-2">
              {openItems.length === 0 && <p className="text-sm text-ink-tertiary">No open commitments.</p>}
              {openItems.map((item) => (
                <div key={item.id} className="rounded border border-soft p-3">
                  <p className="text-sm text-ink-primary">{item.text}</p>
                  <p className="mt-1 text-xs text-ink-tertiary">
                    {item.owner} · due {item.due_date ?? "not specified"} · {item.conversation_title}
                  </p>
                  <button
                    type="button"
                    disabled={resolvingId === item.id}
                    onClick={async () => {
                      setResolvingId(item.id);
                      setError(null);
                      try {
                        const resolved = await resolveCommitment(item.id);
                        setOpenItems((current) =>
                          current.filter((candidate) => candidate.id !== resolved.id),
                        );
                        setResolvedItems((current) => [resolved, ...current]);
                      } catch (resolveError) {
                        setError(
                          resolveError instanceof Error
                            ? resolveError.message
                            : "Failed to resolve commitment",
                        );
                      } finally {
                        setResolvingId(null);
                      }
                    }}
                    className="mt-2 rounded border border-emphasis bg-accent-subtle px-2 py-1 text-xs font-medium text-accent disabled:cursor-not-allowed disabled:border-soft disabled:text-ink-muted"
                  >
                    {resolvingId === item.id ? "Resolving..." : "Mark resolved"}
                  </button>
                </div>
              ))}
            </div>
          </article>

          <article className="card p-5">
            <h2 className="text-lg font-semibold">Resolved</h2>
            <div className="mt-3 space-y-2">
              {resolvedItems.length === 0 && <p className="text-sm text-ink-tertiary">No resolved commitments.</p>}
              {resolvedItems.map((item) => (
                <div key={item.id} className="rounded border border-soft p-3">
                  <p className="text-sm text-ink-primary">{item.text}</p>
                  <p className="mt-1 text-xs text-ink-tertiary">
                    {item.owner} · {item.conversation_title}
                  </p>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </div>
  );
}
