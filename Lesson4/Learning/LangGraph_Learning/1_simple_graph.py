from typing import TypedDict

class Portfolio(TypedDict):
    amount_usd: float
    total_usd : float
    total_inr: float

my_obj : Portfolio={
    "amount_usd": 100,
    "total_usd": 100,
    "total_inr": 34,
}

def calc_total(state : Portfolio) -> Portfolio:
    state["total_usd"] = state["amount_usd"] * 1.08
    return state

def convert_to_inr(state : Portfolio) -> Portfolio:
    state["total_inr"] = state["total_usd"] * 85
    return state

from langgraph.graph import StateGraph,START,END
builder = StateGraph(Portfolio)
builder.add_node("calc_total_node",calc_total)
builder.add_node("convert_to_inr_node",convert_to_inr)

builder.add_edge(START,"calc_total_node")
builder.add_edge("calc_total_node","convert_to_inr_node")
builder.add_edge("convert_to_inr_node",END)

graph = builder.compile()
print(graph)

from IPython.display import Image,display

display(Image(graph.get_graph().draw_mermaid_png()))

png_data = graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(png_data)

print("Graph saved as graph.png")

result = graph.invoke({"amount_usd": 1000})
print(result)