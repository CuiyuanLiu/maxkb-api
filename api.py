from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from starlette.exceptions import HTTPException as StarletteHTTPException
import aiohttp
import json
import time
import uuid
import asyncio

from kbinfo import max_db_info, RequestMaxKB
from paras  import MaxKBParas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

# Please update your parameters here.
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 1.0
    top_p: float = 1.0
    stream: bool = False
    max_tokens: Optional[int] = 512
    stop: Optional[List[str]] = None    
    
class MaxKBProxy:
    @staticmethod
    def format_messages(messages: List[Message]) -> str:
        """Convert OpenAI-style message list to a single prompt string"""
        return "\n".join([f"{msg.role}: {msg.content}" for msg in messages])

    @staticmethod
    async def call_maxkb(formatted_prompt: str, chat_id: str) -> str:
        """Call MaxKB and get the assistant's reply"""
        req = RequestMaxKB(message=formatted_prompt, re_chat=False, stream=False)
        response = await max_db_info.get_textResponse(
            input_url=MaxKBParas.input_url,
            application_id=MaxKBParas.application_id,
            request=req
        )
        return response["content"]

    @staticmethod
    async def stream_maxkb_chunks(formatted_prompt: str, model_id: str, chat_id: str):
        """Simulate streaming chunks from a full MaxKB response"""
        request = RequestMaxKB(message=formatted_prompt, re_chat=False, stream=True)
        application_id = MaxKBParas.application_id
        input_url = MaxKBParas.input_url
        url = f"{input_url}/chat_message/{chat_id}"
        headers = {
            "accept": "application/json",
            "AUTHORIZATION": max_db_info.APIKEY,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=request.dict()) as resp:
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue

                    try:
                        json_data = json.loads(line[6:])  
                        content = json_data.get("content", "")
                        is_end = json_data.get("is_end", False)

                        if content:
                            chunk = {
                                'id': str(uuid.uuid4()),
                                'object': 'chat.completion.chunk',
                                'created': int(time.time()),
                                'model': model_id,
                                'choices': [{ 'delta': {'content': content}, 'index': 0, 'finish_reason': None }]
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"

                        if is_end:
                            yield "data: [DONE]\n\n"
                            break

                    except Exception as e:
                        print("Failed to parse line:", line)
                        print(e)
                        continue



@app.get("/v1/models")
def list_models():
    model_id = MaxKBParas.model_id
    try: model_id = os.getenv("MODEL_ID", "default_id")
    except: pass
    return {
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 0,
                "owned_by": "you",
                "permission": []
            }
        ],
        "object": "list"
    }

@app.post("/v1/chat/completions")
async def generate_text(request: ChatCompletionRequest):
    # TODO Can we find a way don't need to generate chat_id every time?
    chat_res = await max_db_info.get_chatId(MaxKBParas.input_url, MaxKBParas.application_id)
    chat_id = chat_res["data"]
    max_db_info.chat_id = chat_id
    
    try:
        # formatted_prompt = MaxKBProxy.format_messages(request.messages)
        formatted_prompt = request.messages[-1].content
        print(f"formatted_prompt: {formatted_prompt}. End")
        if request.stream:
            return StreamingResponse(
                MaxKBProxy.stream_maxkb_chunks(formatted_prompt, request.model, chat_id),
                media_type="text/event-stream"
            )
        else:
            answer = await MaxKBProxy.call_maxkb(formatted_prompt, chat_id)
            return {
                "id": str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "message": {"role": "assistant", "content": answer},
                    "index": 0,
                    "finish_reason": "stop"
                }]
            }
    except StarletteHTTPException as http_err:
        return {"error": http_err.detail}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=MaxKBParas.port)
