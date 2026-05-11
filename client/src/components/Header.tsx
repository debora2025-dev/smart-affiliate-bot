import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

const NAV_LINKS = [
  { href: '#features', label: 'Benefícios' },
  { href: '#plans',    label: 'Planos' },
  { href: '#calculator', label: 'Calculadora' },
  { href: '#drivers', label: 'Para Motoristas' },
];

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">RB</span>
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg font-bold text-primary">Rode Bem</h1>
            <p className="text-xs text-muted-foreground">Veículos</p>
          </div>
        </div>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="text-sm font-medium hover:text-primary transition-colors">
              {l.label}
            </a>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <Button size="sm">Entrar</Button>
          <button className="md:hidden" onClick={() => setOpen((o) => !o)} aria-label="Menu">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-border bg-background px-6 py-4 space-y-3">
          {NAV_LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="block text-sm font-medium hover:text-primary transition-colors"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </a>
          ))}
        </div>
      )}
    </header>
  );
}
