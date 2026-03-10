"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getTopic, type TopicDetail } from "@/lib/api";

function formatDateTime(value: string): string {
  if (!value) {
    return "Unknown date";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export default function TopicDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [topic, setTopic] = useState<TopicDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getTopic(id);
        if (mounted) {
          setTopic(data);
        }
      } catch (loadError) {
        if (mounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load topic");
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
  }, [id]);

  if (loading) {
    return <section className="card p-4 text-sm text-ink-secondary">Loading topic...</section>;
  }

  if (error || !topic) {
    return (
      <section className="card border border-emphasis bg-accent-subtle p-4 text-sm text-accent">
        {error ?? "Topic not found"}
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="mb-2 text-xs uppercase tracking-[0.06em] text-ink-tertiary">Topic detail</p>
            <h1 className="text-2xl font-semibold text-ink-primary">{topic.label}</h1>
            <p className="mt-2 max-w-3xl text-sm text-ink-secondary">{topic.summary}</p>
          </div>
          <Link
            href="/topics"
            className="rounded border border-standard px-3 py-1.5 text-xs text-ink-secondary hover:border-emphasis hover:text-ink-primary"
          >
            All topics
          </Link>
        </div>
      </section>

      <section className="card p-5">
        <h2 className="text-lg font-semibold">Related conversations</h2>
        <div className="mt-3 space-y-2">
          {topic.conversations.length === 0 && (
            <p className="text-sm text-ink-tertiary">No conversations linked yet.</p>
          )}
          {topic.conversations.map((conversation) => (
            <Link
              key={conversation.id}
              href={`/meetings/${conversation.id}`}
              className="block rounded border border-soft p-3 transition hover:border-emphasis"
            >
              <p className="text-sm font-medium text-ink-primary">{conversation.title}</p>
              <p className="mt-1 text-xs text-ink-tertiary">
                {formatDateTime(conversation.meeting_date)}
              </p>
            </Link>
          ))}
        </div>
      </section>

      <section className="card p-5">
        <h2 className="text-lg font-semibold">Key quotes</h2>
        <div className="mt-3 space-y-2">
          {topic.key_quotes.length === 0 && (
            <p className="text-sm text-ink-tertiary">No quotes available for this topic.</p>
          )}
          {topic.key_quotes.map((quote, index) => (
            <blockquote
              key={`${topic.id}-quote-${index + 1}`}
              className="rounded border border-soft bg-bg-control px-3 py-2 text-sm text-ink-secondary"
            >
              “{quote}”
            </blockquote>
          ))}
        </div>
      </section>
    </div>
  );
}
