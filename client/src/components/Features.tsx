import { ChartColumnIcon, Users, TrendingUp, Zap, Shield, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

const FEATURES = [
  {
    icon: ChartColumnIcon,
    title: 'Dashboard Completo',
    description: 'Visão geral em tempo real de sua frota, motoristas ativos e ganhos acumulados.',
  },
  {
    icon: Users,
    title: 'Gestão de Motoristas',
    description: 'Cadastro, controle de status e acompanhamento de dias ativos na plataforma.',
  },
  {
    icon: TrendingUp,
    title: 'Calculadora de Ganhos',
    description: 'Estime seus ganhos por tipo de veículo com base em corridas realizadas.',
  },
  {
    icon: Zap,
    title: 'Registro de Corridas',
    description: 'Registre corridas de motos e carros com cálculos automáticos e precisos.',
  },
  {
    icon: Shield,
    title: 'Segurança Garantida',
    description: 'Dados protegidos com criptografia e conformidade com padrões de segurança.',
  },
  {
    icon: Clock,
    title: 'Suporte 24/7',
    description: 'Equipe dedicada para ajudar você a maximizar os ganhos da sua frota.',
  },
];

export default function Features() {
  return (
    <section id="features" className="py-20 md:py-32 bg-background">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Recursos Poderosos para Sua Frota</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Tudo que você precisa para gerenciar sua frota e maximizar ganhos em um único lugar.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <Card key={f.title} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <f.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>{f.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">{f.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
