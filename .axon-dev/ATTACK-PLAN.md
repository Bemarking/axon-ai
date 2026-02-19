# 🎯 AXON — PLAN DE ATAQUE

> **Metodología:** Iterative & Incremental Development (basado en principios de
> Compiler Engineering) **Stack:** Python 3.12+ · pytest · anthropic/openai SDKs
> **Filosofía:** "Make it work → Make it right → Make it fast"

---

## Principios de Ingeniería

1. **Bottom-up con validación continua** — Cada capa se testea completamente
   antes de construir la siguiente
2. **Test-first para el compilador** — Los 3 programas canónicos del spec son
   los golden tests
3. **Contract-driven** — Interfaces definidas antes de implementación
4. **Dogfooding temprano** — Usar AXON contra una API real lo antes posible
   (Fase 3)
5. **Sesión-resiliente** — Los archivos `.axon-dev/` permiten a cualquier LLM o
   humano continuar sin pérdida

---

## 🏗️ FASE 0 — SPEC & FUNDACIONES ✅

| Entregable          | Estado |
| ------------------- | ------ |
| AXON_SPEC v0.1.0    | ✅     |
| Gramática EBNF      | ✅     |
| Sistema de tipos    | ✅     |
| Programas canónicos | ✅     |
| Modelo de errores   | ✅     |
| `.venv` configurado | ✅     |
| Sistema de tracking | ✅     |

---

## 🔧 FASE 1 — NÚCLEO DEL LENGUAJE ⬜

> **Objetivo:** Poder parsear cualquier archivo `.axon` válido y producir un AST
> tipado

### Sprint 1.1: Tokenización

| Tarea               | Archivo         | Criterio de éxito                            |
| ------------------- | --------------- | -------------------------------------------- |
| Definir token types | `tokens.py`     | Enum con todos los tokens del EBNF           |
| Implementar lexer   | `lexer.py`      | Tokeniza los 3 programas canónicos sin error |
| Tests de lexer      | `test_lexer.py` | 100% green en canónicos + edge cases         |

### Sprint 1.2: Parsing

| Tarea              | Archivo          | Criterio de éxito                      |
| ------------------ | ---------------- | -------------------------------------- |
| Definir nodos AST  | `ast_nodes.py`   | Un nodo por producción EBNF relevante  |
| Implementar parser | `parser.py`      | Parsea los 3 canónicos → AST correcto  |
| Tests de parser    | `test_parser.py` | Roundtrip: source → AST → verificación |

### Sprint 1.3: Validación Semántica

| Tarea                    | Archivo                | Criterio de éxito                    |
| ------------------------ | ---------------------- | ------------------------------------ |
| Implementar type checker | `type_checker.py`      | Detecta errores semánticos conocidos |
| Tests de type checker    | `test_type_checker.py` | Programas inválidos = error claro    |

### 🚀 Gate de Fase 1

> **Criterio:** `axon check contract_analyzer.axon` parsea y valida sin errores.

---

## ⚙️ FASE 2 — COMPILADOR ⬜

> **Objetivo:** AST → IR → Prompts estructurados para al menos un backend

### Sprint 2.1: Representación Intermedia

| Tarea                 | Archivo           | Criterio de éxito             |
| --------------------- | ----------------- | ----------------------------- |
| Definir nodos IR      | `ir_nodes.py`     | Cada step del spec → nodo IR  |
| Implementar generador | `ir_generator.py` | AST canónico → IR JSON válido |

### Sprint 2.2: Primer Backend (Anthropic)

| Tarea             | Archivo           | Criterio de éxito                              |
| ----------------- | ----------------- | ---------------------------------------------- |
| Interface base    | `base_backend.py` | ABC con métodos `compile_step`, `execute_step` |
| Backend Anthropic | `anthropic.py`    | IR → prompts correctos para Claude             |

### 🚀 Gate de Fase 2

> **Criterio:** Un programa AXON produce un IR JSON válido y genera prompts
> correctos.

---

## 🏃 FASE 3 — RUNTIME ⬜

> **Objetivo:** Ejecutar un programa AXON end-to-end contra un modelo real

### Componentes

| Componente         | Archivo                 | Responsabilidad             |
| ------------------ | ----------------------- | --------------------------- |
| Executor           | `executor.py`           | Ejecuta flows paso a paso   |
| Context Manager    | `context_mgr.py`        | Mantiene estado entre steps |
| Anchor Enforcer    | `anchor_enforcer.py`    | Enforce constraints duros   |
| Semantic Validator | `semantic_validator.py` | Valida tipos de output      |
| Retry Engine       | `retry_engine.py`       | `refine` con backoff        |
| Memory Backend     | `memory_backend.py`     | Vector DB / in-memory       |
| Tracer             | `tracer.py`             | Log semántico de ejecución  |

### 🚀 Gate de Fase 3

> **Criterio:** `contract_analyzer.axon` ejecuta contra Claude y produce un
> `ContractAnalysis` tipado.

---

## 📚 FASE 4 — STANDARD LIBRARY ⬜

> **Objetivo:** Built-in personas, flows, anchors y tools

- Personas: `Analyst`, `LegalExpert`, `Coder`, `Researcher`, etc.
- Flows: `Summarize`, `ExtractEntities`, `CompareDocuments`, etc.
- Anchors: `NoHallucination`, `FactualOnly`, `SafeOutput`, etc.
- Tools: `WebSearch`, `CodeExecutor`, `FileReader`, etc.

---

## 🛠️ FASE 5 — CLI & DX ⬜

> **Objetivo:** Developer experience completa

- `axon run program.axon` — ejecutor
- `axon check program.axon` — type checker / linter
- `axon trace program.axon` — debug con razonamiento visible
- `axon compile program.axon --backend=anthropic` — multi-modelo
- VSCode syntax highlighting (TextMate grammar)
- REPL interactivo

---

## 🧪 FASE 6 — TEST SUITE & HARDENING ⬜

> **Objetivo:** Robustez y confiabilidad

- Suite de tests de compilación (edge cases)
- Tests de runtime (fallo de AI, alucinación, anchor violations)
- Benchmarks: AXON vs. prompt crudo
- Documentación técnica
- Publicación del spec

---

## Protocolo de Sesión (para humanos y LLMs)

### Al INICIAR sesión:

1. Lee `.axon-dev/STATUS.md` — ¿dónde estamos?
2. Lee `.axon-dev/ARCHITECTURE.md` — ¿cómo está el sistema?
3. Lee la fase activa en `.axon-dev/phases/PHASE-XX-*.md` — ¿qué toca?

### Al TERMINAR sesión:

1. Actualiza `STATUS.md` — campos "Estado", "Último archivo", "Siguiente acción"
2. Añade entrada(s) a `CHANGELOG.md`
3. Si tomaste decisiones, añade ADR a `DECISIONS.md`
4. Marca progreso en la fase activa
