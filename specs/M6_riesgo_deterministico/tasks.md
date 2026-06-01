# Tasks — M6.1 Semáforo de riesgo determinístico y predicción dinámica

- [x] 1. Crear módulo risk_rules.py con función determinística de semáforo
  - Crear `modules/predictive/risk_rules.py`
  - Implementar `calcular_etiqueta_riesgo(rend_predicho, promedio_historico, umbral_alto, umbral_medio) -> tuple[str, float]`
  - Lógica: `caida_pct = (promedio_historico - rend_predicho) / promedio_historico`
  - Si `promedio_historico <= 0` o NaN: retornar `("Bajo", 0.0)` y loggear warning
  - Si `rend_predicho < 0`: clampear a 0.0 antes de calcular
  - Si `caida_pct >= umbral_alto`: retornar `("Alto", caida_pct)`
  - Si `caida_pct >= umbral_medio`: retornar `("Medio", caida_pct)`
  - Si `caida_pct < umbral_medio` o negativa: retornar `("Bajo", 0.0)`
  - Usar `UMBRAL_RIESGO_ALTO` y `UMBRAL_RIESGO_MEDIO` de `shared/config.py` como defaults

- [x] 2. Actualizar umbrales en shared/config.py
  - Cambiar `UMBRAL_RIESGO_ALTO = 0.15` (era 0.20)
  - Cambiar `UMBRAL_RIESGO_MEDIO = 0.07` (era 0.10)

- [x] 3. Actualizar POST /predecir en orchestrator/main.py
  - Calcular `promedio_historico` como media de `target_rendimiento` de todas las filas históricas del municipio+cultivo en `feature_matrix.parquet`; si todos son NaN usar `rendimiento_t1`
  - Si `req.año > max_año + 5`: retornar HTTP 422 "El año objetivo no puede superar en más de 5 años el último dato histórico"
  - Si `req.año == max_año + 1`: usar `last_row` como base (comportamiento actual)
  - Si `req.año > max_año + 1`: iterar desde `max_año + 1` hasta `req.año` actualizando `rendimiento_t1`, `rendimiento_prom3a` y `tendencia_rend_3a` con los valores predichos del año anterior
  - Reemplazar clasificador XGBoost por `calcular_etiqueta_riesgo(rend_esperado, promedio_historico)` de `modules/predictive/risk_rules`
  - Eliminar carga de `clf_model_path`, `clf_meta_path`, `classifier` y `clf_features`
  - El contrato JSON de respuesta no cambia

- [x] 4. Actualizar POST /escenario para usar semáforo determinístico
  - Modificar `modules/predictive/scenarios.py`: reemplazar uso del clasificador por `calcular_etiqueta_riesgo`
  - La función `simulate_scenarios` debe aceptar `promedio_historico` como parámetro opcional float
  - Actualizar endpoint `POST /escenario` en `orchestrator/main.py` para calcular `promedio_historico` y pasarlo a `simulate_scenarios`
  - Mantener el mismo esquema de salida del DataFrame (mismas columnas)

- [x] 5. Crear validate_m6.py con tests de criterios de aceptación
  - Crear `specs/M6_riesgo_deterministico/validate_m6.py`
  - Test 1: `calcular_etiqueta_riesgo(0.8, 1.2)` → etiqueta "Alto", caida_pct ≈ 0.333
  - Test 2: `calcular_etiqueta_riesgo(1.1, 1.2)` → etiqueta "Medio", caida_pct ≈ 0.083
  - Test 3: `calcular_etiqueta_riesgo(1.3, 1.2)` → etiqueta "Bajo", caida_pct 0.0
  - Test 4: `calcular_etiqueta_riesgo(1.0, 0.0)` → `("Bajo", 0.0)` sin excepción
  - Test 5: `calcular_etiqueta_riesgo(-0.5, 1.2)` → clampea a 0.0, retorna "Alto"
  - Test 6: `UMBRAL_RIESGO_ALTO == 0.15` y `UMBRAL_RIESGO_MEDIO == 0.07`
  - Imprimir PASS/FAIL por test, salir con código 0 si todos pasan, 1 si alguno falla
