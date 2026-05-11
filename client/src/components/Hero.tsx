import { TrendingUp, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-primary/5 via-background to-background py-20 md:py-32">
      {/* Decorative blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-amber-500/10 blur-3xl" />
      </div>

      <div className="container relative z-10">
        <div className="grid gap-12 md:grid-cols-2 md:gap-8 items-center">
          {/* Left */}
          <div className="flex flex-col gap-6">
            <div className="inline-flex items-center gap-2 w-fit px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
              <TrendingUp className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">Gestão de Frotas Inteligente</span>
            </div>

            <h1 className="text-4xl md:text-5xl font-bold leading-tight text-foreground">
              Maximize seus ganhos com a{' '}
              <span className="text-primary">Rode Bem Veículos</span>
            </h1>

            <p className="text-lg text-muted-foreground">
              Plataforma completa de gestão de frotas. Controle motoristas, calcule ganhos
              em tempo real e aumente a eficiência da sua operação.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <a href="#calculator">
                <Button size="lg">
                  Começar Agora <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </a>
              <a href="#plans">
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  Ver Planos
                </Button>
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-8 border-t border-border">
              <div>
                <p className="text-2xl font-bold text-primary">4</p>
                <p className="text-sm text-muted-foreground">Planos Flexíveis</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-primary">0,21</p>
                <p className="text-sm text-muted-foreground">R$ por Corrida (Moto)</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-primary">0,50</p>
                <p className="text-sm text-muted-foreground">R$ por Corrida (Carro)</p>
              </div>
            </div>
          </div>

          {/* Right – image card */}
          <div className="flex justify-center md:justify-end">
            <div className="relative w-full max-w-md">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/20 to-amber-500/20 blur-2xl" />
              <div className="relative rounded-2xl bg-gradient-to-br from-primary/10 to-amber-500/10 border border-primary/20 p-8 backdrop-blur">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 rounded-xl bg-background/80 border border-border">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                      <TrendingUp className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm">Ganhos do Mês</p>
                      <p className="text-2xl font-bold text-primary">R$ 4.686</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl bg-background/80 border border-border text-center">
                      <p className="text-xs text-muted-foreground">Motos</p>
                      <p className="font-bold text-primary">R$ 0,21</p>
                      <p className="text-xs text-muted-foreground">por corrida</p>
                    </div>
                    <div className="p-3 rounded-xl bg-background/80 border border-border text-center">
                      <p className="text-xs text-muted-foreground">Carros</p>
                      <p className="font-bold text-primary">R$ 0,50</p>
                      <p className="text-xs text-muted-foreground">por corrida</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
