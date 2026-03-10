"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  getCommitments,
  getIndexStats,
  getTodayBriefing,
  type Commitment,
  type IndexStats,
  type TodayBriefing,
} from "@/lib/api";

export default function DashboardPage() {
  const [briefing, setBriefing] = useState<TodayBriefing | null>(null);
  const [stats, setStats] = useState<IndexStats | null>(null);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [todayData, statsData, commitmentData] = await Promise.all([
          getTodayBriefing(),
          getIndexStats(),
          getCommitments("open"),
        ]);
        if (mounted) {
          setBriefing(todayData);
          setStats(statsData);
          setCommitments(commitmentData);
        }
      } catch (loadError) {
        if (mounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard");
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

  if (loading) {
    return <section className="card p-4 text-sm text-ink-secondary">Loading dashboard...</section>;
  }

  if (error || !briefing || !stats) {
    return (
      <section className="card border border-emphasis bg-accent-subtle p-4 text-sm text-accent">
        {error ?? "Dashboard unavailable"}
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          Live dashboard view using `GET /calendar/today`, `GET /index/stats`, and
          `GET /commitments`.
        </p>
      </section>

      <section className="grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-4">
        <div className="card p-4">
          <p className="text-ink-tertiary">Conversations</p>
          <p className="mono mt-1 text-xl text-ink-primary">{stats.conversation_count}</p>
        </div>
        <div className="card p-4">
          <p className="text-ink-tertiary">Topics</p>
          <p className="mono mt-1 text-xl text-ink-primary">{stats.topic_count}</p>
        </div>
        <div className="card p-4">
          <p className="text-ink-tertiary">Commitments</p>
          <p className="mono mt-1 text-xl text-ink-primary">{stats.commitment_count}</p>
        </div>
        <div className="card p-4">
          <p className="text-ink-tertiary">Entities</p>
          <p className="mono mt-1 text-xl text-ink-primary">{stats.entity_count}</p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="card p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold">Upcoming today</h2>
            <Link href="/today" className="text-xs text-accent hover:text-accent-hover">
              Open full view
            </Link>
          </div>
          <div className="mt-3 space-y-2">
            {briefing.upcoming_meetings.map((meeting) => (
              <div key={meeting.id} className="rounded border border-soft px-3 py-2">
                <p className="font-medium text-ink-primary">{meeting.title}</p>
                <p className="mt-1 text-xs text-ink-tertiary">
                  {new Date(meeting.start_time).toLocaleString()} · {meeting.attendees.join(", ")}
                </p>
              </div>
            ))}
            {briefing.upcoming_meetings.length === 0 && (
              <p className="text-sm text-ink-tertiary">No upcoming meetings from calendar yet.</p>
            )}
          </div>
        </article>

        <article className="card p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold">Open commitments</h2>
            <Link href="/commitments" className="text-xs text-accent hover:text-accent-hover">
              View all
            </Link>
          </div>

          <div className="mt-3 space-y-2">
            {commitments.slice(0, 4).map((commitment) => (
              <div key={commitment.id} className="rounded border border-soft px-3 py-2">
                <p className="text-sm text-ink-primary">{commitment.text}</p>
                <p className="mt-1 text-xs text-ink-tertiary">
                  {commitment.owner} · due {commitment.due_date ?? "not specified"} · {" "}
                  {commitment.conversation_title}
                </p>
              </div>
            ))}

            {commitments.length === 0 && (
              <p className="text-sm text-ink-tertiary">No open commitments in the current dataset.</p>
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
