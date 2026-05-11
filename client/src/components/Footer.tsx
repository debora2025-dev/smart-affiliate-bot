const LINKS = {
  Produto: [
    { href: '#features',   label: 'Benefícios' },
    { href: '#plans',      label: 'Planos' },
    { href: '#calculator', label: 'Calculadora' },
    { href: '#drivers',    label: 'Para Motoristas' },
  ],
  Suporte: [
    { href: '#',           label: 'Central de Ajuda' },
    { href: '#',           label: 'Contato' },
    { href: '#',           label: 'FAQ' },
  ],
  Legal: [
    { href: '#',           label: 'Termos de Uso' },
    { href: '#',           label: 'Privacidade' },
  ],
};

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="container py-12">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div>
            <h3 className="font-bold text-lg mb-4">Rode Bem Veículos</h3>
            <p className="text-sm text-muted-foreground">
              Plataforma completa de logística de frotas para maximizar seus ganhos.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(LINKS).map(([title, links]) => (
            <div key={title}>
              <h4 className="font-semibold mb-4">{title}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {links.map((l) => (
                  <li key={l.label}>
                    <a href={l.href} className="hover:text-primary transition-colors">
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-border">
          <p className="text-sm text-muted-foreground text-center">
            © {year} Rode Bem Veículos. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </footer>
  );
}
