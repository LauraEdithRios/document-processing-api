# Declaración de Uso de IA

> Cumplimiento de política de uso de IA — Desafío Técnico

---

## 1. Herramienta Utilizada

| Campo | Detalle |
|-------|---------|
| Herramienta | Claude (Anthropic) |
| Acceso | Claude Code — CLI + extensión de VS Code |
| Modelo | Claude Sonnet 4.6 |
| Interfaz | Sesión interactiva de pair-programming en terminal y VS Code |

---

## 2. Alcance de la Asistencia de IA

El proyecto fue desarrollado mediante un enfoque colaborativo, donde el desarrollador tuvo un rol activo en la definición, implementación y validación de cada componente del sistema.

La interacción fue iterativa y basada en evidencia: el desarrollador definió los requerimientos, implementó funcionalidades, ejecutó el sistema en condiciones reales y reprodujo errores. La IA actuó como herramienta de apoyo, proporcionando sugerencias de implementación, validación técnica y alternativas de solución.

La IA no operó de manera autónoma en ningún componente crítico. En los casos en que generó borradores iniciales (esquemas Pydantic, dashboard, archivos Docker y documentación), estos fueron revisados, ajustados y validados por el desarrollador antes de su integración. Todas las decisiones arquitectónicas y la responsabilidad técnica recaen en el desarrollador.

---

## 3. Detalle de Participación por Área

La tabla distingue dos patrones de colaboración: **(A)** componentes implementados por el desarrollador con asistencia puntual de la IA, y **(B)** componentes donde la IA generó un borrador inicial que el desarrollador revisó y validó.

| Área / Componente | Autoría y Rol de la IA |
|---|---|
| Estructura del proyecto (carpetas, modelos base, configuración de BD) | **A** — Desarrollador. IA para validación y sugerencias estructurales. |
| Handlers de endpoints de la API (`app/api/v1/process.py`) | **A** — Desarrollador. IA para ejemplos y ajustes menores. |
| Capa de servicios (`app/services/process_service.py`) | **A** — Desarrollador. IA en validación de reglas de negocio. |
| Capa de repositorio (`app/repositories/process_repository.py`) | **A** — Desarrollador. IA con sugerencias de optimización de consultas. |
| Worker de documentos (`app/workers/document_worker.py`) | **A** — Desarrollador. IA en patrones de concurrencia y flujo de ejecución. |
| Manager de WebSocket (`app/core/ws_manager.py`) | **A** — Desarrollador. IA en debugging y manejo de eventos. |
| Módulo de señales de proceso (`app/core/process_signals.py`) | **A** — Desarrollador. IA en manejo del ciclo de vida de procesos. |
| Modelos de SQLAlchemy | **A** — Desarrollador. IA en generación inicial y validación. |
| Esquemas Pydantic | **B** — Borrador inicial generado con IA, revisado y validado por el desarrollador. |
| Dashboard web (`static/index.html`) | **B** — Borrador inicial generado con IA, refinado y validado por el desarrollador. |
| Dockerfile y `docker-compose.yml` | **B** — Borrador inicial generado con IA, ajustado y validado por el desarrollador. |
| Documentación (`README.md`, `API_DOCS.md`, `AI_USAGE.md`) | **B** — Redacción inicial con IA, revisada y ajustada por el desarrollador. |
| Corrección de bugs y debugging | Colaborativo: diagnóstico liderado por el desarrollador, IA con propuestas de solución. |

---

## 4. Prompts Representativos

La sesión se llevó a cabo en español. Los siguientes prompts son una muestra representativa (no exhaustiva) de las interacciones técnicas. En todos los casos, el desarrollador definió el problema, reprodujo el comportamiento en ejecución y validó las soluciones propuestas.

### Sincronización de actualización en tiempo real (WebSocket)

> *"El progreso en tiempo real no se refleja en el frontend, la conexión WebSocket parece inicializarse antes de que el nodo del proceso exista en el DOM. ¿Cómo sincronizarlo entre el renderizado y la suscripción?"*

Se identificó una condición de carrera entre el renderizado del DOM y la inicialización de la conexión WebSocket. Se resolvió reubicando `connectWS` al momento en que el nodo ya está disponible en la interfaz, garantizando la correcta recepción de eventos.

### Validación de acciones de usuario y estabilidad del DOM

> *"Las acciones pause y cancel no disparan eventos correctamente. Necesito validar conectividad de WS y estabilidad del DOM ante re-renderizados."*

Se detectaron problemas en la capa de comunicación (dependencias faltantes) y en la presentación (re-renderizado que invalidaba handlers). Se aplicaron ajustes en dependencias y estrategia de renderizado para asegurar la persistencia de los eventos.

### Visibilidad de procesos en ejecución

> *"El proceso en estado running no es visible sin refresh. Analizar posible problema de scroll."*

Se determinó un problema en el manejo del viewport en listas dinámicas. Se implementó una solución con `scrollIntoView` y selección automática del proceso activo.

### Extensión funcional del sistema

> *"Agregar endpoint para eliminación masiva de procesos finalizados manteniendo consistencia entre capas."*

Se implementó el endpoint `DELETE /process/clear` con su lógica en las capas de servicio y repositorio, asegurando coherencia entre persistencia, lógica de negocio y UI.

### Generación de documentación técnica

> *"Generar documentación técnica estructurada (README, API_DOCS, AI_USAGE)."*

La IA asistió en la redacción inicial. El desarrollador revisó, ajustó y validó el contenido final.

---

## 5. Modificaciones al Código Post-Asistencia

Todo el código fue ejecutado y validado en entorno real. La siguiente tabla registra los ajustes realizados por el desarrollador sobre las propuestas de la IA:

| Modificación | Motivo |
|---|---|
| `threading.Event.wait(timeout=0.5)` en loop | Evitar bloqueo del servidor al pausar procesos |
| `process_signals.shutdown()` en lifecycle | Liberar workers correctamente en shutdown |
| `PRAGMA WAL` en SQLite | Evitar errores `database is locked` en accesos concurrentes |
| `_file_delay()` dinámico | Leer variables de entorno en runtime en lugar de en import |
| Reubicación de `connectWS` | Resolver condición de carrera entre renderizado DOM e inicialización WS |
| `cache: 'no-store'` en fetch | Evitar respuestas cacheadas que ocultaban el estado real |
| Renderizado de botones condicional | Evitar pérdida de event handlers ante re-renderizados de la UI |

---

## 6. Conclusión

El uso de IA se mantuvo como complemento al proceso de desarrollo, acelerando tareas puntuales en un contexto de tiempo acotado, sin reemplazar el criterio técnico ni la toma de decisiones del desarrollador.

**Responsabilidades del desarrollador:**

- Definición de requerimientos y alcance funcional
- Implementación de todos los componentes principales
- Ejecución del sistema y reproducción de errores en condiciones reales
- Análisis de logs, consola y comportamiento en runtime
- Validación de cada cambio antes de su integración
- Revisión de los borradores generados por IA (esquemas, dashboard, Docker, documentación)
- Decisiones arquitectónicas y responsabilidad técnica del resultado final

El resultado es un sistema con validación funcional sobre ejecución real, con consistencia técnica verificada en cada etapa del desarrollo.

