import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PLANS = [
  { id: "50",  label: "Plano 50 - R$ 3.000",  motorRate: 0.21, carRate: 0.50 },
  { id: "100", label: "Plano 100 - R$ 5.500",  motorRate: 0.21, carRate: 0.50 },
  { id: "200", label: "Plano 200 - R$ 10.000", motorRate: 0.21, carRate: 0.50 },
  { id: "300", label: "Plano 300 - R$ 10.500", motorRate: 0.21, carRate: 0.50 },
];

export default function Calculator() {
  const [planId, setPlanId] = useState("100");
  const [motorcycles, setMotorcycles] = useState(50);
  const [cars, setCars] = useState(0);
  const [ridesPerDay, setRidesPerDay] = useState(1);
  const [month, setMonth] = useState(1);
  const [daysInMonth, setDaysInMonth] = useState(22);

  const plan = PLANS.find((p) => p.id === planId) ?? PLANS[1];

  const motoEarnings = motorcycles * ridesPerDay * daysInMonth * plan.motorRate;
  const carEarnings  = cars        * ridesPerDay * daysInMonth * plan.carRate;
  const total        = motoEarnings + carEarnings;

  const fmt  = (val: number) =>
    val.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const pad2 = (n: number) => String(n).padStart(2, "0");

  return (
    <section id="calculator" className="py-20 md:py-32">
      <div className="container">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Calcule seus Ganhos</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Configure os parâmetros para calcular seus ganhos
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* ── Inputs ─────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle>Parâmetros</CardTitle>
            </CardHeader>
            <CardContent className="px-6 space-y-6">

              {/* Plano */}
              <div className="space-y-2">
                <Label htmlFor="plan">Selecione o Plano</Label>
                <Select value={planId} onValueChange={setPlanId}>
                  <SelectTrigger id="plan" className="w-fit">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PLANS.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Motos */}
              <div className="space-y-2">
                <Label htmlFor="motorcycles">Quantidade de Motos</Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="motorcycles"
                    type="number"
                    min={0}
                    value={motorcycles}
                    onChange={(e) => setMotorcycles(Math.max(0, Number(e.target.value)))}
                    className="flex-1"
                  />
                  <span className="text-sm text-muted-foreground">
                    R$ {plan.motorRate.toFixed(2)}/corrida
                  </span>
                </div>
              </div>

              {/* Carros */}
              <div className="space-y-2">
                <Label htmlFor="cars">Quantidade de Carros</Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="cars"
                    type="number"
                    min={0}
                    value={cars}
                    onChange={(e) => setCars(Math.max(0, Number(e.target.value)))}
                    className="flex-1"
                  />
                  <span className="text-sm text-muted-foreground">
                    R$ {plan.carRate.toFixed(2)}/corrida
                  </span>
                </div>
              </div>

              {/* Corridas por veículo por dia — máx 2 dígitos (99) */}
              <div className="space-y-2">
                <Label htmlFor="ridesPerDay">Corridas por Veículo por Dia</Label>
                <Input
                  id="ridesPerDay"
                  type="number"
                  min={1}
                  max={99}
                  value={ridesPerDay}
                  onChange={(e) =>
                    setRidesPerDay(Math.min(99, Math.max(1, Number(e.target.value))))
                  }
                />
              </div>

              {/* Data: Mês + Dias */}
              <div className="space-y-2">
                <Label>Data</Label>
                <div className="flex items-center gap-4">
                  <div className="space-y-1 flex-1">
                    <Label
                      htmlFor="month"
                      className="text-xs text-muted-foreground"
                    >
                      Mês (00–12)
                    </Label>
                    <Input
                      id="month"
                      type="number"
                      min={0}
                      max={12}
                      value={pad2(month)}
                      onChange={(e) =>
                        setMonth(Math.min(12, Math.max(0, Number(e.target.value))))
                      }
                    />
                  </div>
                  <div className="space-y-1 flex-1">
                    <Label
                      htmlFor="daysInMonth"
                      className="text-xs text-muted-foreground"
                    >
                      Dias (00–31)
                    </Label>
                    <Input
                      id="daysInMonth"
                      type="number"
                      min={0}
                      max={31}
                      value={pad2(daysInMonth)}
                      onChange={(e) =>
                        setDaysInMonth(Math.min(31, Math.max(0, Number(e.target.value))))
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Cálculo baseado em {motorcycles + cars} veículos ×{" "}
                  {daysInMonth} dias
                </p>
              </div>
            </CardContent>
          </Card>

          {/* ── Resultados ─────────────────────────── */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="font-semibold text-lg">Ganhos com Motos</CardTitle>
              </CardHeader>
              <CardContent className="px-6">
                <p className="text-3xl font-bold text-primary">{fmt(motoEarnings)}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {motorcycles} motos × {daysInMonth} dias
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="font-semibold text-lg">Ganhos com Carros</CardTitle>
              </CardHeader>
              <CardContent className="px-6">
                <p className="text-3xl font-bold text-primary">{fmt(carEarnings)}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {cars} carros × {daysInMonth} dias
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="font-semibold text-lg">
                  Total de Ganhos ({motorcycles + cars} veículos × {daysInMonth} dias)
                </CardTitle>
              </CardHeader>
              <CardContent className="px-6">
                <p className="text-3xl font-bold text-primary">{fmt(total)}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {ridesPerDay} corrida{ridesPerDay !== 1 ? "s" : ""}/dia × {daysInMonth} dias
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
