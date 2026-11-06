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
    
import os
import sys

from langchain_github_copilot import ChatGitHubCopilot
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
import streamlit as st

st.set_page_config(page_title="Chat bot basico", page_icon="🤖")
st.title("Chat bot basico")
st.markdown("Este es un chat bot basico usando LangChain y GitHub Copilot")

try:
    # Get token
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        token = get_github_token()
    
    print(f"\n[INIT] Inicializando ChatGitHubCopilot...")
    chat = ChatGitHubCopilot(github_token=token)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)