import requests
import json
from google.colab import userdata
from tavily import TavilyClient

# ============================================================
# 1. CHARGEMENT DES CLÉS
# ============================================================

OPENROUTER_API_KEY = userdata.get("OPENROUTER_API_KEY")
TAVILY_API_KEY = userdata.get("TAVILY_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY introuvable")

if not TAVILY_API_KEY:
    raise ValueError("❌ TAVILY_API_KEY introuvable")


# ============================================================
# 2. CONFIGURATION
# ============================================================

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openrouter/free"


# ============================================================
# 3. CLIENT TAVILY
# ============================================================

tavily_client = TavilyClient(
    api_key=TAVILY_API_KEY
)


# ============================================================
# 4. FONCTION TAVILY SEARCH
# ============================================================

def tavily_search_tool(
    query: str,
    search_depth: str = "advanced"
):
    """
    Recherche des informations actuelles avec Tavily.
    """

    try:
        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=5,
            include_answer=True
        )

        sources = []

        for result in response.get("results", []):
            sources.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")
            })

        return {
            "answer": response.get("answer", ""),
            "sources": sources
        }

    except Exception as e:
        return {
            "error": str(e),
            "answer": "",
            "sources": []
        }


# ============================================================
# 5. OUTIL DONNÉ AU LLM
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search_tool",
            "description": (
                "Recherche des informations récentes, actuelles "
                "ou vérifiables sur Internet avec Tavily."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "La recherche à effectuer sur Internet."
                        )
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": [
                            "basic",
                            "advanced"
                        ],
                        "description": (
                            "Niveau de profondeur de la recherche."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# ============================================================
# 6. APPEL OPENROUTER
# ============================================================

def openrouter_chat(
    messages,
    tools=None,
    tool_choice="auto"
):
    """
    Appelle OpenRouter directement avec requests.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Personal AI Hackathon"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages
    }

    if tools is not None:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter HTTP {response.status_code}: "
            f"{response.text}"
        )

    return response.json()


# ============================================================
# 7. PROMPT SYSTÈME
# ============================================================

SYSTEM_PROMPT = """
Tu es un Personal AI Assistant.

Tu réponds directement lorsque tu connais la réponse.

Utilise Tavily lorsque :
- l'utilisateur demande des informations récentes ;
- l'information peut avoir changé ;
- l'utilisateur demande une vérification sur Internet ;
- une recherche web est nécessaire.

Lorsque Tavily est utilisé :
- base ta réponse sur les résultats obtenus ;
- ne prétends jamais avoir vérifié quelque chose que tu n'as pas recherché ;
- utilise les sources fournies par Tavily pour construire ta réponse.
"""


# ============================================================
# 8. AGENT
# ============================================================

def run_agent(user_prompt: str):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    print("🧠 Question :", user_prompt)
    print("-" * 70)

    # --------------------------------------------------------
    # PREMIER APPEL AU LLM
    # --------------------------------------------------------

    response = openrouter_chat(
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response["choices"][0]["message"]

    # --------------------------------------------------------
    # LE LLM NE DEMANDE AUCUN OUTIL
    # --------------------------------------------------------

    if not message.get("tool_calls"):

        return message.get(
            "content",
            ""
        )

    # --------------------------------------------------------
    # LE LLM DEMANDE UN OUTIL
    # --------------------------------------------------------

    messages.append(message)

    for tool_call in message["tool_calls"]:

        function_name = tool_call["function"]["name"]

        try:
            arguments = json.loads(
                tool_call["function"]["arguments"]
            )
        except json.JSONDecodeError:
            arguments = {}

        print("🔧 Outil demandé :", function_name)
        print("📋 Arguments :", arguments)

        # ----------------------------------------------------
        # EXÉCUTION TAVILY
        # ----------------------------------------------------

        if function_name == "tavily_search_tool":

            result = tavily_search_tool(
                **arguments
            )

            print("✅ Tavily exécuté")

        else:

            result = {
                "error": (
                    f"Outil inconnu : {function_name}"
                )
            }

        # ----------------------------------------------------
        # RENVOI DU RÉSULTAT AU LLM
        # ----------------------------------------------------

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": json.dumps(
                result,
                ensure_ascii=False
            )
        })

    # --------------------------------------------------------
    # DEUXIÈME APPEL : LE LLM ANALYSE TAVILY
    # --------------------------------------------------------

    final_response = openrouter_chat(
        messages=messages
    )

    return final_response["choices"][0]["message"].get(
        "content",
        ""
    )


# ============================================================
# 9. TEST
# ============================================================

print("✅ Agent chargé avec succès")
print("✅ OpenRouter :", MODEL_NAME)
print("✅ Tavily connecté")
print("✅ Tool calling prêt")

answer = run_agent(
    "Les dix meilleurs ordinateurs  en 2026 ?"
)

print("\n🤖 RÉPONSE FINALE :")
print(answer)
