from typing import TypedDict, Annotated

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage


llm = ChatOllama(model="llama3.2")
# query
response = llm.invoke("Explain large language models in one sentence")
print(response)

class State(TypedDict):
    message: Annotated[list,add_messages]

def chatbot(state: State):
    return {"message": llm.invoke(state["message"])}


builder = StateGraph(State)
builder.add_node("chatbot_node", chatbot)
builder.add_edge(START,"chatbot_node")
builder.add_edge("chatbot_node",END)

graph = builder.compile()
print(graph)

from IPython.display import Image,display

display(Image(graph.get_graph().draw_mermaid_png()))

png_data = graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(png_data)

print("Graph saved as graph.png")

message = {
    "message": [
        HumanMessage(
            content="Explain large language models in one sentence"
        )
    ]
}
response = graph.invoke(message)
print(response)

state = None

while True:
    in_message = input("You: ")
    if in_message.lower() == "exit":
        break
    if state is None:
        state = {
            "message": [
                HumanMessage(content=in_message)
            ]
        }
    else:
        state["message"].append(
            HumanMessage(content=in_message)
        )
    response = graph.invoke(state)
    print("AI:", response["message"][-1].content)
    state = response