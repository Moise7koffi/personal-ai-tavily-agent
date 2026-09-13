# Personal AI Agent — ReAct Loop with Tavily & NVIDIA Models

An autonomous Personal AI Agent built for the **Nebius x NVIDIA Global AI Hackathon** (Targeting: *Best Use of Tavily*).

## 🌟 Key Features
- **ReAct Architecture**: Implements Reason + Act decision-making cycles.
- **Real-Time Web Search**: Powered by **Tavily Search API** for accurate, up-to-date context retrieval.
- **LLM Integration**: Built to interface with NVIDIA Nemotron models hosted on Nebius Token Factory.

## 📁 Project Structure
- `agent.py`: Main ReAct agent loop and Tavily search integration.
- `.env.example`: Template for environment variables.
- `requirements.txt`: Project dependencies.

## 🚀 Quick Start
1. Clone the repository:
   ```bash
   git clone [https://github.com/VOTRE_PSEUDO/personal-ai-tavily-agent.git](https://github.com/VOTRE_PSEUDO/personal-ai-tavily-agent.git)
   cd personal-ai-tavily-agent

## 🔌 LLM Providers & Compatibility

This agent is designed with a multi-provider fallback architecture:
- **Primary / Native Target**: NVIDIA Nemotron models hosted on **Nebius Token Factory**.
- **Fallback / Multi-Region Support**: Compatible with OpenAI-standard APIs (e.g., OpenRouter) to guarantee uninterrupted agentic operation across all geographic regions.
