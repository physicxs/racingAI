export function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mx-auto max-w-5xl px-6 py-20">
      <h2 className="mb-10 text-center text-2xl font-semibold tracking-tight text-white sm:text-3xl">
        {title}
      </h2>
      {children}
    </section>
  );
}
