import { Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const PLANS = [
  {
    id: '50',
    name: 'Plano 50',
    description: 'Para frotas pequenas e em crescimento',
    price: 3000,
    people: 50,
    perPerson: 60,
    popular: false,
  },
  {
    id: '100',
    name: 'Plano 100',
    description: 'Para frotas em expansão',
    price: 5500,
    people: 100,
    perPerson: 55,
    popular: true,
  },
  {
    id: '200',
    name: 'Plano 200',
    description: 'Para frotas consolidadas',
    price: 10000,
    people: 200,
    perPerson: 50,
    popular: false,
  },
  {
    id: '300',
    name: 'Plano 300',
    description: 'Para grandes operações',
    price: 10500,
    people: 300,
    perPerson: 35,
    popular: false,
  },
];

const FEATURES = [
  'Acesso ao dashboard completo',
  'Gestão ilimitada de motoristas',
  'Registro de corridas',
  'Calculadora de ganhos',
  'Relatórios detalhados',
  'Suporte prioritário',
];

export default function Plans() {
  return (
    <section id="plans" className="py-20 md:py-32 bg-muted/30">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Planos de Assinatura</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Escolha o plano ideal para sua frota. Todos incluem acesso completo a todos os recursos.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map((plan) => (
            <Card
              key={plan.id}
              className={`relative transition-all ${
                plan.popular ? 'ring-2 ring-primary shadow-lg md:scale-105' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-primary-foreground text-xs font-semibold rounded-full">
                  Mais Popular
                </div>
              )}

              <CardHeader>
                <CardTitle>{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                <div>
                  <p className="text-4xl font-bold text-primary">
                    R$ {plan.price.toLocaleString('pt-BR')}
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    por mês para {plan.people} pessoas
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    R$ {plan.perPerson.toFixed(2)} por pessoa
                  </p>
                </div>

                <div className="space-y-3">
                  {FEATURES.map((f) => (
                    <div key={f} className="flex items-start gap-3">
                      <Check className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{f}</span>
                    </div>
                  ))}
                </div>

                <Button
                  className="w-full"
                  variant={plan.popular ? 'default' : 'outline'}
                >
                  Começar Agora
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
