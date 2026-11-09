from langchain_core.runnables import RunnableLambda

step1  = RunnableLambda(lambda x: f" Numero {x}")

def duplicar_texto(text):
    return [text] * 2

step2 = RunnableLambda(duplicar_texto)

chain = step1 | step2

# Ejecutar la cadena con un valor de ejemplo
resultado = chain.invoke(5)
print(resultado)