# 🏗️ AXON — ARCHITECTURE REFERENCE

> **Para LLMs:** Este archivo es tu mapa. Antes de escribir código, confírmalo
> aquí.

---

## Qué es AXON

AXON es un **lenguaje de programación** cuyos primitivos son los primitivos
cognitivos de una AI. No compila a código máquina — compila a **cadenas de
prompts + orquestación** contra LLMs.

**No es**: una librería Python, un wrapper de LangChain, ni un DSL en YAML. **Sí
es**: un lenguaje con gramática EBNF, lexer, parser, AST, IR, múltiples backends
y runtime.

---

## Los 12 Primitivos Cognitivos

| #  | Primitivo | Qué representa                          | Keyword    |
| -- | --------- | --------------------------------------- | ---------- |
| 1  | Persona   | Identidad cognitiva del modelo          | `persona`  |
| 2  | Context   | Memoria de trabajo / config de sesión   | `context`  |
| 3  | Intent    | Instrucción semántica atómica           | `intent`   |
| 4  | Flow      | Pipeline composable de pasos cognitivos | `flow`     |
| 5  | Reason    | Cadena de razonamiento explícita        | `reason`   |
| 6  | Anchor    | Restricción dura (nunca violable)       | `anchor`   |
| 7  | Validate  | Gate de validación semántica            | `validate` |
| 8  | Refine    | Retry adaptativo con contexto de fallo  | `refine`   |
| 9  | Memory    | Almacenamiento semántico persistente    | `memory`   |
| 10 | Tool      | Capacidad externa invocable             | `tool`     |
| 11 | Probe     | Extracción dirigida de información      | `probe`    |
| 12 | Weave     | Síntesis semántica de múltiples outputs | `weave`    |

---

## Estructura de Módulos (Target)

```
axon-constructor/
├── project/
│   └── brain.md              # AXON_SPEC v0.1.0
├── big-picture.md            # Visión y filosofía
├── north-star.md             # Roadmap de fases
├── .axon-dev/                # 📋 Tracking de desarrollo (este dir)
│   ├── STATUS.md             # Estado global del proyecto
│   ├── ARCHITECTURE.md       # ESTE ARCHIVO
│   ├── CHANGELOG.md          # Log cronológico
│   ├── DECISIONS.md          # Registro de decisiones (ADR)
│   └── phases/               # Tracking por fase
│       ├── PHASE-01-core.md
│       ├── PHASE-02-compiler.md
│       └── ...
└── axon/                     # 🐍 Código fuente (Python)
    ├── __init__.py
    ├── compiler/
    │   ├── __init__.py
    │   ├── lexer.py           # Source → Token stream
    │   ├── tokens.py          # Token type definitions
    │   ├── parser.py          # Tokens → AST
    │   ├── ast_nodes.py       # AST node class hierarchy
    │   ├── type_checker.py    # Semantic type validation
    │   ├── ir_generator.py    # AST → AXON IR
    │   └── ir_nodes.py        # IR node definitions
    ├── backends/
    │   ├── __init__.py
    │   ├── base_backend.py    # Abstract backend interface
    │   ├── anthropic.py       # Claude backend
    │   ├── openai.py          # OpenAI backend
    │   ├── gemini.py          # Google Gemini backend
    │   └── ollama.py          # Local Ollama backend
    ├── runtime/
    │   ├── __init__.py
    │   ├── executor.py        # Flow execution engine
    │   ├── context_mgr.py     # Context state management
    │   ├── anchor_enforcer.py # Hard constraint enforcement
    │   ├── semantic_validator.py
    │   ├── retry_engine.py    # Failure recovery (refine)
    │   ├── memory_backend.py  # Semantic memory layer
    │   └── tracer.py          # Execution trace recorder
    ├── stdlib/
    │   ├── personas/          # Built-in personas
    │   ├── flows/             # Built-in flows
    │   ├── anchors/           # Built-in anchors
    │   └── tools/             # Built-in tools
    ├── cli/
    │   ├── __init__.py
    │   ├── main.py            # `axon` CLI entrypoint
    │   ├── run.py             # `axon run`
    │   ├── check.py           # `axon check`
    │   └── trace.py           # `axon trace`
    └── errors.py              # Error hierarchy (6 levels)
```

---

## Pipeline de Compilación

```
.axon source  →  Lexer  →  Token Stream  →  Parser  →  AST
                                                          ↓
                                           Type Checker (semantic validation)
                                                          ↓
                                           IR Generator → AXON IR (JSON)
                                                          ↓
                                           Backend (Anthropic | OpenAI | Gemini | Ollama)
                                                          ↓
                                           Runtime (Executor + Validators + Tracer)
                                                          ↓
                                           Typed Output (validated result)
```

---

## Sistema de Tipos Semánticos

| Categoría     | Tipos                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------ |
| Epistémicos   | `FactualClaim`, `Opinion`, `Uncertainty`, `Speculation`                                                |
| Contenido     | `Document`, `Chunk`, `EntityMap`, `Summary`, `Translation`                                             |
| Análisis      | `RiskScore(0..1)`, `ConfidenceScore(0..1)`, `SentimentScore(-1..1)`, `ReasoningChain`, `Contradiction` |
| Estructurales | `Party`, `Obligation`, `Risk` (user-defined types)                                                     |
| Reporte       | `StructuredReport` (compound type)                                                                     |

**Regla clave:** `Opinion` NUNCA puede usarse donde se espera `FactualClaim`.
`Uncertainty` propaga — cualquier cómputo con Uncertainty produce Uncertainty.

---

## Jerarquía de Errores

```
Level 1: ValidationError    — tipo de output no coincide
Level 2: ConfidenceError    — confianza por debajo del piso
Level 3: AnchorBreachError  — restricción anchor violada
Level 4: RefineExhausted    — max intentos de refine agotados
Level 5: RuntimeError       — llamada al modelo falló
Level 6: TimeoutError       — ejecución excedió límite de tiempo
```

---

## Restricciones de Diseño Inamovibles

1. **Declarativo sobre imperativo** — Se describe qué, no cómo
2. **Semántico sobre sintáctico** — Tipos = significado, no layout
3. **Cognición composable** — Bloques que se componen como neuronas
4. **Determinismo configurable** — Espectro exploración → precisión
5. **Fallo como ciudadano de primera clase** — Retry, refine, fallback nativos
