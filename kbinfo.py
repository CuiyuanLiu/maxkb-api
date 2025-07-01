import json
import asyncio
import httpx
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from fastapi import HTTPException

class RequestMaxKB(BaseModel):
    message: str
    re_chat: bool = False
    stream: bool = True
    form_data: Optional[Dict[str, Any]] = {}
    image_list: Optional[List[str]] = []
    document_list: Optional[List[str]] = []
    audio_list: Optional[List[str]] = []
    runtime_node_id: Optional[str] = ""
    node_data: Optional[Dict[str, Any]] = {}
    chat_record_id: Optional[str] = ""
    child_node: Optional[Dict[str, Any]] = {}

    def dict(self, **kwargs):
        kwargs['exclude_unset'] = True
        return super().dict(**kwargs)

class max_db_info:
    # Please update your application_id and api_key here.
    APIKEY = {
        "Your-Application-ID": "application-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    chat_id = ""

    @staticmethod
    async def get_chatId(input_url: str, application_id: str) -> Dict[str, Any]:
        url = f"{input_url}/{application_id}/chat/open"
        headers = {
            "accept": "application/json",
            "AUTHORIZATION": max_db_info.APIKEY[application_id]
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get("data")
                return {"status": 200, "data": data}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to open chat: {response.text}"
                )
        except Exception as err:
            return {"status": 201, "exception": str(err)}

    @staticmethod
    async def get_textResponse(input_url: str, application_id: str, chat_id: str, request: RequestMaxKB) -> Dict[str, Any]:
        
        if (max_db_info.chat_id == ""):
            chat_id_response = max_db_info.chat_id
            chat_id_response = await max_db_info.get_chatId(input_url, application_id)
            if not chat_id_response.get("data"):
                raise HTTPException(status_code=500, detail="Missing chat_id in response")
            print("chat_id_response['data'] =", chat_id_response["data"])
            chat_id = chat_id_response["data"]
            if not chat_id:
                raise HTTPException(status_code=500, detail="chat_id not found in response['data']")
            else: max_db_info.chat_id = chat_id

        url = f"{input_url}/chat_message/{chat_id}"
        headers = {
            "accept": "application/json",
            "AUTHORIZATION": max_db_info.APIKEY[application_id],
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=request.dict(), headers=headers)
            if (response.status_code == 200 and response.text):
                return {"status": 200, "data": response.text}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to obtain response: {response.text}"
                )
        except Exception as err:
            return {"status": 201, "exception": str(err)}
