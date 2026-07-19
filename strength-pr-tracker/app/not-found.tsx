import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="text-center">
        <h1 className="text-[clamp(2.5rem,7vw,4rem)] font-extrabold tracking-[-0.03em]">
          Nothing here.
        </h1>
        <p className="mt-4 text-[1.1rem] text-[var(--muted)]">
          <Link href="/" className="font-bold text-[var(--ink)] underline">
            Back to your week
          </Link>
        </p>
      </div>
    </main>
  );
}
