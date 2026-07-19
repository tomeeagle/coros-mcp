import { NextRequest, NextResponse } from "next/server";

const BRIDGE = process.env.COROS_BRIDGE_URL || "http://127.0.0.1:5055";

export async function GET(req: NextRequest) {
  const week = req.nextUrl.searchParams.get("week");
  const refresh = req.nextUrl.searchParams.get("refresh");
  const q = new URLSearchParams();
  if (week) q.set("week", week);
  if (refresh) q.set("refresh", refresh);
  try {
    const res = await fetch(`${BRIDGE}/review?${q}`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      {
        error:
          "Weekly API is not running. Start it with: coros-mcp weekly-api",
      },
      { status: 503 }
    );
  }
}
