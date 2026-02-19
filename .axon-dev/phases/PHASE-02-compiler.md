# 🧪 FASE 2 — COMPILADOR (IR + Backends)

> **Meta:** AST → IR intermedio → Backends de modelo (Anthropic, OpenAI, Ollama)
> **Prioridad:** 🟠 ALTA — depende de Fase 1 completa **Prerequisito:** Fase 1
> ✅

---

## Componentes

### 2.1 IR Nodes (`ir_nodes.py`) — ⬜ NO INICIADO

- Define la representación intermedia JSON-serializable
- Cada nodo IR es model-agnostic

### 2.2 IR Generator (`ir_generator.py`) — ⬜ NO INICIADO

- Transforma AST validado → AXON IR
- Resuelve dependencias entre steps
- Construye el DAG de ejecución

### 2.3 Base Backend (`base_backend.py`) — ⬜ NO INICIADO

- Interface abstracta que todo backend implementa
- Métodos: `compile_step()`, `execute_step()`, `validate_output()`

### 2.4 Anthropic Backend (`anthropic.py`) — ⬜ NO INICIADO

- Compila IR steps a prompts para Claude
- Gestiona system prompt (persona + anchors)
- Gestiona tool use

### 2.5 Gemini Backend (`gemini.py`) — ⬜ NO INICIADO

- Compila IR steps a prompts para Gemini (Google AI)
- Gestiona system instructions + tool declarations
- Soporte para Gemini 2.5 Pro/Flash

### 2.6 OpenAI Backend (`openai.py`) — ⬜ NO INICIADO

### 2.7 Ollama Backend (`ollama.py`) — ⬜ NO INICIADO

---

_(Se expande cuando se inicie esta fase)_
