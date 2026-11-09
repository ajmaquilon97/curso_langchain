from langchain_core.prompts import PromptTemplate

template = "Eres un experto en marketing. Sugiere un eslogan creativo para el producto: {producto}"

prompt = PromptTemplate(
    template=template, 
    input_variables=["producto"]
    )

prompt_complete = prompt.format(producto="Café organico")
print(prompt_complete)
