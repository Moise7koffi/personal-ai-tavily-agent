# 🤖 Autonomous ReAct Agent – Nebius x NVIDIA Global AI Hackathon

> **Submission for Category**: Best Use of Tavily

An autonomous Reasoning and Action (ReAct) AI agent built to deliver accurate, real-time, and ground-truth web insights using the **Tavily Search API** combined with an OpenAI-compatible multi-provider LLM infrastructure.

---

## 🌟 Key Features

* **ReAct Architecture**: Implements the full **Thought ➔ Action ➔ Observation ➔ Final Answer** decision-making loop for multi-step reasoning.
* **Powered by Tavily Search API**: Uses Tavily's advanced search depth and automated synthesis to extract up-to-date facts without context degradation.
* **Agnostic & Production-Ready**: Built on an OpenAI-compatible interface, allowing seamless model switching (OpenRouter, Nebius AI Studio, or local endpoints).
* **Robust Tool Calling**: Integrates structured JSON Function Calling to handle search requests deterministically.

---

## 🔄 ReAct Workflow

```text
                 PERSONAL AI
                      │
             ┌────────┴────────┐
             ↓                 ↓
       Tavily Search      Tavily Extract
             │                 │
       trouver les infos   lire les sources
             └────────┬────────┘
                      ↓
                    LLM
                      ↓
               réponse finale
