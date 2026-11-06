import os
import sys
import subprocess
import urllib3
from urllib3.exceptions import InsecureRequestWarning

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

from langchain_github_copilot import ChatGitHubCopilot
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

try:
    # Get token
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        token = get_github_token()
    
    print(f"\n[INIT] Inicializando ChatGitHubCopilot...")
    chat = ChatGitHubCopilot(github_token=token)
    
    print("[CHAT] Enviando mensaje...")
    plantilla = PromptTemplate(
        input_variables=["nombre"],
        template="Hola, {nombre}"
    )
    chain =plantilla | chat
    response = chat.invoke([HumanMessage(content="nombre: Angel")])
    print("\n[OK] Respuesta recibida:")
    print("-" * 50)
    # Encode response to handle unicode properly
    output = response.content.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print(output)
    print("-" * 50)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)