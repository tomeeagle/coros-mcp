"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import TrendsPanel, { type Trends } from "./TrendsPanel";

type DayActivity = {
  kind: string;
  label: string;
  hard?: boolean;
  reason?: string | null;
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
          <circle cx="13" cy="4" r="1.6" />
          <path d="M4 17l5 1 .75-1.5" />
          <path d="M15 21v-4l-4-3 1-6" />
          <path d="M7 12v-3l5-1 3 3 3 1" />
        </svg>
      );
    case "bike":
      return (
        <svg {...common}>
          <circle cx="5" cy="17.5" r="3.2" />
          <circle cx="19" cy="17.5" r="3.2" />
          <circle cx="17" cy="5" r="1.4" />
          <path d="M12 18.5v-4l-3-3 5-4 2 3h3" />
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
    case "flame":
      return (
        <svg {...common}>
          <path d="M12 3c1 3-2 4-2 7a2 2 0 004 0c0-1 1-2 1-2 1 1.5 2 3 2 5a5 5 0 01-10 0c0-4 4-6 5-10z" />
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

const KIND_CHIP: Record<string, { bg: string; fg: string }> = {
  run: { bg: "#E4EAFF", fg: "#2E5BFF" },
  bike: { bg: "#DCF0E3", fg: "#169B62" },
  strength: { bg: "#E9E5F3", fg: "#2B2244" },
  rest: { bg: "#F2F2F2", fg: "#9A9A9A" },
  other: { bg: "#F2F2F2", fg: "#666666" },
};

function KindChip({ kind, hard }: { kind: string; hard?: boolean }) {
  const c = hard ? { bg: "#FBE3DB", fg: "#D9532B" } : KIND_CHIP[kind] || KIND_CHIP.other;
  return (
    <span
      className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl"
      style={{ backgroundColor: c.bg, color: c.fg }}
    >
      <Icon kind={kind} className="h-8 w-8" />
    </span>
  );
}

const STATUS_PILL: Record<string, { text: string; bg: string; fg: string }> = {
  missed: { text: "Missed", bg: "#FBE3DB", fg: "#C24216" },
  extra: { text: "Extra", bg: "#E4EAFF", fg: "#2E5BFF" },
  matched: { text: "Done", bg: "#DCF0E3", fg: "#12703F" },
  upcoming: { text: "Upcoming", bg: "#F2F2F2", fg: "#8A8A8A" },
  pending: { text: "Later today", bg: "#FDF1DC", fg: "#9A6A12" },
};

function splitLabel(label: string): { title: string; meta: string | null } {
  const idx = label.indexOf(" · ");
  if (idx === -1) return { title: label, meta: null };
  return { title: label.slice(0, idx), meta: label.slice(idx + 3) };
}

function fmtKm(n: number | undefined | null): string {
  if (n == null) return "0";
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

export default function WeeklyCoachPage() {
  const [week, setWeek] = useState<string | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [trends, setTrends] = useState<Trends | null>(null);
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
      const [revRes, trRes] = await Promise.all([
        fetch(`/api/coach/review?${q}`),
        fetch(`/api/coach/trends?${q}`),
      ]);
      const data = await revRes.json();
      if (!revRes.ok) throw new Error(data.error || "Failed to load review");
      setReview(data);
      setWeek(data.weekStart);
      if (trRes.ok) {
        setTrends(await trRes.json());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(undefined, true);
  }, [load]);

  const hero = useMemo(() => {
    if (!review) return { bg: "#2B2244", fg: "#ffffff" };
    const h = review.headline.toLowerCase();
    if (h.includes("hard")) return { bg: "#D9532B", fg: "#ffffff" };
    if (h.includes("on track") || h.includes("nice")) return { bg: "#169B62", fg: "#ffffff" };
    if (h.includes("hasn't happened") || h.includes("lighter"))
      return { bg: "#C3E4CD", fg: "#12291A" };
    return { bg: "#2B2244", fg: "#ffffff" };
  }, [review]);

  const statItems = useMemo(() => {
    if (!review?.stats) return [];
    const s = review.stats;
    const items: {
      key: string;
      icon: string;
      value: string;
      label: string;
      bg: string;
      fg: string;
    }[] = [
      {
        key: "load",
        icon: "load",
        value: String(s.weekLoad ?? 0),
        label: s.loadRatio != null ? `training load · ${s.loadRatio}×` : "training load",
        bg: "#2B2244",
        fg: "#ffffff",
      },
      {
        key: "run",
        icon: "run",
        value: `${fmtKm(s.doneRunKm)}`,
        label: `km run · ${fmtKm(s.plannedRunKm)} planned`,
        bg: "#2E5BFF",
        fg: "#ffffff",
      },
      {
        key: "bike",
        icon: "bike",
        value: `${fmtKm(s.bikeKm)}`,
        label: s.bikeMinutes ? `km bike · ${s.bikeMinutes} min` : "km bike",
        bg: "#C3E4CD",
        fg: "#12291A",
      },
    ];
    if (s.avgRunHr != null) {
      items.push({
        key: "hr",
        icon: "heart",
        value: String(s.avgRunHr),
        label: "avg run HR",
        bg: "#E0524D",
        fg: "#ffffff",
      });
    }
    if (s.avgRhr != null) {
      items.push({
        key: "rhr",
        icon: "heart",
        value: String(s.avgRhr),
        label: "avg resting HR",
        bg: "#F3B63F",
        fg: "#2B2244",
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
    <main className="min-h-screen px-6 py-8 sm:px-10 sm:py-10">
      <div className="mx-auto w-full max-w-[64rem]">
        <div className="fade-up mb-8 flex items-end justify-between gap-6">
          <div>
            <p className="mb-1.5 text-[1rem] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
              Weekly coach
            </p>
            {week && review && (
              <p className="text-[1.05rem] font-medium text-[var(--muted)]">
                {formatWeekRange(review.weekStart, review.weekEnd)}
              </p>
            )}
          </div>
          <div className="flex items-center gap-4 text-[1rem] font-semibold">
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
              <code className="rounded bg-white px-2 py-1 text-[1rem]">coros-mcp weekly-api</code>
            </p>
          </div>
        )}

        {review && (
          <>
            <div
              className="fade-up mb-8 rounded-2xl px-8 py-8 sm:px-10 sm:py-10"
              style={{ backgroundColor: hero.bg, color: hero.fg }}
            >
              <h1 className="max-w-[16ch] text-[clamp(2.2rem,6vw,3.4rem)] font-extrabold leading-[1.05] tracking-[-0.035em]">
                {review.headline}
              </h1>
            </div>

            {review.refreshWarning && (
              <p className="fade-up mb-8 max-w-xl text-[1rem] leading-relaxed text-[var(--muted)]">
                {review.refreshWarning}
              </p>
            )}

            {statItems.length > 0 && (
              <div className="fade-up mb-14 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
                {statItems.map((item) => (
                  <div
                    key={item.key}
                    className="min-w-0 rounded-2xl px-5 py-6"
                    style={{ backgroundColor: item.bg, color: item.fg }}
                  >
                    <div className="mb-4 opacity-90">
                      <Icon kind={item.icon} className="h-10 w-10" />
                    </div>
                    <p className="text-[2rem] font-extrabold leading-none tracking-[-0.03em] sm:text-[2.25rem]">
                      {item.value}
                    </p>
                    <p className="mt-2 text-[1rem] font-semibold leading-snug opacity-80">
                      {item.label}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <ul className="fade-up-delay mb-14 space-y-4">
              {review.notes.map((note) => (
                <li
                  key={note}
                  className="max-w-xl text-[1.15rem] font-medium leading-snug text-[var(--ink)]"
                >
                  {note}
                </li>
              ))}
            </ul>

            {trends && <TrendsPanel trends={trends} />}

            <section className="fade-up-delay-2 mb-20">
              <h2 className="mb-8 text-[1rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                This week
              </h2>
              <div className="rounded-2xl bg-white px-6 py-2 sm:px-8">
                <div className="hidden grid-cols-[4.5rem_1fr_1.4fr_6.5rem] gap-4 border-b border-[var(--line)] py-4 sm:grid">
                  {["Day", "Planned", "Done", ""].map((h, i) => (
                    <p
                      key={i}
                      className="text-[1rem] font-semibold uppercase tracking-[0.12em] text-[var(--muted)]"
                    >
                      {h}
                    </p>
                  ))}
                </div>
                <div className="divide-y divide-[var(--line)]">
                  {review.days.map((day) => {
                    const pill = STATUS_PILL[day.status];
                    const [wd, num] = dayName(day.date).split(" ");
                    return (
                      <div
                        key={day.date}
                        className="grid grid-cols-[4.5rem_1fr] gap-4 py-5 sm:grid-cols-[4.5rem_1fr_1.4fr_6.5rem] sm:items-center"
                      >
                        <div>
                          <p className="text-[1rem] font-semibold uppercase tracking-wide text-[var(--muted)]">
                            {wd}
                          </p>
                          <p className="text-[1.5rem] font-extrabold leading-tight tracking-[-0.02em]">
                            {num}
                          </p>
                        </div>

                        <div className="flex items-center gap-3">
                          <KindChip kind={day.plannedKind || (day.planned ? "other" : "rest")} />
                          <p
                            className={`text-[1.02rem] font-bold leading-snug ${
                              day.planned ? "" : "text-[var(--muted)]"
                            }`}
                          >
                            {day.planned || "Rest"}
                          </p>
                        </div>

                        <div className="col-span-2 pl-[4.75rem] sm:col-span-1 sm:pl-0">
                          {day.activities && day.activities.length > 0 ? (
                            <ul className="space-y-3">
                              {day.activities.map((act) => {
                                const { title, meta } = splitLabel(act.label);
                                return (
                                  <li
                                    key={`${day.date}-${act.label}`}
                                    className="flex items-start gap-3"
                                  >
                                    <KindChip kind={act.kind} hard={act.hard} />
                                    <div className="min-w-0">
                                      <p className="flex flex-wrap items-center gap-x-2 text-[1.02rem] font-bold leading-snug">
                                        <span>{title}</span>
                                        {act.hard && (
                                          <span className="inline-flex items-center gap-1 rounded-full bg-[#D9532B] px-2 py-0.5 text-[1rem] font-bold text-white">
                                            <Icon kind="flame" className="h-4 w-4" />
                                            Too hard
                                          </span>
                                        )}
                                      </p>
                                      {meta && (
                                        <p className="text-[1rem] font-medium text-[var(--muted)]">
                                          {meta}
                                        </p>
                                      )}
                                      {act.hard && act.reason && (
                                        <p className="mt-1 text-[1rem] font-medium leading-snug text-[#D9532B]">
                                          {act.reason}
                                        </p>
                                      )}
                                    </div>
                                  </li>
                                );
                              })}
                            </ul>
                          ) : (
                            <p className="text-[1.02rem] font-medium text-[#c4c4c4]">—</p>
                          )}
                        </div>

                        <div className="col-span-2 pl-[4.75rem] sm:col-span-1 sm:justify-self-end sm:pl-0">
                          {pill && (
                            <span
                              className="inline-block rounded-full px-3 py-1 text-[1rem] font-bold"
                              style={{ backgroundColor: pill.bg, color: pill.fg }}
                            >
                              {pill.text}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            <section className="fade-up-delay-2 mb-12">
              <h2 className="mb-8 text-[1rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                Next week
              </h2>
              {review.nextWeekSuggestions.length === 0 ? (
                <div className="rounded-2xl bg-[#C3E4CD] px-8 py-8 text-[#12291A]">
                  <p className="text-[1.25rem] font-bold leading-snug tracking-[-0.02em]">
                    No plan tweaks suggested — keep the schedule as written.
                  </p>
                </div>
              ) : (
                <ul className="mb-10 space-y-4">
                  {review.nextWeekSuggestions.map((s) => (
                    <li
                      key={`${s.date}-${s.from}`}
                      className="rounded-2xl bg-[#2E5BFF] px-8 py-8 text-white"
                    >
                      <p className="text-[1.35rem] font-bold leading-snug tracking-[-0.02em]">
                        {s.from} → {s.to}
                      </p>
                      <p className="mt-2 max-w-lg text-[1.05rem] opacity-85">{s.reason}</p>
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
                <p className="mt-5 max-w-xl text-[1rem] leading-relaxed text-[var(--muted)]">
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
