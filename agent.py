
import requests
import json
from google.colab import userdata
from tavily import TavilyClient


OPENROUTER_API_KEY = userdata.get("OPENROUTER_API_KEY")
TAVILY_API_KEY = userdata.get("TAVILY_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError(
        " OPENROUTER_API_KEY est introuvable dans Colab Secrets."
    )

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY est introuvable dans Colab Secrets."
    )

print(" OPENROUTER_API_KEY chargée")
print(" TAVILY_API_KEY chargée")




OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

MODEL_NAME = "openrouter/free"

print(" OpenRouter :", OPENROUTER_URL)
print(" Modèle :", MODEL_NAME)


tavily_client = TavilyClient(
    api_key=TAVILY_API_KEY
)

print(" Client Tavily initialisé")



used_sources = []


def register_source(title, url):
    """
    Ajoute une source au registre sans doublon.
    """

    if not url:
        return

    for source in used_sources:
        if source["url"] == url:
            return

    used_sources.append({
        "title": title or "Source sans titre",
        "url": url
    })

def tavily_search_tool(
    query: str,
    search_depth: str = "advanced"
):
    """
    Recherche des informations sur Internet avec Tavily.
    """

    try:

        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=5,
            include_answer=True,
            include_raw_content=False
        )

        sources = []


        answer = response.get("answer", "")


        for result in response.get("results", []):

            title = result.get(
                "title",
                "Source sans titre"
            )

            url = result.get(
                "url",
                ""
            )

            content = result.get(
                "content",
                ""
            )


            register_source(
                title,
                url
            )

            sources.append({
                "title": title,
                "url": url,
                "content": content[:3000]
            })

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:

        return {
            "error": str(e),
            "answer": "",
            "sources": []
        }



def tavily_extract_tool(urls: list):
    """
    Extrait le contenu détaillé de pages web
    avec Tavily Extract.
    """

    if not urls:

        return {
            "error": "Aucune URL fournie.",
            "results": []
        }

    try:

        response = tavily_client.extract(
            urls=urls
        )

        results = []

        for result in response.get(
            "results",
            []
        ):

            url = result.get(
                "url",
                ""
            )

            raw_content = result.get(
                "raw_content",
                ""
            )


            register_source(
                "Page extraite",
                url
            )

            results.append({
                "url": url,
                "raw_content": raw_content[:6000]
            })

        return {
            "results": results
        }

    except Exception as e:

        return {
            "error": str(e),
            "results": []
        }



print("\n Test de Tavily...")

test_tavily = tavily_search_tool(
    "NVIDIA Rubin latest news 2026"
)

if "error" in test_tavily:

    print(
        " Erreur Tavily :",
        test_tavily["error"]
    )

else:

    print("Tavily Search fonctionne")

    print(
        "\n Synthèse :"
    )

    print(
        test_tavily["answer"]
    )

    print(
        "\n Sources trouvées :"
    )

    for source in test_tavily["sources"]:

        print(
            "-",
            source["title"]
        )

        print(
            " ",
            source["url"]
        )




tools = [


    {
        "type": "function",
        "function": {

            "name": "tavily_search_tool",

            "description": (
                "Recherche des informations récentes, "
                "actuelles ou vérifiables sur Internet "
                "avec Tavily."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "query": {
                        "type": "string",
                        "description": (
                            "La recherche à effectuer "
                            "sur Internet."
                        )
                    },

                    "search_depth": {
                        "type": "string",
                        "enum": [
                            "basic",
                            "advanced"
                        ],
                        "description": (
                            "Niveau de profondeur "
                            "de la recherche."
                        )
                    }

                },

                "required": [
                    "query"
                ]
            }
        }
    },



    {
        "type": "function",
        "function": {

            "name": "tavily_extract_tool",

            "description": (
                "Extrait et lit en profondeur le contenu "
                "d'une ou plusieurs pages web précises. "
                "Utilise cet outil lorsqu'une source trouvée "
                "par Tavily Search doit être analysée "
                "plus en détail."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "urls": {

                        "type": "array",

                        "items": {
                            "type": "string"
                        },

                        "description": (
                            "Liste des URLs à analyser."
                        )
                    }

                },

                "required": [
                    "urls"
                ]
            }
        }
    }

]

print("\n Search + Extract déclarés comme outils")



SYSTEM_PROMPT = """
You are a Personal AI Assistant designed for a hackathon.

You have access to two web tools:

1. tavily_search_tool
   Use this tool to search the web for current,
   recent, changing, or verifiable information.

2. tavily_extract_tool
   Use this tool to deeply inspect specific web pages
   discovered through Tavily Search.

Rules:

- Do not use web search when it is unnecessary.
- Use Tavily Search for current or externally verifiable information.
- When the research is complex, perform multiple searches if necessary.
- After searching, identify the most relevant sources.
- When a source needs deeper inspection, use Tavily Extract.
- You may use Search and Extract multiple times.
- Do not claim to have read a web page unless Tavily Extract
  actually returned its content.
- Base factual claims about current information on the research.
- Be transparent about uncertainty.
- Give a clear and useful final answer.
- Do not output XML-style <tool_call> tags as normal text.
"""



def openrouter_chat(
    messages,
    tools=None,
    tool_choice="auto"
):
    """
    Appelle directement l'API OpenRouter
    avec requests.
    """

    headers = {

        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),

        "Content-Type": (
            "application/json"
        ),

        "HTTP-Referer": (
            "https://github.com"
        ),

        "X-Title": (
            "Personal AI Hackathon"
        )
    }

    payload = {

        "model": MODEL_NAME,

        "messages": messages
    }


    if tools is not None:

        payload["tools"] = tools

        payload["tool_choice"] = tool_choice

        payload["parallel_tool_calls"] = False

    response = requests.post(

        OPENROUTER_URL,

        headers=headers,

        json=payload,

        timeout=120
    )

    if response.status_code != 200:

        raise RuntimeError(
            "OpenRouter HTTP "
            + str(response.status_code)
            + ": "
            + response.text
        )

    return response.json()



print("\n Test OpenRouter...")

test_llm = openrouter_chat(
    messages=[
        {
            "role": "user",
            "content": (
                "Réponds exactement : "
                "connexion réussie."
            )
        }
    ]
)

print(
    "Réponse :",
    test_llm["choices"][0]["message"]["content"]
)


def execute_tool(
    function_name,
    arguments,
    fallback_urls=None
):
    """
    Exécute un outil et récupère automatiquement
    les URLs du dernier Search si Extract reçoit
    des arguments invalides.
    """



    if function_name == "tavily_search_tool":

        result = tavily_search_tool(
            **arguments
        )

        return result




    elif function_name == "tavily_extract_tool":


        urls = arguments.get("urls")


        if (
            not isinstance(urls, list)
            or not urls
        ):

            if fallback_urls:
                urls = fallback_urls[:3]

                print(
                    " Arguments Extract invalides."
                )

                print(
                    " Utilisation automatique "
                    "des URLs du dernier Search :",
                    urls
                )

            else:

                return {
                    "error": (
                        "Aucune URL valide disponible "
                        "pour Tavily Extract."
                    )
                }

        result = tavily_extract_tool(
            urls=urls
        )

        return result



    else:

        return {
            "error": (
                f"Outil inconnu : {function_name}"
            )
        }


def run_agent(
    user_prompt: str,
    max_iterations: int = 8
):
    """
    Agent Personal AI robuste :

    LLM
      ↓
    Search
      ↓
    Extract
      ↓
    LLM
      ↓
    réponse finale
    """



    used_sources.clear()


    last_search_urls = []


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


    print(
        "\n🧠 Question :",
        user_prompt
    )

    print("=" * 70)

    for iteration in range(
        1,
        max_iterations + 1
    ):

        print(
            f"\n Tour agent : {iteration}"
        )



        response = openrouter_chat(
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )


        message = response[
            "choices"
        ][0][
            "message"
        ]



        if not message.get("tool_calls"):

            final_answer = (
                message.get(
                    "content",
                    ""
                )
                or ""
             )
            if used_sources:

                final_answer += (
                    "\n\n"
                    "### Sources utilisées\n"
                )

                for index, source in enumerate(
                    used_sources,
                    start=1
                ):

                    final_answer += (
                        f"{index}. "
                        f"{source['title']}\n"
                        f"   {source['url']}\n"
                    )


            return final_answer


        tool_calls = message.get(
            "tool_calls",
            []
        )

        print(
            "🔧 Nombre d'outils demandés :",
            len(tool_calls)
        )



        messages.append(
            message
        )


        for tool_call in tool_calls:

            function_name = (
                tool_call[
                    "function"
                ][
                    "name"
                ]
            )


            raw_arguments = (
                tool_call[
                    "function"
                ][
                    "arguments"
                ]
            )


            try:

                arguments = json.loads(
                    raw_arguments
                )

                json_valid = True

            except Exception:

                print(
                    " Arguments JSON invalides."
                )

                arguments = {}

                json_valid = False


            print(
                "\n🔧 Outil :",
                function_name
            )


            print(
                " Arguments :",
                arguments
            )




            if function_name == (
                "tavily_search_tool"
            ):

                result = execute_tool(
                    function_name,
                    arguments
                )

                print(
                    " Tavily Search exécuté"
                )



                if isinstance(
                    result,
                    dict
                ):

                    sources = result.get(
                        "sources",
                        []
                    )

                    last_search_urls = [

                        source.get("url")

                        for source in sources

                        if source.get("url")
                    ]


                    print(
                        " URLs disponibles :",
                        len(last_search_urls)
                    )



            elif function_name == (
                "tavily_extract_tool"
            ):


                if (
                    not json_valid
                    or not arguments.get("urls")
                ):

                    arguments = {
                        "urls": last_search_urls[:3]
                    }


                result = execute_tool(
                    function_name,
                    arguments,
                    fallback_urls=last_search_urls
                )


                print(
                    " Tavily Extract exécuté"
                )



            else:

                result = {
                    "error": (
                        f"Outil inconnu : "
                        f"{function_name}"
                    )
                }



            messages.append({

                "role": "tool",

                "tool_call_id": (
                    tool_call["id"]
                ),

                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            })


    return (
        " L'agent a atteint la limite "
        "d'itérations sans produire "
        "de réponse finale."
    )



print("\n" + "=" * 70)
print(" PERSONAL AI CHARGÉ")
print("=" * 70)

print(" OpenRouter")
print("LLM")
print(" Tavily Search")
print(" Tavily Extract")
print(" Tool Calling")
print(" Multi-step Agent")
print(" Registre des sources")
