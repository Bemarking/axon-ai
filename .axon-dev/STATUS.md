# 🧠 AXON — SESSION STATUS

> **INSTRUCCIÓN PARA CUALQUIER LLM:** Lee este archivo PRIMERO al iniciar
> sesión. Luego lee `ARCHITECTURE.md` y el `CHANGELOG.md` para máximo contexto.
> Consulta `phases/PHASE-XX-*.md` para la fase activa.

---

## Estado Actual del Proyecto

| Campo                      | Valor                                              |
| -------------------------- | -------------------------------------------------- |
| **Versión del Spec**       | v0.1.0                                             |
| **Fase Activa**            | FASE 4: Standard Library (en progreso)             |
| **Estado de la Fase**      | ✅ Runtime Tool System + Real Backends completos   |
| **Último Archivo Editado** | `tests/test_tool_backends.py`                      |
| **Última Sesión**          | 2026-02-18                                         |
| **Bloqueadores**           | Ninguno                                            |
| **Siguiente Acción**       | Implementar personas, anchors y flows de la stdlib |

---

## Qué está HECHO

- [x] Especificación completa del lenguaje (`brain.md` — 1374 líneas)
- [x] Filosofía y visión del proyecto (`big-picture.md`)
- [x] Roadmap de fases (`north-star.md`)
- [x] Gramática EBNF formal definida
- [x] 12 primitivos cognitivos especificados
- [x] Sistema de tipos semánticos diseñado
- [x] 3 programas canónicos de ejemplo escritos
- [x] Modelo de errores definido (6 niveles)
- [x] Arquitectura del compilador y runtime diseñada
- [x] Standard Library conceptualizada
- [x] Entorno virtual `.venv` creado y activado
- [x] **FASE 1**: Lexer → Parser → AST → Type Checker (83 tests ✅)
- [x] **FASE 2**: IR Generator → Compiler Backends (164 tests ✅)
- [x] **FASE 3**: Runtime — 7 módulos, 115 tests ✅
  - `runtime_errors.py` — Jerarquía de 6 errores con ErrorContext
  - `tracer.py` — 14 tipos de eventos, spans jerárquicos, serialización JSON
  - `context_mgr.py` — Estado mutable entre steps, snapshots inmutables
  - `semantic_validator.py` — Tipos, confianza, campos estructurados, rangos
  - `retry_engine.py` — Backoff, contexto de fallo, exhaustion handling
  - `memory_backend.py` — Interfaz abstracta + InMemoryBackend
  - `executor.py` — Protocolo ModelClient, loop de ejecución, orquestador
- [/] **FASE 4**: Standard Library — Runtime Tool System + Real Backends, 88
  tests ✅
  - **Tool Infrastructure** (53 tests):
    - `base_tool.py` — BaseTool ABC + ToolResult dataclass
    - `registry.py` — RuntimeToolRegistry con caché por config
    - `dispatcher.py` — ToolDispatcher (IR → runtime bridge, timeouts)
    - 6 stubs: WebSearch, CodeExecutor, FileReader, PDFExtractor, ImageAnalyzer,
      APICall
    - 2 reales en stubs/: Calculator (wrapper stdlib), DateTime (wrapper stdlib)
    - `executor.py` — Integración `_execute_tool_step()` con ToolDispatcher
  - **Real Backends** (35 tests):
    - `backends/web_search_serper.py` — WebSearch via Serper.dev API (httpx
      async)
    - `backends/file_reader_local.py` — FileReader local con protección
      path-traversal
    - `backends/code_executor_subprocess.py` — CodeExecutor via subprocess +
      asyncio
    - `backends/__init__.py` — `register_all_backends()` condicional por API
      keys
    - `tools/__init__.py` —
      `create_default_registry(mode="stub"|"real"|"hybrid")`
  - **Configuración**:
    - `.env` — API keys (Serper, OpenAI, Gemini, Anthropic)
    - `.env.example` — Template seguro sin keys reales
    - `.gitignore` — Excluye `.env`, `__pycache__`, `.venv`, etc.

## Qué FALTA (próximo)

- [ ] **FASE 4**: Standard Library — personas, anchors, flows restantes
- [ ] **FASE 5**: CLI + REPL + VSCode Extension
- [ ] **FASE 6**: Test Suite + Hardening + Docs

---

## Métricas del Proyecto

| Métrica             | Valor                                |
| ------------------- | ------------------------------------ |
| **Tests Totales**   | 731 (+ 2 pre-existentes)             |
| **Fase 1 Tests**    | 83 ✅                                |
| **Fase 2 Tests**    | 164 ✅                               |
| **Fase 3 Tests**    | 115 ✅                               |
| **Fase 4 Tests**    | 88 ✅ (53 infra + 35 backends)       |
| **Otros Tests**     | 281 (stdlib+misc)                    |
| **Módulos Runtime** | 7 + 11 tools + 3 backends            |
| **Bugs Conocidos**  | 2 (IR serialization, pre-existentes) |

---

## Archivos Fuente del Proyecto

| Archivo            | Qué contiene                            |
| ------------------ | --------------------------------------- |
| `project/brain.md` | AXON_SPEC v0.1.0 — spec completa        |
| `big-picture.md`   | Visión, filosofía, primitivos, sintaxis |
| `north-star.md`    | Roadmap de 6 fases (Día 0 → Día 6)      |

## Archivos de Seguimiento (esta carpeta)

| Archivo                       | Propósito                                 |
| ----------------------------- | ----------------------------------------- |
| `STATUS.md`                   | ⭐ ESTE ARCHIVO — estado global           |
| `ARCHITECTURE.md`             | Mapa de módulos, dependencias, decisiones |
| `CHANGELOG.md`                | Log cronológico de TODO lo que se hace    |
| `DECISIONS.md`                | Registro de decisiones técnicas (ADR)     |
| `phases/PHASE-01-core.md`     | Tracking detallado de Fase 1              |
| `phases/PHASE-02-compiler.md` | Tracking detallado de Fase 2              |
| _(etc.)_                      | Se crean conforme se avanza               |
