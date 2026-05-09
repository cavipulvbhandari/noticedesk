interface ComingSoonProps {
  title: string;
  sprint: string;
  description: string;
}

export function ComingSoon({
  title,
  sprint,
  description,
}: ComingSoonProps): React.ReactElement {
  return (
    <section className="mx-auto max-w-2xl py-12">
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate">
        {sprint}
      </p>
      <h1 className="mt-2 font-serif text-3xl text-navy">{title}</h1>
      <p className="mt-3 text-sm text-slate">{description}</p>
    </section>
  );
}
