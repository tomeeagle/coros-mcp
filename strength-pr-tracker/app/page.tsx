"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type DayActivity = {
  kind: string;
  label: string;
};

type DayReview = {
  date: string;
  planned: string | null;
  plannedKind?: string | null;
  done: string | null;
  status: string;
  activities?: DayActivity[];
};

type Suggestion = {
  date: string;
  from: string;
  to: string;
  reason: string;
};

type Review = {
  weekStart: string;
  weekEnd: string;
  headline: string;
  notes: string[];
  days: DayReview[];
  nextWeekSuggestions: Suggestion[];
  refreshWarning?: string;
  stats: {
    plannedRunKm?: number;
    doneRunKm?: number;
    bikeKm?: number;
    bikeMinutes?: number;
    weekLoad?: number;
    loadRatio?: number | null;
    avgRunHr?: number | null;
    avgRhr?: number | null;
    activityCount?: number;
  };
};

function shiftWeek(isoMonday: string, deltaWeeks: number): string {
  const d = new Date(isoMonday + "T12:00:00");
  d.setDate(d.getDate() + deltaWeeks * 7);
  return d.toISOString().slice(0, 10);
}

function formatWeekRange(start: string, end: string): string {
  const a = new Date(start + "T12:00:00");
  const b = new Date(end + "T12:00:00");
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  return `${a.toLocaleDateString("en-GB", opts)} – ${b.toLocaleDateString("en-GB", opts)}`;
}

function dayName(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return `${d.toLocaleDateString("en-GB", { weekday: "short" })} ${d.getDate()}`;
}

function Icon({
  kind,
  className = "h-5 w-5",
}: {
  kind: string | null | undefined;
  className?: string;
}) {
  const common = {
    className,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true as const,
  };

  switch (kind) {
    case "run":
      return (
        <svg {...common}>
          <circle cx="12" cy="5" r="2" />
          <path d="M8 21l2-6 2 2 3-5" />
          <path d="M14 12l-2-4-3 1-2 5" />
        </svg>
      );
    case "bike":
      return (
        <svg {...common}>
          <circle cx="6.5" cy="16.5" r="3.5" />
          <circle cx="17.5" cy="16.5" r="3.5" />
          <path d="M6.5 16.5L10 8h4l3.5 8.5" />
          <path d="M10 8l2 4h4" />
        </svg>
      );
    case "strength":
      return (
        <svg {...common}>
          <path d="M6 8v8M18 8v8M3 10v4M21 10v4M6 12h12" />
        </svg>
      );
    case "rest":
      return (
        <svg {...common}>
          <path d="M18 14.5A6.5 6.5 0 119.5 6 5.2 5.2 0 0018 14.5z" />
        </svg>
      );
    case "heart":
      return (
        <svg {...common}>
          <path d="M12 20s-7-4.5-7-10a4 4 0 017-2.5A4 4 0 0119 10c0 5.5-7 10-7 10z" />
        </svg>
      );
    case "load":
      return (
        <svg {...common}>
          <path d="M4 19V9M10 19V5M16 19v-7M22 19V8" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
  }
}

function doneFallback(day: DayReview): string {
  if (day.status === "upcoming") return "Upcoming";
  if (day.status === "pending") return "Later today";
  return "—";
}

function fmtKm(n: number | undefined | null): string {
  if (n == null) return "0";
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

export default function WeeklyCoachPage() {
  const [week, setWeek] = useState<string | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);
  const [applyMsg, setApplyMsg] = useState<string | null>(null);

  const load = useCallback(async (weekParam?: string, refresh = false) => {
    setLoading(true);
    setError(null);
    setApplyMsg(null);
    try {
      const q = new URLSearchParams();
      if (weekParam) q.set("week", weekParam.replace(/-/g, ""));
      if (refresh) q.set("refresh", "1");
      const res = await fetch(`/api/coach/review?${q}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load review");
      setReview(data);
      setWeek(data.weekStart);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(undefined, true);
  }, [load]);

  const accent = useMemo(() => {
    if (!review) return "var(--ink)";
    const h = review.headline.toLowerCase();
    if (h.includes("hard")) return "var(--ease)";
    if (h.includes("on track") || h.includes("nice")) return "var(--ok)";
    return "var(--ink)";
  }, [review]);

  const statItems = useMemo(() => {
    if (!review?.stats) return [];
    const s = review.stats;
    const items: { key: string; icon: string; value: string; label: string }[] = [
      {
        key: "load",
        icon: "load",
        value: String(s.weekLoad ?? 0),
        label: s.loadRatio != null ? `Load · ${s.loadRatio}×` : "Training load",
      },
      {
        key: "run",
        icon: "run",
        value: `${fmtKm(s.doneRunKm)}`,
        label: `km run · ${fmtKm(s.plannedRunKm)} planned`,
      },
      {
        key: "bike",
        icon: "bike",
        value: `${fmtKm(s.bikeKm)}`,
        label: s.bikeMinutes ? `km bike · ${s.bikeMinutes} min` : "km bike",
      },
    ];
    if (s.avgRunHr != null) {
      items.push({
        key: "hr",
        icon: "heart",
        value: String(s.avgRunHr),
        label: "avg run HR",
      });
    }
    if (s.avgRhr != null) {
      items.push({
        key: "rhr",
        icon: "heart",
        value: String(s.avgRhr),
        label: "avg resting HR",
      });
    }
    return items;
  }, [review]);

  async function applyTweaks() {
    if (!review?.nextWeekSuggestions?.length) return;
    setApplying(true);
    setApplyMsg(null);
    try {
      const res = await fetch("/api/coach/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suggestions: review.nextWeekSuggestions }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Apply failed");
      setApplyMsg(
        `Updated plan (${data.changed} change${data.changed === 1 ? "" : "s"}). ${(data.logs || []).join(" · ")}`
      );
      await load(week || undefined, true);
    } catch (e) {
      setApplyMsg(e instanceof Error ? e.message : "Apply failed");
    } finally {
      setApplying(false);
    }
  }

  return (
    <main className="min-h-screen px-6 py-16 sm:px-10 sm:py-24">
      <div className="mx-auto w-full max-w-[44rem]">
        <div className="fade-up mb-16 flex items-end justify-between gap-6">
          <div>
            <p className="mb-3 text-[0.8rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
              Weekly coach
            </p>
            {week && review && (
              <p className="text-[1.05rem] font-medium text-[var(--muted)]">
                {formatWeekRange(review.weekStart, review.weekEnd)}
              </p>
            )}
          </div>
          <div className="flex items-center gap-4 text-[0.95rem] font-semibold">
            <button
              type="button"
              className="text-[var(--muted)] transition hover:text-[var(--ink)]"
              onClick={() => week && load(shiftWeek(week, -1))}
              disabled={loading || !week}
            >
              Prev
            </button>
            <button
              type="button"
              className="text-[var(--muted)] transition hover:text-[var(--ink)]"
              onClick={() => load(undefined, true)}
              disabled={loading}
            >
              Today
            </button>
            <button
              type="button"
              className="text-[var(--muted)] transition hover:text-[var(--ink)]"
              onClick={() => week && load(shiftWeek(week, 1))}
              disabled={loading || !week}
            >
              Next
            </button>
          </div>
        </div>

        {loading && !review && (
          <p className="text-[1.2rem] font-medium text-[var(--muted)]">Checking your week…</p>
        )}

        {error && (
          <div className="fade-up space-y-4">
            <h1 className="text-[clamp(2.4rem,6vw,3.6rem)] font-extrabold leading-[1.08] tracking-[-0.03em]">
              Can&apos;t reach the coach API.
            </h1>
            <p className="max-w-xl text-[1.1rem] leading-relaxed text-[var(--muted)]">{error}</p>
            <p className="text-[1rem] text-[var(--muted)]">
              In the repo root run{" "}
              <code className="rounded bg-white px-2 py-1 text-[0.95rem]">coros-mcp weekly-api</code>
            </p>
          </div>
        )}

        {review && (
          <>
            <h1
              className="fade-up mb-10 max-w-[18ch] text-[clamp(2.6rem,7vw,4rem)] font-extrabold leading-[1.05] tracking-[-0.035em]"
              style={{ color: accent }}
            >
              {review.headline}
            </h1>

            {review.refreshWarning && (
              <p className="fade-up mb-8 max-w-xl text-[0.95rem] leading-relaxed text-[var(--muted)]">
                {review.refreshWarning}
              </p>
            )}

            {statItems.length > 0 && (
              <div className="fade-up mb-14 grid grid-cols-2 gap-x-6 gap-y-8 border-y border-[var(--line)] py-8 sm:grid-cols-3">
                {statItems.map((item) => (
                  <div key={item.key} className="min-w-0">
                    <div className="mb-3 text-[var(--muted)]">
                      <Icon kind={item.icon} className="h-5 w-5" />
                    </div>
                    <p className="text-[2rem] font-extrabold leading-none tracking-[-0.03em] sm:text-[2.25rem]">
                      {item.value}
                    </p>
                    <p className="mt-2 text-[0.85rem] font-medium leading-snug text-[var(--muted)]">
                      {item.label}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <ul className="fade-up-delay mb-20 space-y-4">
              {review.notes.map((note) => (
                <li
                  key={note}
                  className="max-w-xl text-[1.15rem] font-medium leading-snug text-[var(--ink)]"
                >
                  {note}
                </li>
              ))}
            </ul>

            <section className="fade-up-delay-2 mb-20">
              <h2 className="mb-8 text-[0.8rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                This week
              </h2>
              <div className="divide-y divide-[var(--line)] border-y border-[var(--line)]">
                {review.days.map((day) => (
                  <div
                    key={day.date}
                    className="grid grid-cols-[5.5rem_1fr] gap-4 py-5 sm:grid-cols-[6rem_1fr_1fr]"
                  >
                    <div className="pt-0.5 text-[0.95rem] font-bold">{dayName(day.date)}</div>
                    <div>
                      <p className="text-[0.75rem] font-medium uppercase tracking-wide text-[var(--muted)]">
                        Planned
                      </p>
                      <div className="mt-1 flex items-start gap-2">
                        <span className="mt-0.5 shrink-0 text-[var(--muted)]">
                          <Icon
                            kind={day.plannedKind || (day.planned ? "other" : "rest")}
                            className="h-[1.1rem] w-[1.1rem]"
                          />
                        </span>
                        <p className="text-[1.02rem] font-medium leading-snug">
                          {day.planned || "Rest"}
                        </p>
                      </div>
                    </div>
                    <div className="col-span-2 sm:col-span-1">
                      <p className="text-[0.75rem] font-medium uppercase tracking-wide text-[var(--muted)]">
                        Done
                      </p>
                      {day.activities && day.activities.length > 0 ? (
                        <ul className="mt-1 space-y-2">
                          {day.activities.map((act) => (
                            <li key={`${day.date}-${act.label}`} className="flex items-start gap-2">
                              <span className="mt-0.5 shrink-0 text-[var(--muted)]">
                                <Icon kind={act.kind} className="h-[1.1rem] w-[1.1rem]" />
                              </span>
                              <p className="text-[1.02rem] font-medium leading-snug text-[var(--muted)]">
                                {act.label}
                              </p>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-1 text-[1.02rem] font-medium leading-snug text-[var(--muted)]">
                          {doneFallback(day)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="fade-up-delay-2 mb-12">
              <h2 className="mb-8 text-[0.8rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                Next week
              </h2>
              {review.nextWeekSuggestions.length === 0 ? (
                <p className="text-[1.15rem] font-medium text-[var(--muted)]">
                  No plan tweaks suggested — keep the schedule as written.
                </p>
              ) : (
                <ul className="mb-10 space-y-8">
                  {review.nextWeekSuggestions.map((s) => (
                    <li key={`${s.date}-${s.from}`}>
                      <p className="text-[1.35rem] font-bold leading-snug tracking-[-0.02em]">
                        {s.from} → {s.to}
                      </p>
                      <p className="mt-2 max-w-lg text-[1.05rem] text-[var(--muted)]">{s.reason}</p>
                    </li>
                  ))}
                </ul>
              )}

              {review.nextWeekSuggestions.length > 0 && (
                <button
                  type="button"
                  onClick={applyTweaks}
                  disabled={applying}
                  className="rounded-md bg-[var(--ink)] px-7 py-3.5 text-[1rem] font-bold text-white transition hover:opacity-90 disabled:opacity-50"
                >
                  {applying ? "Applying…" : "Apply tweaks to plan"}
                </button>
              )}
              {applyMsg && (
                <p className="mt-5 max-w-xl text-[0.95rem] leading-relaxed text-[var(--muted)]">
                  {applyMsg}
                </p>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
