import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# Chargement des variables d'environnement (.env)
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not TAVILY_API_KEY or not OPENROUTER_API_KEY:
    raise ValueError("⚠️ Les clés TAVILY_API_KEY et OPENROUTER_API_KEY doivent être définies.")

# Initialisation des clients
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://github.com",
        "X-Title": "Tavily ReAct Agent",
    }
)

def execute_tavily_search(query: str) -> str:
    """Exécute une recherche web en temps réel via l'API Tavily."""
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

# Schéma Function Calling pour OpenAI Spec
tools = [{
    "type": "function",
    "function": {
        "name": "execute_tavily_search",
        "description": "Recherche sur le web en temps réel pour obtenir des faits récents ou informations externes.",
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
    """Exécute la boucle agentique ReAct (Thought -> Action -> Observe -> Final Answer)."""
    print(f"\n🤖 Question : {user_prompt}")
    print("=" * 60)

    messages = [
        {
            "role": "system", 
            "content": "Tu es un agent IA autonome. Utilise impérativement `execute_tavily_search` dès qu'une information en temps réel est nécessaire."
        },
        {"role": "user", "content": user_prompt}
    ]

    MODEL_NAME = "openrouter/free"

    # Thought -> Action
    response = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        search_query = args.get("query")

        print(f"\n🧠 [THOUGHT] Besoin d'information en temps réel.")
        print(f"🔍 [ACTION] Lancement Tavily Search : '{search_query}'")

        # Observation
        observation = execute_tavily_search(search_query)
        print("\n👁️ [OBSERVATION] Données de Tavily récupérées.")

        messages.append(response_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": observation
        })

        # Final Answer
        final_response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )

        print("\n✅ [FINAL ANSWER] :")
        print(final_response.choices[0].message.content)
    else:
        print("\n✅ [FINAL ANSWER] (Réponse directe) :")
        print(response_message.content)

if __name__ == "__main__":
    run_react_agent("Quelles sont les dernières fonctionnalités annoncées pour NVIDIA Rubin en 2026 ?")
