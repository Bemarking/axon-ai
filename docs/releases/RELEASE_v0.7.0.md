# AXON v0.7.0 — Paradigm Shifts

> **De compilador de prompts a Sistema Operativo Cognitivo.**

Esta release introduce tres cambios de paradigma a nivel de compilador que
transforman fundamentalmente cómo se programa inteligencia artificial con AXON.

---

## 🧠 Directivas Epistémicas

El estado de confianza de la IA es ahora un constructo de primera clase en el
lenguaje.

```axon
know {
    flow ExtractFacts(doc: Document) -> CitedFact {
        step Verify { ask: "Extract only verifiable facts" output: CitedFact }
    }
}

speculate {
    flow Brainstorm(topic: String) -> Opinion {
        step Imagine { ask: "What could be possible?" output: Opinion }
    }
}
```

**4 modos epistémicos** con restricciones calculadas en **tiempo de
compilación**:

| Modo        | Temperature | Top-p | Anchors Auto-inyectados            |
| ----------- | ----------- | ----- | ---------------------------------- |
| `know`      | 0.1         | 0.3   | RequiresCitation, NoHallucination  |
| `believe`   | 0.3         | 0.5   | NoHallucination                    |
| `speculate` | 0.9         | 0.95  | ∅                                  |
| `doubt`     | 0.2         | 0.4   | RequiresCitation, SyllogismChecker |

El compilador **no etiqueta** — transforma estructuralmente. Un bloque `know`
inyecta anchors de citación y baja el temperature a 0.1, haciendo la alucinación
una violación de restricción en tiempo de compilación.

---

## ⚡ Parallel Cognitive Dispatch

Dispatch de tareas cognitivas independientes en paralelo, como un equipo humano:

```axon
flow AnalyzeContract(doc: Document) -> Report {
    par {
        step Financial { ask: "Analyze financial exposure" output: RiskScore }
        step Regulatory { ask: "Check compliance" output: ComplianceReport }
        step Precedent { ask: "Find case law" output: CaseList }
    }
    weave [Financial, Regulatory, Precedent] into Report { format: Report }
}
```

- Verificación de dependencias en tiempo de compilación:
  `∀ bᵢ, bⱼ : deps(bᵢ) ∩ outputs(bⱼ) = ∅`
- Latencia `O(max(tᵢ))` en vez de `O(Σtᵢ)` — reducción hasta ~Nx
- Runtime via `asyncio.gather`

---

## 💤 Dynamic State Yielding

Agentes que hibernan sin costo, esperan eventos, y retoman con contexto
completo:

```axon
flow MonitorContract(id: String) -> Report {
    step InitialAnalysis { ask: "Analyze contract" output: Analysis }
    hibernate until "amendment_received"
    step FollowUp { ask: "Re-evaluate with amendments" output: Report }
}
```

- **Continuation-Passing Style (CPS)** a nivel de lenguaje
- `continuation_id` determinístico via `SHA-256(flow ∥ event ∥ position)`
- `ExecutionState` serializable: call stack, step results, context vars
- **$0 de cómputo** mientras el agente espera
- `StateBackend` protocol + `InMemoryStateBackend` (Redis/Postgres pendientes)

---

## 📊 Números

| Métrica                     | Antes | Después       |
| --------------------------- | ----- | ------------- |
| Keywords del lenguaje       | 33    | **40** (+7)   |
| Primitivas cognitivas       | 12    | **18** (+6)   |
| Nodos AST                   | 17    | **20** (+3)   |
| Nodos IR                    | 16    | **19** (+3)   |
| Tests totales               | 822   | **878** (+56) |
| Regresiones                 | —     | **0**         |
| Archivos modificados/nuevos | —     | **9**         |

## 📁 Archivos Modificados

**Compilador (6 archivos):**

- `axon/compiler/tokens.py` — 7 keywords nuevos
- `axon/compiler/ast_nodes.py` — 3 dataclasses AST
- `axon/compiler/parser.py` — 3 métodos de parsing + dispatch
- `axon/compiler/type_checker.py` — 3 validadores + dispatch en flow steps
- `axon/compiler/ir_nodes.py` — 3 nodos IR frozen
- `axon/compiler/ir_generator.py` — Constraint matrix + 3 visitors + SHA-256

**Runtime (1 archivo nuevo):**

- `axon/runtime/state_backend.py` — Protocolo `StateBackend` +
  `InMemoryStateBackend`

**Tests (1 archivo nuevo):**

- `tests/test_paradigm_shifts.py` — 56 tests cubriendo 5 capas del pipeline

**Documentación:**

- `README.md` — Sección Paradigm Shifts completa (formal, filosófica, 3 use
  cases)

---

## ⬆️ Upgrade

```bash
pip install --upgrade axon-lang
```

## Próximos Pasos (Fase 8)

- Integración del executor con los 3 paradigmas
- `RedisStateBackend` y `PostgresStateBackend` para producción
- Resolución de dependencias en `par` blocks via DAG scheduling
- `consolidate` como operador nativo post-`par`
