import os
import json
from tavily import TavilyClient
from openai import OpenAI

# 1. Configuration des clés API
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

def get_llm_client():
    """Initialise le client LLM avec fallback dynamique (Nebius ou OpenRouter)."""
    if NEBIUS_API_KEY:
        print("🚀 Backend LLM : Nebius Token Factory (NVIDIA Nemotron)")
        return OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=NEBIUS_API_KEY
        ), "nvidia/nemotron-4-340b-instruct"
    else:
        print("🔄 Backend LLM : OpenRouter (Fallback)")
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        ), "openrouter/free"

def execute_tavily_search(query: str) -> str:
    """Exécute une recherche web temps réel via l'API Tavily."""
    if not tavily_client:
        return "Erreur : TAVILY_API_KEY non configurée."
    try:
        search_result = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=3,
            include_answer=True
        )
        output = []
        if search_result.get("answer"):
            output.append(f"Synthèse Tavily : {search_result['answer']}\n")
        output.append("Résultats détaillés :")
        for res in search_result.get("results", []):
            output.append(f"- [{res['title']}]({res['url']}): {res['content']}")
        return "\n".join(output)
    except Exception as e:
        return f"Erreur lors de la recherche Tavily : {str(e)}"

# Définition du schéma d'outil au format OpenAI Function Calling
tools_schema = [{
    "type": "function",
    "function": {
        "name": "execute_tavily_search",
        "description": "Recherche sur le web en temps réel les faits récents, actualités ou données précises.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La requête de recherche optimisée pour Tavily."
                }
            },
            "required": ["query"]
        }
    }
}]

def run_react_agent(user_prompt: str):
    """Boucle agentique autonome ReAct (Thought -> Action -> Observe -> Final Answer)."""
    client, model_name = get_llm_client()
    
    print(f"\n🤖 Question utilisateur : {user_prompt}")
    print("=" * 60)

    messages = [
        {
            "role": "system", 
            "content": "Tu es un assistant IA autonome. Utilise l'outil `execute_tavily_search` dès qu'une information en temps réel est nécessaire."
        },
        {"role": "user", "content": user_prompt}
    ]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        search_query = args.get("query")

        print(f"\n🧠 [THOUGHT] Recherche web requise.")
        print(f"🔍 [ACTION] Recherche Tavily : '{search_query}'")

        observation = execute_tavily_search(search_query)
        print("\n👁️ [OBSERVATION] Données web récupérées avec succès.")

        messages.append(response_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": observation
        })

        final_response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )

        print("\n✅ [FINAL ANSWER] :")
        print(final_response.choices[0].message.content)
    else:
        print("\n✅ [FINAL ANSWER] (Sans recherche web) :")
        print(response_message.content)

if __name__ == "__main__":
    run_react_agent("Quelles sont les dernières fonctionnalités annoncées pour NVIDIA Rubin en 2026 ?")
