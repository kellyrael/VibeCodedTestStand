---
name: ni-rf-hw-specs
description: "Compare NI RF hardware specifications across VST models (PXIe-5841, PXIe-5842, PXIe-5860, PXIe-5831). Use when users ask to compare VST specs, select RF hardware, understand instrument capabilities, or need frequency range, bandwidth, output power, phase noise, or other RF specifications for NI Vector Signal Transceivers."
argument-hint: "Ask about VST model comparison, RF hardware selection, instrument specifications, frequency range, bandwidth, output power, or any NI VST capability question."
user-invocable: true
---

# NI RF Hardware Specifications

Provides accurate, specification-document-sourced comparison tables for NI PXIe Vector Signal Transceivers (VSTs). Use this skill whenever a user asks about VST capabilities, hardware selection, or instrument specifications.

## ⚠️ CRITICAL: Read This First

**Before answering any VST comparison or hardware selection question**, read [`references/VST-Family.md`](references/VST-Family.md) for the complete specifications table sourced directly from NI specification documents.

## Data Completeness Rule

**NEVER** use vague placeholders like "See spec document", "See charts", "Per-port", or "See constituent module specs" in specification tables. Every cell must contain a concrete numeric value. If a value is truly unavailable, write "Not specified — <reason>".

## When to Use This Skill

- User asks to **compare** NI VST models (5841, 5842, 5860, 5831)
- User asks about **frequency range**, **bandwidth**, **output power**, or other RF specs
- User needs to **select hardware** for a specific test application (Wi-Fi, 5G, mmWave, etc.)
- User asks "which VST should I use for..." questions
- User asks about **instrument capabilities** or **differences** between VSTs

## Reference Files

| File | Purpose |
|---|---|
| `references/VST-Family.md` | Complete side-by-side specifications table for PXIe-5841, 5842, 5860, 5831 |

## How to Respond

1. Read `references/VST-Family.md`
2. Present the full comparison table or the relevant subset based on the user's question
3. Include the **Key Takeaways** section to help with hardware selection
4. If the user asks about API/programming differences, also reference the `ni-hw-drivers-csharp` skill for code patterns

## Data Sources

All specifications are extracted from official NI specification documents (PDF):
- PXIe-5841 Specifications (377850C-01, March 2026)
- PXIe-5842 Specifications
- PXIe-5860 Specifications (379054E-01, May 2026)
- PXIe-5831 Specifications
