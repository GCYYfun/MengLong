import json
import fastapi
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from string import Template
from enum import Enum
import yaml
import os
import sys


# 导入MengLong库的相关模块
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from mlong.model_interface import Model
from mlong.model_interface.utils import user, system
from mlong.agent.role_play import RoleAgent, GameAgent
from mlong.agent.conversation.conversation_gtg import GTGConversation
from mlong.tools.vector_database import VectorStore

DEFAULT_MEMORY_SPACE = os.path.join(os.path.dirname(__file__), "configs")
DEFAULT_ROLE_PATH = os.path.join(os.path.dirname(__file__), "configs", "roles")
DEFAULT_TOPIC_PROMPT = os.path.join(
    os.path.dirname(__file__), "configs", "topics", "ds_chat_v3.yaml"
)

# 创建FastAPI应用实例
app = FastAPI(
    title="MengLong API",
    description="MengLong框架API服务，提供大模型对话、角色扮演、RAG等功能",
    version="1.0.0",
)

# 配置CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义模型ID枚举类型
class ModelID(str, Enum):
    CLAUDE_3_7_SONNET = "Claude-3.7-Sonnet"
    DEEPSEEK_R1_V1 = "us.deepseek.r1-v1:0"
    DEEPSEEK_REASONER = "deepseek-reasoner"
    DEEPSEEK_CHAT = "deepseek-chat"
    GPT_4O = "gpt-4o"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    AMAZON_NOVA_PRO = "us.amazon.nova-pro-v1:0"
    ANTHROPIC_CLAUDE_3_5 = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    ANTHROPIC_CLAUDE_3_7 = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    COHERE_EMBED = "cohere.embed-multilingual-v3"


# 定义请求和响应模型
class Message(BaseModel):
    role: str
    content: str


class ChatParam(BaseModel):
    messages: List[Message]
    model_id: ModelID = ModelID.DEEPSEEK_REASONER
    temperature: float = 0
    max_tokens: int = 8192
    stream: bool = False


class RoleParam(BaseModel):
    role_name: str
    message: str
    model_id: ModelID = ModelID.DEEPSEEK_REASONER
    stream: bool = False


class ConversationParam(BaseModel):
    active_role: str
    passive_role: str
    topic: str
    memory_space: str = "memory"
    model_id: ModelID = ModelID.DEEPSEEK_REASONER


class VectorStoreParam(BaseModel):
    collection_name: str
    documents: Optional[List[str]] = None
    query: Optional[str] = None
    top_k: int = 5


# API端点实现
@app.get("/")
async def root():
    return {"message": "欢迎使用MengLong API服务"}


@app.get("/api/models")
async def models():
    return {"models": list(ModelID)}


# 基础聊天接口
@app.post("/api/chat")
async def chat(param: ChatParam):
    try:
        model = Model()
        if param.stream:
            # 流式响应需要在前端处理
            response = model.chat(
                messages=param.messages, model_id=param.model_id, stream=True
            )

            # 创建一个生成器函数来处理流式响应
            async def stream_generator():
                # 对流式响应进行处理
                for chunk in response:
                    # 如果是 ChatStreamResponse 对象，需要将其转换为字典
                    chunk_dict = (
                        chunk.dict() if hasattr(chunk, "dict") else {"text": str(chunk)}
                    )
                    yield f"data: {chunk_dict}\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            res = model.chat(messages=param.messages, model_id=param.model_id)
            return {"response": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 角色扮演聊天接口
@app.post("/api/agent/chat")
async def agent_chat(param: RoleParam):
    role_file_path = os.path.join("configs", "roles", param.role_name + ".yaml")
    with open(role_file_path, "r") as f:
        role_config = yaml.safe_load(f)
    try:
        agent = RoleAgent(dict(role_config), model_id=param.model_id)
        if param.stream:
            # 流式响应需要在前端处理
            response = agent.chat_stream(param.message)

            # 创建一个生成器函数来处理流式响应
            async def stream_generator():
                # 对流式响应进行处理
                for chunk in response:
                    # 如果是 ChatStreamResponse 对象，需要将其转换为字典
                    chunk_dict = (
                        chunk.dict() if hasattr(chunk, "dict") else {"text": str(chunk)}
                    )
                    yield f"data: {chunk_dict}\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            # 非流式响应
            res = agent.chat(param.message, stream=param.stream)
            return {"response": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/plan")
async def agent_plan():
    plan_file_path = os.path.join("configs", "prompts", "plan.yaml")
    with open(plan_file_path, "r") as f:
        plan_config = yaml.safe_load(f)
    try:
        model = Model()
        prompt = Template(plan_config["prompt"]).substitute(plan_config["var"])
        messages = [system(plan_config["system"]), user(prompt)]
        res = model.chat(
            messages=messages,
            model_id=plan_config["use_model"]["model_id"],
            temperature=plan_config["use_model"]["temperature"],
            max_tokens=plan_config["use_model"]["max_tokens"],
        )
        print(res)
        return {"response": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NPC角色扮演聊天接口
@app.post("/api/agent/npc")
async def npc_chat(param: RoleParam, clear_memory: bool = False):
    try:
        # 创建FluctLight实例，使用内存中存储而非文件
        npc = GameAgent(role_config=dict(param.role_config))

        if clear_memory:
            npc.clear()
            print("记忆已清除")

        res = npc.chat_stream_with_mem(param.message)
        return {"response": res, "system_prompt": npc.system_prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 角色对话接口
@app.post("/api/agent/ata")
async def agent_to_agent_chat(param: ConversationParam):
    role_dict = {}
    # 扫描 configs/roles 目录获取所有配置文件
    for file_name in os.listdir(DEFAULT_ROLE_PATH):
        file_path = os.path.join(DEFAULT_ROLE_PATH, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            role_dict[file_name.split(".")[0]] = yaml.safe_load(f)

    if param.topic is None or param.topic == "":
        with open(DEFAULT_TOPIC_PROMPT, "r", encoding="utf-8") as f:
            topic_dict = yaml.safe_load(f)
            topic = topic_dict["topic"]
    else:
        topic = param.topic

        # try:
    ata = GTGConversation(
        active_role=dict(role_dict[param.active_role]),
        passive_role=dict(role_dict[param.passive_role]),
        topic=topic,
        memory_space=os.path.join(DEFAULT_MEMORY_SPACE, param.memory_space),
        model_id=param.model_id,
    )

    async def stream_generator():
        for chunk in ata.chat_stream():
            if "event" in chunk:
                yield f"event: {chunk}\n\n"
            if "data" in chunk:
                yield f"data: {chunk}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


# 向量数据库接口
@app.post("/api/vectorstore")
async def vector_store(param: VectorStoreParam):
    try:
        vector_db = VectorStore()
        vector_db.connect_collection(param.collection_name)

        # 如果有文档，则添加到向量库
        if param.documents:
            doc_ids = [f"doc_{i}" for i in range(len(param.documents))]
            vector_db.add_documents(
                ids=doc_ids,
                documents=param.documents,
                metadatas=[{"source": "api"} for _ in param.documents],
            )
            return {"message": f"成功添加 {len(param.documents)} 个文档"}

        # 如果有查询，则执行查询
        elif param.query:
            results = vector_db.query(
                param.query, top_k=param.top_k, filter_conditions={"source": "api"}
            )
            return {
                "results": results,
                "documents": [vector_db.data[r["id"]]["document"] for r in results],
            }

        else:
            return {"message": "请提供文档或查询"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 简易RAG接口
@app.post("/api/rag")
async def rag_query(
    question: str = Body(..., embed=True),
    collection_name: str = Body("knowledge_base", embed=True),
):
    try:
        vector_db = VectorStore()
        vector_db.connect_collection(collection_name)

        # 检索相关文档
        results = vector_db.query(question, top_k=3)

        # 构建上下文
        context = "\n".join([vector_db.data[r["id"]]["document"] for r in results])

        # 调用模型生成回答
        model = Model()
        prompt = f"""基于以下知识库内容回答问题:
        
{context}

问题: {question}
答案:"""

        response = model.chat(
            messages=[user(prompt)], model_id=ModelID.CLAUDE_3_7_SONNET
        )

        return {
            "answer": response,
            "context": context,
            "sources": [r["id"] for r in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
