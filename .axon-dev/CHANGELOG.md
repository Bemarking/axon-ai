# 📜 AXON — CHANGELOG

> **Regla:** Cada sesión de LLM DEBE añadir entradas aquí al final. Formato:
> `[YYYY-MM-DD] CATEGORÍA: descripción breve`

---

## 2026-02-18

- `[2026-02-18]` **BACKENDS**: 3 backends reales implementados:
  - `web_search_serper.py` — WebSearch via Serper.dev API (httpx async)
  - `file_reader_local.py` — FileReader con protección path-traversal
  - `code_executor_subprocess.py` — CodeExecutor via subprocess + asyncio
- `[2026-02-18]` **INFRA**: `backends/__init__.py` — `register_all_backends()`
  condicional (API keys + dependencias)
- `[2026-02-18]` **INFRA**: `create_default_registry()` ahora acepta
  `mode="stub"|"real"|"hybrid"`
- `[2026-02-18]` **CONFIG**: `.env.example` + `.gitignore` para API keys
- `[2026-02-18]` **TEST**: 35 tests para backends reales
  (`test_tool_backends.py`)
- `[2026-02-18]` **FIX**: `backends/__init__.py` — string literal sin cerrar
  (SyntaxError)
- `[2026-02-18]` **STATUS**: Tests totales: 731 passed, 2 pre-existentes (IR
  serialization)

## 2026-02-16

- `[2026-02-16]` **INIT**: Proyecto creado con tres archivos fundacionales
- `[2026-02-16]` **SPEC**: `brain.md` completado — AXON_SPEC v0.1.0 (1374
  líneas)
  - 12 primitivos cognitivos definidos
  - Gramática EBNF formal completa
  - Sistema de tipos semánticos (epistémicos, contenido, análisis,
    estructurales)
  - 3 programas canónicos (Contract Analyzer, Research Intelligence, Code
    Review)
  - Modelo de errores de 6 niveles
  - Arquitectura de compilador y runtime definida
  - IR specification (JSON-serializable)
  - Trace format specification
- `[2026-02-16]` **SPEC**: `big-picture.md` completado — Visión y filosofía
- `[2026-02-16]` **SPEC**: `north-star.md` completado — Roadmap de 6 fases
- `[2026-02-16]` **ENV**: `.venv` creado y activado (Python)
- `[2026-02-16]` **TRACKING**: Sistema `.axon-dev/` creado con STATUS,
  ARCHITECTURE, CHANGELOG, DECISIONS, y tracking por fases
- `[2026-02-16]` **SPEC**: Backend Gemini (Google AI) añadido — ahora 4
  backends: Anthropic, OpenAI, Gemini, Ollama
