import os
import json
from tavily import TavilyClient

# Initialisation du client Tavily
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

def execute_tavily_search(query: str) -> str:
    """Exécute une recherche web via l'API Tavily."""
    if not tavily_client:
        return "Erreur: Clé TAVILY_API_KEY non configurée."
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
        output.append("Résultats web :")
        for res in search_result.get("results", []):
            output.append(f"- [{res['title']}]({res['url']}): {res['content']}")
        return "\n".join(output)
    except Exception as e:
        return f"Erreur lors de la recherche : {str(e)}"

def run_react_loop(user_prompt: str):
    """Boucle agentique ReAct (Reasoning + Acting)."""
    print(f"\n🤖 Utilisateur : {user_prompt}")
    print("=" * 60)
    
    # Thought
    print("\n🧠 [THOUGHT] L'agent identifie le besoin d'effectuer une recherche web.")
    
    # Action
    print(f"\n🔍 [ACTION] Lancement de la recherche via Tavily: '{user_prompt}'")
    observation = execute_tavily_search(user_prompt)
    
    # Observation
    print("\n👁️ [OBSERVATION] Données récupérées avec succès.")
    
    # Final Answer
    print("\n✅ [FINAL ANSWER] Résultat synthétisé par l'agent :")
    print(observation)

if __name__ == "__main__":
    prompt = "NVIDIA Rubin GPU features 2026"
    run_react_loop(prompt)
