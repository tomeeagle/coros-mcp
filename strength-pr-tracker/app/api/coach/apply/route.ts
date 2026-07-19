import { NextRequest, NextResponse } from "next/server";

const BRIDGE = process.env.COROS_BRIDGE_URL || "http://127.0.0.1:5055";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${BRIDGE}/review/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: "Weekly API is not running. Start it with: coros-mcp weekly-api" },
      { status: 503 }
    );
  }
}
