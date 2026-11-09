from langchain_core.prompts import ChatPromptTemplate

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en marketing."),
    ("user", "{text_human}")
])

list_message = chat_prompt.format_messages(text_human="Sugiere un eslogan creativo para el producto: café organico")

for m in list_message:
    print(f"{type(m)}: {m.content}")