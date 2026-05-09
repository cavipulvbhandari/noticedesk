import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-start justify-center gap-6 px-6 py-12">
      <h1 className="text-4xl font-semibold tracking-tight text-navy">
        NoticeDesk
      </h1>
      <p className="text-slate-600 max-w-prose">
        Litigation-first tax operating system for Indian CA firms — GST and
        Income Tax. This is the Sprint 1 scaffold; the working product begins
        in Sprint 2.
      </p>
      <div className="flex items-center gap-3">
        <Link
          href="/login"
          className="inline-flex items-center rounded-md bg-navy px-4 py-2 text-sm font-medium text-white hover:bg-navy-500"
        >
          Sign in
        </Link>
        <Link
          href="/inbox"
          className="inline-flex items-center rounded-md bg-slate-100 px-4 py-2 text-sm font-medium text-navy hover:bg-slate-200"
        >
          Open inbox
        </Link>
      </div>
    </main>
  );
}
