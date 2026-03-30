const upstreamBaseUrl =
  process.env.ALPHASCOPE_API_URL ??
  process.env.NEXT_PUBLIC_SERVER_URL ??
  "http://localhost:8000";

export async function GET() {
  const headers = new Headers();
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;
  const upstreamUrl = new URL(`${upstreamBaseUrl}/api/dashboard/latest`);

  if (bypassSecret) {
    headers.set("x-vercel-protection-bypass", bypassSecret);
    upstreamUrl.searchParams.set("x-vercel-protection-bypass", bypassSecret);
  }
  try {
    const response = await fetch(upstreamUrl, {
      headers,
      cache: "no-store",
    });

    const body = await response.text();
    const contentType =
      response.headers.get("content-type") ?? "application/json";

    return new Response(body, {
      status: response.status,
      headers: {
        "content-type": contentType,
        "cache-control": "no-store",
      },
    });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "upstream fetch failed";

    return Response.json(
      { detail: `Failed to reach dashboard backend: ${detail}` },
      { status: 502 },
    );
  }
}
