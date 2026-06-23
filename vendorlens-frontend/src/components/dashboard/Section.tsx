const Section = ({
  title, icon, children,
}: {
  title: string; icon: React.ReactNode; children: React.ReactNode;
}) => (
  <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
    <div className="flex items-center gap-2 px-4 py-2.5 border-b bg-muted/30">
      <span className="text-primary">{icon}</span>
      <span className="text-sm font-semibold text-foreground">{title}</span>
    </div>
    {children}
  </div>
);

export default Section;
