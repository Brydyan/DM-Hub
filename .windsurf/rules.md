# Directrices de Desarrollo: Mineria de Datos

1. Arquitectura:
- Esquema monorepositorio con entorno de ejecución contenerizado vía Docker.
- Todo comando de validación o ejecución de Python se ejecuta dentro del contenedor `dm_analytics` (`docker compose exec analytics ...`).

2. Calidad de Código Analítico:
- Uso estricto de anotaciones de tipo (`typing`).
- Documentación con docstrings explicativos.
- Modularización de funciones en `apps/analytics/src/`.

3. Pruebas:
- Todo pipeline debe contar con pruebas unitarias usando `pytest` en `apps/analytics/tests/`.