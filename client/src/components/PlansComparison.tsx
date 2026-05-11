const DAYS = 22;
const MOTO_RATE = 0.21;
const CAR_RATE  = 0.50;

const PLANS = [
  { name: 'Plano 50',  vehicles: 50,  fee: 3000  },
  { name: 'Plano 100', vehicles: 100, fee: 5500  },
  { name: 'Plano 200', vehicles: 200, fee: 10000 },
  { name: 'Plano 300', vehicles: 300, fee: 10500 },
];

const fmt = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export default function PlansComparison() {
  return (
    <section className="py-20 md:py-32 bg-background">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Comparação de Planos</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Estimativas de ganhos mensais com 1 corrida por veículo × {DAYS} dias úteis.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                {['Plano', 'Investimento', 'Só Motos', 'Só Carros', 'Combinado (50/50)', 'Resultado Líquido'].map(
                  (h) => (
                    <th key={h} className="text-left py-4 px-4 font-semibold">{h}</th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {PLANS.map((p) => {
                const half     = p.vehicles / 2;
                const motoOnly = p.vehicles * DAYS * MOTO_RATE;
                const carOnly  = p.vehicles * DAYS * CAR_RATE;
                const combined = half * DAYS * MOTO_RATE + half * DAYS * CAR_RATE;
                const net      = combined - p.fee;
                return (
                  <tr key={p.name} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="py-4 px-4 font-medium">{p.name}</td>
                    <td className="py-4 px-4 text-muted-foreground">{fmt(p.fee)}</td>
                    <td className="py-4 px-4">{fmt(motoOnly)}</td>
                    <td className="py-4 px-4">{fmt(carOnly)}</td>
                    <td className="py-4 px-4 font-medium">{fmt(combined)}</td>
                    <td className={`py-4 px-4 font-bold ${net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {fmt(net)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="text-xs text-muted-foreground mt-4">
          * Combinado = metade dos veículos como motos + metade como carros, 1 corrida/dia.
        </p>
      </div>
    </section>
  );
}
