# Decisions Log

## 2026-02-27

### Decision: Use LangGraph-style orchestration
**Rationale**: Sequential agent execution with shared state ensures predictability and debuggability.

### Decision: Single LLM wrapper
**Rationale**: All LLM access through src/core/llm/engine.py ensures consistency and easy model swapping.

### Decision: SQLite memory
**Rationale**: Simple, reliable, zero-dependency persistence. Vector embeddings optional future upgrade.

### Decision: llama3.1:8b for all tasks
**Rationale**: Deepseek-r1 too slow on CPU. Single model reduces complexity.

### Decision: Reduced article processing
**Rationale**: 5 articles per run keeps pipeline under 2 minutes on CPU.

---

## Future Considerations
- Add more RSS feeds
- Implement confidence scoring
- Add market correlation agent
- Enable GPU inference
