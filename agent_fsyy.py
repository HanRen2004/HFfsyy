import streamlit as st
import requests
import uuid
import dashscope
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.tools import tool
from langchain_community.llms.tongyi import Tongyi
import os
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_core.prompts import PromptTemplate
from openai import OpenAI
from langchain_openai import ChatOpenAI
from flask import Flask, request, jsonify
from streamlit.components.v1 import html
import base64
import threading
import time

# 页面配置
st.set_page_config(page_title="放松音乐", page_icon="🎵 ")

# 自定义 CSS 样式
custom_css = """
<style>
    h1 {
        font-size: 2.5rem;
        color: #333;
        text-align: center;
    }

    h2 {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 20px;
    }

    .result-block {
        border: 1px solid #ddd;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 8px;
        background-color: #f9f9f9;
    }

    .result-block h3 {
        font-size: 1.2rem;
        color: #4a4a4a;
        margin-bottom: 10px;
    }

    .result-block p {
        font-size: 1rem;
        color: #555;
        margin-bottom: 5px;
    }

    .result-block a {
        display: inline-block;
        margin-top: 10px;
        padding: 8px 12px;
        background-color: #007BFF;
        color: white;
        text-decoration: none;
        border-radius: 5px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 页面标题和小标题
st.title("放松音乐")
st.markdown('<h2 style="font-family: Arial;">放松心情，缓解压力</h2>', unsafe_allow_html=True)

# 设置 API 密钥
os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY", "sk-38a6f574d6c6483eae5c32998a16822a")
os.environ["DASHSCOPE_API_BASE"] = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")



# 创建网络搜索工具
@tool
def bocha_websearch_tool(query: str, count: int = 20) -> str:
    """
    使用Bocha Web Search API 网页搜索
    """
    url = 'https://api.bochaai.com/v1/web-search'
    headers = {
        'Authorization': f'Bearer sk-6012a020f72d4c26ae5ad415300c94f9',
        'Content-Type': 'application/json'
    }
    data = {
        "query": query,
        "freshness": "noLimit",
        "summary": True,
        "count": count
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        try:
            json_response = response.json()
            if json_response["code"] == 200 and json_response.get("data"):
                webpages = json_response["data"]["webPages"]["value"]
                if not webpages:
                    return "未找到相关结果."
                formatted_results = ""
                for idx, page in enumerate(webpages, start=1):
                    formatted_results += (
                        f"引用：{idx}\n"
                        f"标题：{page['name']}\n"
                        f"URL: {page['url']}\n"
                        f"摘要：{page['summary']}\n"
                        f"网站名称：{page['siteName']}\n"
                        f"网站图标：{page['siteIcon']}\n"
                        f"发布时间：{page['dateLastCrawled']}\n\n"
                    )
                return formatted_results.strip()
            else:
                return f"搜索失败，原因：{json_response.get('message', '未知错误')}"
        except Exception as e:
            return f"处理搜索结果失败，原因是：{str(e)}\n原始响应：{response.text}"
    else:
        return f"搜索API请求失败，状态码：{response.status_code}, 错误信息：{response.text}"


memory = ConversationBufferMemory(memory_key="chat_history",return_messages=True)

llm = ChatOpenAI(
    model="qwen-max",
    temperature=0.8,
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

bocha_tool = Tool(
    name="Bocha Web Search",
    func=bocha_websearch_tool,
    description="使用Bocha Web Search API进行搜索互联网网页，输入应为搜索查询字符串，输出将返回搜索结果的详细信息。包括网页标题、网页URL",
)



#搜索工具提示词
agent_prompt = """
国内直连 自然白噪音 单曲播放
无登陆要求 空灵吟唱
网页音乐 纯音乐 单曲直链
无需下载
HTTP状态码200 直接访问
读取在bocha_tool返回结果中可用的网址链接，并返回
"""


agent = initialize_agent(
    tools=[bocha_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    agent_kwargs={"agent_prompt": agent_prompt, 'memory': memory}
)




#大语言模型提示词
prompt_template_with_search_results = """
{previous_conversation}

最新的搜索结果如下：
{search_results}

请推荐适合心理放松场景的治愈系单曲资源，要求：
1、提供国内可直接网页播放的直链（无需登录/翻墙）
2.标注CCB授权或平台免费试听音乐
3、完全排除疾病相关描述（包括隐喻词汇）
4、输出格式：歌曲名称 +创作者+时长+国内直连平台名称+直接访问链接（HTTPS协议，已验证可访问，并且应该在bocha_tool的搜索返回结果）
5.推荐纯器乐或自然音效类音乐，或者其他类型的轻音乐
6.优先使用国内CDN加速资源
"""

final_prompt = PromptTemplate(
    input_variables=["previous_conversation", "search_results"],
    template=prompt_template_with_search_results
)



llm_chat = ChatOpenAI(
    model="qwen-max-latest",
    temperature=0.8,
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

chain = LLMChain(llm=llm_chat, prompt=final_prompt)





#用户提问（功能相关）
user_question = "我想得到一些放松音乐,请给我可用的网络链接"


response = agent.run(user_question)

# 准备输入给 Final Prompt 的数据
inputs = {
    "previous_conversation": "\n".join([str(message) for message in memory.load_memory_variables({})["chat_history"]]),
    "search_results": response
}

final_response=chain.run(inputs)


st.write(final_response)
