import os
import sys
import subprocess
from langchain_github_copilot import ChatGitHubCopilot
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from langchain_core.runnables import RunnableLambda, RunnableParallel


# Force UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# Disable all SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

# Set environment variables
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['PYTHONWARNINGS'] = 'ignore'

# Patch requests BEFORE importing langchain
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = 0  # ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

# Patch the default session
session = requests.Session()
session.mount('https://', SSLAdapter())


# Monkey patch requests.post to use our patched session
def patched_post(*args, **kwargs):
    kwargs['verify'] = False
    return session.post(*args, **kwargs)

requests.post = patched_post
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_github_token():
    """Get GitHub token from gh CLI"""
    try:
        # Try to get token from existing gh CLI authentication
        result = subprocess.run(
            ['gh', 'auth', 'token'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                print("[OK] Token obtenido de gh CLI")
                return token
    except FileNotFoundError:
        print("[ERROR] 'gh' CLI no encontrada")
        print("[INFO] Instalalo en: https://cli.github.com/")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error obteniendo token: {e}")
    
    print("\n[AUTH] No hay sesion de GitHub activa")
    print("[INFO] Ejecuta primero: gh auth login")
    print("[INFO] Te abrira el navegador para autenticarte")
    sys.exit(1)


def limpiar_texto(texto):
    """Limpia el texto eliminando espacios extras y limitando longitud"""
    return texto.strip()[:500]


try:
    # Get token
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        token = get_github_token()
        
    chat = ChatGitHubCopilot(github_token=token, model="gpt-4")
    # Primer runnable limpiar texto
    preprocessor = RunnableLambda(limpiar_texto)

    def generate_summary(text):
        """Genera un resumen conciso del texto"""
        prompt = f"Resume en una sola oración: {text}"
        response = chat.invoke(prompt)
        return response.content
    
    summary_brach = RunnableLambda(generate_summary)

    def analyze_sentiment(text):
        """Analiza el sentimiento y devuelve resultado estructurado"""
        prompt = f"""Analiza el sentimiento del siguiente texto.
        Responde ÚNICAMENTE en formato JSON válido:
        {{"sentimiento": "positivo|negativo|neutro", "razon": "justificación breve"}}
        
        Texto: {text}"""
        # Aquí podrías usar el chat de GitHub Copilot para procesar el prompt
        response = chat.invoke(prompt)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"sentimiento": "neutro", "razon": "Error en análisis"}

    sentiment_branch = RunnableLambda(analyze_sentiment)

    def merge_results(data):
        """Combina los resultados de ambas ramas en un formato unificado"""
        return {
            "resumen": data["resumen"],
            "sentimiento": data["sentimiento_data"]["sentimiento"],
            "razon": data["sentimiento_data"]["razon"]
        }

    merger = RunnableLambda(merge_results)

    parallel_analysis = RunnableParallel({
        "resumen": summary_brach,
        "sentimiento_data": sentiment_branch
    })
    
    # Convertir en Runnable


    cadena = preprocessor | parallel_analysis | merger

    # Prueba con diferentes textos
    textos_prueba = [
        "¡Me encanta este producto! Funciona perfectamente y llegó muy rápido.",
        "El servicio al cliente fue terrible, nadie me ayudó con mi problema.",
        "El clima está nublado hoy, probablemente llueva más tarde."
    ]

    resultado_batch = cadena.batch(textos_prueba)

    print(resultado_batch)

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)