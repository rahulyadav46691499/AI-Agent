import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from graph import app_graph
import uuid

app = FastAPI(title="Smart Travel Companion API")

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    active_service: str | None
    flight_context: dict
    hotel_context: dict

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    
    inputs = {"messages": [HumanMessage(content=request.message)]}
    
    # Stream events through LangGraph
    for event in app_graph.stream(inputs, config=config, stream_mode="values"):
        pass

    final_state = app_graph.get_state(config)
    state_values = final_state.values
    
    messages = state_values.get("messages", [])
    if not messages:
        return ChatResponse(response="No response", active_service=None, flight_context={}, hotel_context={})
    
    # Get the latest message (which should be an AIMessage)
    latest_message_obj = messages[-1]
    if isinstance(latest_message_obj, AIMessage):
        latest_message = latest_message_obj.content
    else:
        # Fallback to looking for the last AIMessage
        aimessages = [m for m in messages if isinstance(m, AIMessage)]
        latest_message = aimessages[-1].content if aimessages else "I'm sorry, I couldn't process that request."
    
    return ChatResponse(
        response=latest_message,
        active_service=state_values.get("active_service"),
        flight_context=state_values.get("flight_context", {}).model_dump() if hasattr(state_values.get("flight_context"), "model_dump") else {},
        hotel_context=state_values.get("hotel_context", {}).model_dump() if hasattr(state_values.get("hotel_context"), "model_dump") else {}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
