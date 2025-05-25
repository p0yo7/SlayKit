'use client'

import { useEffect, useState } from 'react'

interface WrappedResponse {
  cliente_id: string
  rango: string
  moneda: string
  total_gastado: number
  resumen_gastos: Record<string, number>
  resumen_categorias: Record<string, number>
  proporcion_essentials_vs_subs: { tipo: string; valor: number }[]
  predictibilidad_por_categoria: { categoria: string; score: number }[]
  compra_mas_iconica?: {
    fecha: string
    comercio: string
    monto: number
    mensaje: string
  }
}

interface PredictionResponse {
  total_spending: number
  per_merchant_spending: Record<string, number>
  predicted_subs: { comercio: string; monto: number; anio: number; mes: number; dia: number }[]
  iconic_commerce: string
  iconic_count: number
}

export default function WrappedSummary() {
  const [data, setData] = useState<WrappedResponse | null>(null)
  const [predictions, setPredictions] = useState<PredictionResponse | null>(null)

  useEffect(() => {
    const token = 'c1f6e6cd-3f25-4738-970c-b5d56d072f08';

    if (!token) return;

    fetch('http://localhost:8000/wrapped_gastos?desde=2020-01-01&hasta=2024-12-31&modo=comercio', {
        method: 'GET',
        headers: {
        'Content-Type': 'application/json',
        token: token
        }
    })
        .then(res => {
        if (!res.ok) {
            console.log("Error en wrapped_gastos:", res);
        }
        return res.json();
        })
        .then(wrappedData => {
        console.log("wrappedData:", wrappedData);
        setData(wrappedData);

        return fetch('http://localhost:8000/predict_gastos_recurrentes', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id_cliente: wrappedData.cliente_id, token: token })
        });
        })
        .then(res => {
        if (!res.ok) {
            // throw new Error(`Error en predict_gastos_recurrentes: ${res.status}`);
            console.log("Error en predict_gastos_recurrentes:", res);
        }
        return res.json();
        })
        .then(predictionData => {
        console.log("predictionData:", predictionData);
        setPredictions(predictionData);
        })
        .catch(err => {
        console.error("Error en alguna petición:", err);
        });
    }, []);


  if (!data) return <p className="text-gray-500">Cargando...</p>

  const topNegocios = Object.entries(data.resumen_gastos)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)

  const canalDigital = data.resumen_categorias['digital'] || 0
  const canalFisico = data.resumen_categorias['fisica'] || 0
  const canalDigitalPct = Math.round((canalDigital / (canalDigital + canalFisico)) * 100)
  const canalFisicoPct = 100 - canalDigitalPct

  const predictibilidadPromedio = Math.round(
    data.predictibilidad_por_categoria.reduce((a, b) => a + b.score, 0) / data.predictibilidad_por_categoria.length
  )

  return (
    <div className="bg-pink-700 text-white min-h-screen p-10 font-sans">
      <h1 className="text-4xl font-bold mb-8">hey, <span className="text-white">Wrap</span></h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        <div>
          <h2 className="text-xl font-semibold">Top Negocios</h2>
          <ul className="mt-2">
            {topNegocios.map(([name], i) => (
              <li key={i}>{i + 1}. <span className="font-bold">{name}</span></li>
            ))}
          </ul>

          <div className="mt-8">
            <h2 className="text-xl font-semibold">Canal Favorito</h2>
            <p className="mt-1">Digital: {canalDigitalPct}%</p>
            <p>Físico: {canalFisicoPct}%</p>
            <p className="mt-2">Prefieres la eficiencia de las plataformas digitales.</p>
          </div>

          <div className="mt-8">
            <h2 className="text-xl font-semibold">
              ¿Qué tan predecible eres?
            </h2>
            <p className="mt-2">
              Tu gasto es {predictibilidadPromedio}% constante, con algunos picos de consumo marcados por eventos.
            </p>
          </div>
        </div>

        <div>
          <div>
            <h2 className="text-xl font-semibold">Tus prioridades</h2>
            <p className="mt-2">Tu dinero habla:</p>
            {data.proporcion_essentials_vs_subs.map((item, i) => (
              <p key={i}>- {item.valor.toFixed(2)} en {item.tipo.toLowerCase()}</p>
            ))}
          </div>

          <div className="mt-12">
            <h2 className="text-xl font-semibold">Gasto más icónico</h2>
            <p className="mt-2">
              {data.compra_mas_iconica?.mensaje ?? 'No se encontró información sobre la compra más memorable.'}
            </p>
          </div>

          {predictions && (
            <div className="mt-12">
              <h2 className="text-xl font-semibold">Predicciones del siguiente mes</h2>
              <p className="mt-2">Total estimado: ${predictions.total_spending.toFixed(2)}</p>

              <div className="mt-2">
                <p className="font-semibold">Suscripciones esperadas:</p>
                {predictions.predicted_subs.length === 0 && <p>Sin suscripciones previstas.</p>}
                <ul className="list-disc list-inside">
                  {predictions.predicted_subs.map((sub, i) => (
                    <li key={i}>{sub.comercio} - ${sub.monto.toFixed(2)} el {sub.dia}/{sub.mes}/{sub.anio}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
