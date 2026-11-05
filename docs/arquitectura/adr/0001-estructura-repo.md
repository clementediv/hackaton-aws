---
tipo: adr
estado: aceptada
fecha: 2026-10-12
---
# ADR 0001 — Repo único como vault de Obsidian y espacio de agentes

## Contexto
Trabajamos con Obsidian (notas), Claude Code y Codex en paralelo.

## Decisión
Un solo repositorio git que es a la vez vault de Obsidian. Reglas comunes en `AGENTS.md`; `CLAUDE.md` lo importa. Tareas coordinadas en `30-tareas/board.md`.

## Consecuencias
- Un solo lugar para contexto: los agentes leen las mismas notas que el equipo.
- Hay que evitar conflictos: ramas o worktrees separadas por agente.
