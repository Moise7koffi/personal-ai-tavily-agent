import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# Prise en charge des Secrets Colab + fichier .env local
try:
    from google.colab import userdata
    TAVILY_API_KEY = userdata.get('TAVILY_API_KEY')
    OPENROUTER_API_KEY = userdata.get('OPENROUTER_API_KEY')
    try:
        NEBIUS_API_KEY = userdata.get('NEBIUS_API_KEY')
    except:
        NEBIUS_API_KEY = None
except ImportError:
    load_dotenv()
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("⚠️ La clé TAVILY_API_KEY est obligatoire.")

# 2. Client LLM (Compatible OpenRouter & Nebius Token Factory)
# Si NEBIUS_API_KEY est présent, on utilise Nebius Studio, sinon OpenRouter par défaut.
if NEBIUS_API_KEY:
    BASE_URL = "https://api.studio.nebius.ai/v1"
    API_KEY = NEBIUS_API_KEY
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-70B-Instruct"
    print("⚡ Mode actif : Nebius Token Factory")
else:
    BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY = OPENROUTER_API_KEY
    MODEL_NAME = "openrouter/free"
    print("🌐 Mode actif : OpenRouter Free Routing")

llm_client = OpenAI(
    base_url=BASE_URL,
api_key=API_KEY,
    default_headers={
        "HTTP-Referer": "https://github.com",
        "X-Title": "Tavily Advanced ReAct Agent",
    }
)

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# 3. Outils Avancés Tavily
def tavily_search_tool(query: str, search_depth: str = "advanced") -> str:
    """Effectue une recherche web approfondie via Tavily Search API."""
    try:
        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=5,
            include_answer=True
        )
        output = []
        if response.get("answer"):
            output.append(f"📌 SYNTHÈSE TAVILY : {response['answer']}\n")
        
        output.append("🔗 RÉSULTATS DÉTAILLÉS :")
        for res in response.get("results", []):
            output.append(f"- [{res['title']}]({res['url']}): {res['content']}")
        return "\n".join(output)
    except Exception as e:
        return f"Erreur Recherche Tavily : {str(e)}"

def tavily_extract_tool(urls: list) -> str:
    """Extrait le contenu complet d'une ou plusieurs URLs via Tavily Extract API."""
    try:
        response = tavily_client.extract(urls=urls)
        results = []
        for res in response.get("results", []):
            results.append(f"📄 CONTENU DE {res['url']} :\n{res['raw_content'][:1000]}...")
        return "\n\n".join(results)
    except Exception as e:
        return f"Erreur Extraction Tavily : {str(e)}"

# 4. Schémas des outils Function Calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search_tool",
            "description": "Effectue une recherche web en temps réel pour obtenir des faits récents, actualités ou données précises.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "La requête de recherche optimisée."},
                    "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "advanced"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tavily_extract_tool",
            "description": "Extrait et lit le contenu complet d'une ou plusieurs URLs spécifiques quand une recherche synthétique ne suffit pas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste des URLs à analyser."
                    }
                },
                "required": ["urls"]
            }
        }
    }
]

# 5. Boucle ReAct Autonome Multi-Hop
def run_react_agent(user_prompt: str, max_iterations: int = 4):
    print(f"\n🤖 Question utilisateur : {user_prompt}")
    print("=" * 70)

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un agent ReAct autonome hautement intelligent. Utilise `tavily_search_tool` "
                "pour rechercher des informations web récentes et `tavily_extract_tool` si tu as besoin "
                "d'analyser le contenu complet d'une page web précise."
            )
        },
        {"role": "user", "content": user_prompt}
    ]

    for iteration in range(1, max_iterations + 1):
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                print(f"\n🧠 [THOUGHT - Étape {iteration}]: Analyse requise.")
                print(f"🔍 [ACTION]: Exécution de `{fn_name}` avec : {fn_args}")

                if fn_name == "tavily_search_tool":
                    observation = tavily_search_tool(**fn_args)
                elif fn_name == "tavily_extract_tool":
                    observation = tavily_extract_tool(**fn_args)
                else:
                    observation = "Outil inconnu."

                print(f"👁️ [OBSERVATION]: Données récupérées via Tavily API.")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation
                })
        else:
            print("\n✅ [FINAL ANSWER] :")
            print(response_message.content)
            return

    print("\n⚠️ Limite d'itérations atteinte.")

if __name__ == "__main__":
    run_react_agent("Quelles sont les dernières fonctionnalités annoncées pour NVIDIA Rubin en 2026 ?")
