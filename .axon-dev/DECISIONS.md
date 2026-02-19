# 🧭 AXON — DECISION LOG (ADR)

> **Formato:** Cada decisión tiene ID, contexto, opciones consideradas, y razón.
> Esto evita que un LLM futuro re-debata decisiones ya tomadas.

---

## ADR-001: Lenguaje nuevo vs. librería Python

- **Fecha:** 2026-02-16
- **Estado:** ✅ DECIDIDO
- **Contexto:** ¿Construir AXON como un lenguaje con gramática propia o como una
  librería Python (estilo LangChain/DSPy)?
- **Opciones:**
  1. Librería Python con API declarativa
  2. DSL embebido en Python con decoradores
  3. **Lenguaje propio con EBNF, lexer, parser, AST, IR**
- **Decisión:** Opción 3 — Lenguaje propio
- **Razón:** Una librería hereda el mismatch cognitivo del lenguaje host. Solo
  un lenguaje propio permite tipos semánticos, enforcement de anchors a nivel de
  lenguaje, y un AST cognitivamente consciente.

---

## ADR-002: EBNF en vez de YAML/JSON DSL

- **Fecha:** 2026-02-16
- **Estado:** ✅ DECIDIDO
- **Decisión:** Gramática EBNF formal
- **Razón:** YAML/JSON DSLs son fáciles de empezar pero imposibles de componer,
  extender o verificar formalmente. EBNF permite compilador real, errores
  reales, tooling real (lint, format, LSP).

---

## ADR-003: IR intermedio antes de backends

- **Fecha:** 2026-02-16
- **Estado:** ✅ DECIDIDO
- **Decisión:** Compilar AXON → IR (JSON-serializable) → Backend específico
- **Razón:** Desacopla programas AXON de cualquier modelo. Permite futuras
  pasadas de optimización. Los programas son model-agnostic.

---

## ADR-004: Python como lenguaje de implementación

- **Fecha:** 2026-02-16
- **Estado:** ✅ DECIDIDO
- **Opciones:**
  1. Rust (máximo rendimiento, curva alta)
  2. **Python (máxima velocidad de desarrollo, ecosistema AI)**
  3. TypeScript (viable, pero fragmenta el ecosistema)
- **Decisión:** Python
- **Razón:** Ecosistema AI nativo (anthropic, openai, ollama SDKs). Velocidad de
  prototipado. Se puede optimizar a Rust después si es necesario.

---

## ADR-005: Anchors hard vs. soft guidelines

- **Fecha:** 2026-02-16
- **Estado:** ✅ DECIDIDO
- **Decisión:** Anchors son restricciones DURAS enforzadas mecánicamente por el
  runtime
- **Razón:** System prompts con "be careful" son advisory y pueden ser
  ignorados. Los anchors de AXON son leyes, no sugerencias.

---

## ADR-006: `refine` vs. retry simple

- **Fecha:** 2026-02-16
- **Estado:** ✅ DECIDIDO
- **Decisión:** `refine` pasa contexto de fallo al modelo para mejora deliberada
- **Razón:** Un retry simple es estocástico. `refine` es closed-loop learning
  dentro de una ejecución.
