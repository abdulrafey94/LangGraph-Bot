from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from api.schema import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": str(body.thread_id)}}
    result = await graph.ainvoke(
        {"messages": HumanMessage(content=body.message)},
        config=config
    )
    
    agent_response = result["messages"][-1].content
    api_response = ChatResponse(
        thread_id=body.thread_id, 
        reply=agent_response
    )
    return api_response
