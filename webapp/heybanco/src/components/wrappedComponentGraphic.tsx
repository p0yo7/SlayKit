'use client'

import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#8dd1e1', '#a4de6c']

type WrappedResponse = {
  cliente_id: string
  rango: string
  moneda: string
  total_gastado: number
  resumen_gastos: { [comercio: string]: number }
  resumen_categorias: { [categoria: string]: number }
  proporcion_essentials_vs_subs: { tipo: string; valor: number }[]
  predictibilidad_por_categoria: { categoria: string; score: number }[]
}

export default function WrappedDashboard() {
  const [data, setData] = useState<WrappedResponse | null>(null)

  useEffect(() => {
  const token = 'c1f6e6cd-3f25-4738-970c-b5d56d072f08';

  fetch('http://localhost:8000/wrapped_gastos?desde=2020-01-01&hasta=2024-12-31&modo=comercio', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      token: token  // ← token como header
    }
  })
    .then(async res => {
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Wrapped API error: ${errorText}`);
      }
      return res.json();
    })
    .then(json => {
      console.log('wrapped response:', json);
      setData(json);
    })
    .catch(err => console.error('Error en wrapped_gastos:', err));
}, []);



  if (!data) return <p className="text-gray-500">Cargando...</p>

  const resumenComercios = Object.entries(data.resumen_gastos ?? {}).map(
    ([comercio, monto]) => ({ comercio, monto })
  );

  const resumenCategorias = Object.entries(data.resumen_categorias ?? {}).map(
    ([categoria, monto]) => ({ categoria, monto })
  );


  return (
    <div className="p-6 space-y-8 bg-purple-100 min-h-screen">
      <h1 className="text-3xl font-bold text-center text-purple-900">hey, Stacking Mode</h1>
      <p className="text-center text-md text-purple-800 max-w-xl mx-auto">Tú decides en qué vale la pena gastar. Nosotros te ayudamos a verlo claro.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
        <div className="bg-white p-4 rounded-2xl shadow-md">
          <h2 className="text-lg font-semibold text-purple-800 mb-2">Servicios detectadas y su costo</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={resumenComercios}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="comercio" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="monto" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-sm text-center mt-2 text-gray-600">Si mantienes tus suscripciones activas, el próximo mes vas a gastar {data.total_gastado.toLocaleString()} {data.moneda}.</p>
        </div>

        <div className="bg-white p-4 rounded-2xl shadow-md">
          <h2 className="text-lg font-semibold text-purple-800 mb-2">Proporción entre gastos esenciales y suscripciones</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.proporcion_essentials_vs_subs}
                dataKey="valor"
                nameKey="tipo"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {data.proporcion_essentials_vs_subs.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-2xl shadow-md">
          <h2 className="text-lg font-semibold text-purple-800 mb-2">Gastos por Categoría</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={resumenCategorias}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="categoria" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="monto" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-2xl shadow-md">
          <h2 className="text-lg font-semibold text-purple-800 mb-2">Nivel de predictibilidad por categoría</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data.predictibilidad_por_categoria}>
              <PolarGrid />
              <PolarAngleAxis dataKey="categoria" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} />
              <Radar name="Predictibilidad" dataKey="score" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

