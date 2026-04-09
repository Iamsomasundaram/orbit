import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    service: "orbit-web",
    status: "ok",
    runtime: "nextjs",
    milestone: "1",
  });
}
