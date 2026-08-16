"use client";

import type { CSSProperties, ReactNode } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type WeekTrend = {
  weekStart: string;
  weekEnd: string;
  label: string;
  runKm: number;
  bikeKm: number;
  strengthCount: number;
  load: number;
  loadRatio: number | null;
  avgRhr: number | null;
  avgHrv: number | null;
  sleepNights: number;
  avgSleepHours: number | null;
  avgAwakeHours: number | null;
  avgNapHours: number | null;
  vo2max: number | null;
  gap: boolean;
};

export type DailyPoint = {
  date: string;
  label: string;
  load: number;
  rhr: number | null;
  hrv: number | null;
  sleepHours: number | null;
  awakeHours: number | null;
};

export type FatigueFactor = {
  title: string;
  detail: string;
  weight: "high" | "medium" | "low" | string;
};

export type Trends = {
  weekStart: string;
  weekEnd: string;
  weeks: WeekTrend[];
  daily: DailyPoint[];
  fatigue: {
    headline: string;
    summary: string;
    factors: FatigueFactor[];
  };
  refreshWarning?: string;
};

const RUN = "#2E5BFF";
const BIKE = "#169B62";
const LOAD = "#2B2244";
const RHR = "#E0524D";
const HRV = "#2E5BFF";
const SLEEP = "#2B2244";
const AWAKE = "#D9532B";

function ChartFrame({
  title,
  caption,
  children,
}: {
  title: string;
  caption: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl bg-white px-5 py-5 sm:px-6 sm:py-6">
      <p className="mb-1 text-[1rem] font-bold tracking-[-0.02em]">{title}</p>
      <p className="mb-5 text-[0.95rem] font-medium text-[var(--muted)]">{caption}</p>
      <div className="h-56 w-full">{children}</div>
    </div>
  );
}

function tooltipStyle(): CSSProperties {
  return {
    border: "1px solid #e8e8e8",
    borderRadius: 12,
    fontSize: 13,
    fontWeight: 600,
  };
}

const WEIGHT_STYLE: Record<string, { bg: string; fg: string; label: string }> = {
  high: { bg: "#FBE3DB", fg: "#C24216", label: "Main" },
  medium: { bg: "#FDF1DC", fg: "#9A6A12", label: "Also" },
  low: { bg: "#DCF0E3", fg: "#12703F", label: "Note" },
};

export default function TrendsPanel({ trends }: { trends: Trends }) {
  const weeks = trends.weeks.map((w) => ({
    ...w,
    avgRhr: w.avgRhr ?? undefined,
    avgHrv: w.avgHrv ?? undefined,
    avgSleepHours: w.avgSleepHours ?? undefined,
    avgAwakeHours: w.avgAwakeHours ?? undefined,
  }));
  const daily = trends.daily;
  const fat = trends.fatigue;

  return (
    <section className="fade-up-delay mb-20">
      <h2 className="mb-8 text-[1rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
        Why this week feels heavy
      </h2>

      <div className="mb-8 rounded-2xl bg-[#2B2244] px-8 py-8 text-white">
        <p className="max-w-[28ch] text-[clamp(1.6rem,4vw,2.2rem)] font-extrabold leading-[1.12] tracking-[-0.03em]">
          {fat.headline}
        </p>
        <p className="mt-3 max-w-xl text-[1.05rem] font-medium leading-relaxed opacity-85">
          {fat.summary}
        </p>
      </div>

      {fat.factors.length > 0 && (
        <ul className="mb-12 space-y-3">
          {fat.factors.map((f) => {
            const pill = WEIGHT_STYLE[f.weight] || WEIGHT_STYLE.medium;
            return (
              <li key={f.title} className="rounded-2xl bg-white px-6 py-5">
                <div className="mb-2 flex items-center gap-3">
                  <span
                    className="rounded-full px-2.5 py-0.5 text-[0.85rem] font-bold"
                    style={{ backgroundColor: pill.bg, color: pill.fg }}
                  >
                    {pill.label}
                  </span>
                  <p className="text-[1.08rem] font-bold leading-snug">{f.title}</p>
                </div>
                <p className="max-w-2xl text-[1rem] font-medium leading-relaxed text-[var(--muted)]">
                  {f.detail}
                </p>
              </li>
            );
          })}
        </ul>
      )}

      <h2 className="mb-8 text-[1rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
        Trends
      </h2>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartFrame
          title="Weekly distance"
          caption="Run and bike kilometres · last 12 weeks"
        >
          <ResponsiveContainer>
            <ComposedChart data={weeks} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#e8e8e8" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#666", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fill: "#666", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                unit=" km"
                width={48}
              />
              <Tooltip contentStyle={tooltipStyle()} />
              <Legend />
              <Bar dataKey="runKm" name="Run" stackId="d" fill={RUN} radius={[0, 0, 0, 0]} />
              <Bar dataKey="bikeKm" name="Bike" stackId="d" fill={BIKE} radius={[4, 4, 0, 0]} />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartFrame>

        <ChartFrame
          title="Weekly training load"
          caption="Coros daily load summed Mon–Sun"
        >
          <ResponsiveContainer>
            <ComposedChart data={weeks} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#e8e8e8" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#666", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#666", fontSize: 11 }} axisLine={false} tickLine={false} width={36} />
              <Tooltip contentStyle={tooltipStyle()} />
              <Bar dataKey="load" name="Load" fill={LOAD} radius={[4, 4, 0, 0]} />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartFrame>

        <ChartFrame
          title="Sleep"
          caption="Average hours per night (naps not included in the line)"
        >
          <ResponsiveContainer>
            <ComposedChart data={weeks} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#e8e8e8" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#666", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fill: "#666", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                unit=" h"
                width={40}
                domain={[0, 10]}
              />
              <Tooltip contentStyle={tooltipStyle()} />
              <Legend />
              <Line
                type="monotone"
                dataKey="avgSleepHours"
                name="Sleep"
                stroke={SLEEP}
                strokeWidth={2.5}
                dot={{ r: 3 }}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="avgAwakeHours"
                name="Awake"
                stroke={AWAKE}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartFrame>

        <ChartFrame
          title="Resting HR and sleep HRV"
          caption="Weekly averages · RHR down is better, HRV up is better"
        >
          <ResponsiveContainer>
            <ComposedChart data={weeks} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#e8e8e8" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#666", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                yAxisId="rhr"
                tick={{ fill: "#666", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={36}
                domain={["dataMin - 4", "dataMax + 4"]}
              />
              <YAxis
                yAxisId="hrv"
                orientation="right"
                tick={{ fill: "#666", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={36}
              />
              <Tooltip contentStyle={tooltipStyle()} />
              <Legend />
              <Line
                yAxisId="rhr"
                type="monotone"
                dataKey="avgRhr"
                name="RHR"
                stroke={RHR}
                strokeWidth={2.5}
                dot={{ r: 3 }}
                connectNulls={false}
              />
              <Line
                yAxisId="hrv"
                type="monotone"
                dataKey="avgHrv"
                name="HRV"
                stroke={HRV}
                strokeWidth={2.5}
                dot={{ r: 3 }}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartFrame>
      </div>

      <div className="mt-4">
        <ChartFrame
          title="This week, day by day"
          caption="Training load vs resting HR · the Friday–Saturday pile-up"
        >
          <ResponsiveContainer>
            <ComposedChart data={daily} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#e8e8e8" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#666", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                yAxisId="load"
                tick={{ fill: "#666", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={36}
              />
              <YAxis
                yAxisId="rhr"
                orientation="right"
                tick={{ fill: "#666", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={36}
                domain={["dataMin - 6", "dataMax + 6"]}
              />
              <Tooltip contentStyle={tooltipStyle()} />
              <Legend />
              <Bar yAxisId="load" dataKey="load" name="Load" fill={LOAD} radius={[4, 4, 0, 0]} />
              <Line
                yAxisId="rhr"
                type="monotone"
                dataKey="rhr"
                name="RHR"
                stroke={RHR}
                strokeWidth={2.5}
                dot={{ r: 4 }}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartFrame>
      </div>

      <p className="mt-4 text-[0.9rem] font-medium text-[var(--muted)]">
        Source: Coros cache · {trends.weeks[0]?.label} → {trends.weeks.at(-1)?.label}
        {trends.refreshWarning ? ` · ${trends.refreshWarning}` : ""}
      </p>
    </section>
  );
}
