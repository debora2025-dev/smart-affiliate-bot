import { DollarSign, TrendingUp, Users, CircleAlert } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

const RULES = [
  {
    icon: DollarSign,
    color: 'bg-blue-100 text-blue-600',
    title: 'Taxa de Adesão',
    description: 'Investimento inicial para participar da plataforma',
    value: 'R$ 50,00',
  },
  {
    icon: TrendingUp,
    color: 'bg-green-100 text-green-600',
    title: 'Comissão por Corrida',
    description: 'Ganho automático por cada corrida registrada',
    value: 'R$ 0,21 (moto) / R$ 0,50 (carro)',
  },
  {
    icon: Users,
    color: 'bg-purple-100 text-purple-600',
    title: 'Bônus por Indicação',
    description: 'Ganhe por cada motorista ativo que você indicar',
    value: 'R$ 1,50 por motorista',
  },
];

export default function DriverRules() {
  return (
    <section id="drivers" className="py-20 md:py-32 bg-background">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Oportunidades para Motoristas</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Regras simples e transparentes para maximizar seus ganhos na plataforma.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {RULES.map((r) => (
            <Card key={r.title} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${r.color}`}>
                  <r.icon className="h-6 w-6" />
                </div>
                <CardTitle>{r.title}</CardTitle>
                <CardDescription>{r.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-primary">{r.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Bônus alert card */}
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <div className="flex items-start gap-3">
              <CircleAlert className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <CardTitle className="text-amber-900">Como Funciona o Bônus de Indicação</CardTitle>
                <CardDescription className="text-amber-700 mt-1">
                  Quando você indica um novo motorista, ele recebe um bônus de R$ 1,50 após completar
                  7 dias ativos na plataforma. Quanto mais motoristas você indicar, maiores serão
                  seus ganhos extras!
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>
    </section>
  );
}
