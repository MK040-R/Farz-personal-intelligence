"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  getAvailableRecordings,
  getAllImportStatus,
  startImport,
  type ImportJob,
  type ImportJobStatus,
  type RecordingItem,
} from "@/lib/api";

function formatBytes(value: number | null): string {
  if (value === null) {
    return "Unknown size";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return date.toLocaleString();
}

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_CONSECUTIVE_POLL_ERRORS = 5;

export default function OnboardingPage() {
  const [recordings, setRecordings] = useState<RecordingItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [jobStatuses, setJobStatuses] = useState<Record<string, ImportJobStatus>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadRecordings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await getAvailableRecordings();
      setRecordings(items);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load recordings");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRecordings();
  }, [loadRecordings]);

  useEffect(() => {
    if (jobs.length === 0) {
      return;
    }

    let isCancelled = false;
    const pollStartedAt = Date.now();
    let consecutivePollErrors = 0;

    const poll = async () => {
      if (Date.now() - pollStartedAt > POLL_TIMEOUT_MS) {
        if (!isCancelled) {
          setError("Import status polling timed out after 10 minutes. Refresh to check current state.");
        }
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        return;
      }

      try {
        const aggregate = await getAllImportStatus(jobs.map((job) => job.job_id));
        consecutivePollErrors = 0;

        if (isCancelled) {
          return;
        }

        const nextStatuses: Record<string, ImportJobStatus> = {};
        aggregate.jobs.forEach((status) => {
          nextStatuses[status.job_id] = status;
        });

        setJobStatuses(nextStatuses);

        const allTerminal = aggregate.jobs.every(
          (status) => status.status === "success" || status.status === "failure",
        );

        if (allTerminal && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          void loadRecordings();
        }
      } catch (pollError) {
        consecutivePollErrors += 1;
        if (!isCancelled) {
          setError(pollError instanceof Error ? pollError.message : "Failed to poll import status");
        }
        if (consecutivePollErrors >= MAX_CONSECUTIVE_POLL_ERRORS && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    };

    void poll();

    intervalRef.current = setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      isCancelled = true;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobs, loadRecordings]);

  const summary = useMemo(() => {
    const total = jobs.length;
    if (total === 0) {
      return null;
    }

    let pending = 0;
    let progress = 0;
    let success = 0;
    let failure = 0;

    jobs.forEach((job) => {
      const state = jobStatuses[job.job_id]?.status ?? "pending";
      if (state === "pending") {
        pending += 1;
      } else if (state === "progress" || state === "processing") {
        progress += 1;
      } else if (state === "success") {
        success += 1;
      } else if (state === "failure") {
        failure += 1;
      }
    });

    return {
      total,
      pending,
      progress,
      success,
      failure,
    };
  }, [jobs, jobStatuses]);

  const selectableCount = recordings.filter((item) => !item.already_imported).length;

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <h1 className="text-2xl font-semibold">Onboarding</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          Live backend integration: list Google Drive recordings, select files, queue imports, and
          poll status every 3 seconds until completion.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
          <button
            type="button"
            onClick={() => {
              void loadRecordings();
            }}
            className="rounded border border-standard px-3 py-1.5 text-ink-secondary hover:border-emphasis hover:text-ink-primary"
          >
            Refresh recordings
          </button>
          {lastUpdated && <span className="text-ink-tertiary">Last updated: {lastUpdated}</span>}
        </div>
      </section>

      {error && (
        <section className="card border border-emphasis bg-accent-subtle p-4 text-sm text-accent">
          {error}
        </section>
      )}

      {summary && (
        <section className="card p-4">
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <span className="font-semibold text-ink-primary">Import progress</span>
            <span className="mono text-ink-secondary">Total {summary.total}</span>
            <span className="mono text-ink-secondary">Pending {summary.pending}</span>
            <span className="mono text-ink-secondary">Running {summary.progress}</span>
            <span className="mono text-ink-secondary">Success {summary.success}</span>
            <span className="mono text-ink-secondary">Failed {summary.failure}</span>
          </div>
        </section>
      )}

      <section className="card p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Available recordings</h2>
          <div className="text-sm text-ink-tertiary">
            {isLoading ? "Loading..." : `${recordings.length} found (${selectableCount} selectable)`}
          </div>
        </div>

        <div className="mb-4">
          <button
            type="button"
            disabled={selectedIds.size === 0 || isSubmitting}
            onClick={async () => {
              if (selectedIds.size === 0) {
                return;
              }
              setIsSubmitting(true);
              setError(null);
              try {
                const response = await startImport(Array.from(selectedIds));
                setJobs(response.jobs);
                const initialStates: Record<string, ImportJobStatus> = {};
                response.jobs.forEach((job) => {
                  initialStates[job.job_id] = {
                    job_id: job.job_id,
                    status: "pending",
                  };
                });
                setJobStatuses(initialStates);
                setSelectedIds(new Set());
              } catch (submitError) {
                setError(submitError instanceof Error ? submitError.message : "Failed to queue import");
              } finally {
                setIsSubmitting(false);
              }
            }}
            className="rounded border border-emphasis bg-accent-subtle px-4 py-2 text-sm font-medium text-accent disabled:cursor-not-allowed disabled:border-soft disabled:text-ink-muted"
          >
            {isSubmitting ? "Queueing..." : `Import selected (${selectedIds.size})`}
          </button>
        </div>

        {recordings.length === 0 && !isLoading && (
          <p className="text-sm text-ink-tertiary">No recordings were returned for the current lookback window.</p>
        )}

        <div className="space-y-3">
          {recordings.map((recording) => {
            const job = jobs.find((candidate) => candidate.file_id === recording.file_id);
            const status = job ? jobStatuses[job.job_id]?.status : null;

            return (
              <label
                key={recording.file_id}
                className={`block rounded-md border px-4 py-3 ${
                  recording.already_imported
                    ? "border-soft bg-bg-control"
                    : "border-standard bg-bg-surface-raised hover:border-emphasis"
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1"
                    disabled={recording.already_imported}
                    checked={selectedIds.has(recording.file_id)}
                    onChange={(event) => {
                      setSelectedIds((current) => {
                        const next = new Set(current);
                        if (event.target.checked) {
                          next.add(recording.file_id);
                        } else {
                          next.delete(recording.file_id);
                        }
                        return next;
                      });
                    }}
                  />

                  <div className="flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-ink-primary">{recording.name}</p>
                      <span className="mono text-xs text-ink-tertiary">{formatBytes(recording.size_bytes)}</span>
                    </div>
                    <p className="mt-1 text-sm text-ink-tertiary">Created {formatDate(recording.created_time)}</p>
                    <p className="mt-1 text-xs text-ink-muted">{recording.mime_type}</p>

                    {recording.already_imported && (
                      <p className="mt-2 inline-flex rounded border border-soft px-2 py-1 text-xs text-ink-secondary">
                        Already imported
                      </p>
                    )}

                    {!recording.already_imported && status && (
                      <p className="mt-2 inline-flex rounded border border-soft px-2 py-1 text-xs text-ink-secondary">
                        Job status: {status}
                      </p>
                    )}
                  </div>
                </div>
              </label>
            );
          })}
        </div>
      </section>
    </div>
  );
}
