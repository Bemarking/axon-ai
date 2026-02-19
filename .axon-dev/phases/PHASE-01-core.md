# 🔧 FASE 1 — NÚCLEO DEL LENGUAJE

> **Meta:** Construir Lexer → Parser → AST → Type Checker **Prioridad:** 🔴
> CRÍTICA — Todo lo demás se construye sobre esto **Estado:** ✅ COMPLETADO

---

## Componentes y Progreso

### 1.1 Token Definitions (`tokens.py`) — ✅ COMPLETADO

- Define 35 keywords, 6 literal types, 12 symbols, 6 comparison operators, 3
  special tokens
- Keyword lookup table para discriminación keyword/identifier

### 1.2 Lexer (`lexer.py`) — ✅ COMPLETADO

- Lexer single-pass escrito a mano
- Soporte: strings con escapes, int, float, duration, bool
- Line/column tracking completo para errores descriptivos
- Comments `//` y `/* */`

### 1.3 AST Nodes (`ast_nodes.py`) — ✅ COMPLETADO

- 27 nodos cognitivos (no mecánicos)
- Nodos clave: PersonaDefinition, FlowDefinition, ReasonChain, AnchorConstraint,
  ProbeDirective, WeaveNode
- Todos con line/column tracking

### 1.4 Parser (`parser.py`) — ✅ COMPLETADO

- Recursive descent parser con 20+ métodos de parsing
- Un método por production rule de la EBNF
- Errores descriptivos con línea, columna, expected vs found

### 1.5 Type Checker (`type_checker.py`) — ✅ COMPLETADO

- Name resolution y type compatibility checks
- Reglas epistémicas: Opinion vs FactualClaim, Uncertainty propagation
- Validación de wiring en run statements
- Constraint enforcement para campos obligatorios

### 1.6 Error Hierarchy (`errors.py`) — ✅ COMPLETADO

- AxonError base → AxonLexerError, AxonParseError, AxonTypeError
- Cada error incluye: line, column, context descriptivo

---

## Tests — ✅ 83 TESTS PASANDO

- [x] `tests/test_lexer.py` — 9 test classes, keywords, literals, symbols,
      errors
- [x] `tests/test_parser.py` — 12 test classes, todas las construcciones del
      lenguaje
- [x] `tests/test_type_checker.py` — 10 test classes, validación epistémica
      completa

---

## Notas y Decisiones de Fase

- **Bug fix:** Parser corregido para manejar `import axon.anchors.{X, Y}` — el
  DOT antes de `{` ahora se trata como separador de named imports en vez de
  inicio de path segment.
- **AST cognitivo:** Todos los nodos hablan el lenguaje de inteligencia, no de
  programación mecánica.
- **Type system epistémico:** Rastrea la naturaleza y confiabilidad de la
  información.
