import Link from "next/link";
import type { HTMLAttributes, ReactNode } from "react";

export function PageFrame({ children }: { children: ReactNode }) {
  return <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-6 py-10 md:px-10">{children}</main>;
}

export function ShellCard({
  children,
  className = "",
  ...props
}: {
  children: ReactNode;
  className?: string;
} & HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={`rounded-[28px] border border-orbit-pine/10 bg-white/78 p-6 shadow-panel backdrop-blur ${className}`}
      {...props}
    >
      {children}
    </section>
  );
}

export function SectionEyebrow({ children }: { children: ReactNode }) {
  return <div className="text-xs uppercase tracking-[0.24em] text-orbit-pine/70">{children}</div>;
}

export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-[24px] border border-orbit-pine/10 bg-white/75 p-5 shadow-panel backdrop-blur">
      <div className="text-xs uppercase tracking-[0.22em] text-orbit-pine/70">{label}</div>
      <div className="mt-3 text-2xl font-semibold text-orbit-ink">{value}</div>
      <p className="mt-3 text-sm leading-6 text-orbit-ink/70">{detail}</p>
    </article>
  );
}

export function StatusBadge({
  label,
  tone = "default",
}: {
  label: string;
  tone?: "default" | "success" | "warning" | "danger";
}) {
  const toneClass =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : tone === "warning"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : tone === "danger"
          ? "border-rose-200 bg-rose-50 text-rose-700"
          : "border-orbit-pine/15 bg-orbit-mist text-orbit-pine";

  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${toneClass}`}>{label}</span>;
}

export function ActionLink({
  href,
  children,
  tone = "default",
}: {
  href: string;
  children: ReactNode;
  tone?: "default" | "muted";
}) {
  return (
    <Link
      href={href}
      className={
        tone === "muted"
          ? "inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 text-sm font-medium text-orbit-ink/75 transition hover:border-orbit-pine/30 hover:text-orbit-ink"
          : "inline-flex rounded-full bg-orbit-pine px-4 py-2 text-sm font-medium text-orbit-mist transition hover:bg-orbit-ink"
      }
    >
      {children}
    </Link>
  );
}

export function FieldLabel({ htmlFor, children }: { htmlFor: string; children: ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="text-sm font-medium text-orbit-ink/85">
      {children}
    </label>
  );
}

export function Input({
  id,
  name,
  placeholder,
  required = false,
  defaultValue,
}: {
  id: string;
  name: string;
  placeholder?: string;
  required?: boolean;
  defaultValue?: string;
}) {
  return (
    <input
      id={id}
      name={name}
      placeholder={placeholder}
      required={required}
      defaultValue={defaultValue}
      className="mt-2 w-full rounded-2xl border border-orbit-pine/10 bg-white px-4 py-3 text-sm text-orbit-ink shadow-sm outline-none transition focus:border-orbit-pine/40 focus:ring-2 focus:ring-orbit-gold/25"
    />
  );
}

export function TextArea({
  id,
  name,
  placeholder,
  required = false,
  rows = 6,
  defaultValue,
}: {
  id: string;
  name: string;
  placeholder?: string;
  required?: boolean;
  rows?: number;
  defaultValue?: string;
}) {
  return (
    <textarea
      id={id}
      name={name}
      placeholder={placeholder}
      required={required}
      rows={rows}
      defaultValue={defaultValue}
      className="mt-2 w-full rounded-3xl border border-orbit-pine/10 bg-white px-4 py-3 text-sm leading-6 text-orbit-ink shadow-sm outline-none transition focus:border-orbit-pine/40 focus:ring-2 focus:ring-orbit-gold/25"
    />
  );
}

export function SubmitButton({ children }: { children: ReactNode }) {
  return (
    <button
      type="submit"
      className="inline-flex rounded-full bg-orbit-ink px-5 py-3 text-sm font-semibold text-orbit-mist transition hover:bg-orbit-pine"
    >
      {children}
    </button>
  );
}
