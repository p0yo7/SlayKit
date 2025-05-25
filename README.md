# Reto Hey Banco, Datathon 2025


### Impacto al Negocio
Buscamos generar experiencias que apoyen la retención de clientes y la
generación del valor.Una pieza clave en esta ecuación es la capacidad de anticipar cuándo y cómo
los clientes realizarán gastos de forma consistente y predecible. Esto incluye,
pero no se limita a, suscripciones, facturas de servicios, compras habituales de
ciertos productos o cualquier otro gasto que demuestre una periodicidad clara.

### Objetivo
Generar un modelo predictivo que sea capaz de identificar y predecir los
gastos recurrentes de los clientes. Esto implica no solo detectar estos patrones,
sino también prever la probabilidad de que ocurran en el futuro y, si es posible,
estimar el monto, fecha y comercio de dicho gasto.

### Consejos
- Entiende el Problema a Fondo: Dedica tiempo a comprender el objetivo, las métricas y las restricciones del
reto antes de empezar a codificar.
- Exploración de Datos (EDA): Visualiza y analiza tus datos para descubrir patrones, problemas de calidad e
ideas clave.
- Empieza Sencillo y Luego Itera: Construye una solución base rápida y funcional, para luego iterar y mejorar
progresivamente.
- Colaboración Efectiva en Equipo: Comunica, divide tareas y usa herramientas de control de versiones para
maximizar la productividad del equipo.
- Gestión del Tiempo y Priorización: Planifica tus fases de trabajo y enfócate en las tareas que generarán el
mayor impacto en tu solución final.

### Evaluación 
- Se evaluará la precisión, creatividad,
impacto al negocio e storytelling de la
solución.

### Posibles Soluciones
- Usar modelos basados en series de tiempo y clustering, como por ejemplo DBSCAN o KMeans, 
agrupando por cliente, comercio, monto e intervalos entre fechas. 
- Asimismo se pueden usar patrones de frecuencia, como FP-Growth. 
- Para lograr una predicción de recurrencia es posible predecir si los gastos volverán a ocurrir y cuándo. Se puede usar:

- Modelos de series temporales individuales por cliente y comercio: Prophet el cual es de fácil uso, robusto. ARIMA si se tienen suficientes datos por serie, LSTM (Long Short-Term Memory) si se desea una solución con aprendizaje profundo. 
- Modelos de clasificación + regresión: Un clasificador para determinar si es probable que el gasto ocurra, tal como Random Forest, XGBoost, Logistic Regression y/o regressor para predecir monto tal como XGBoost Regressor, LightGBM, Linear Regression

