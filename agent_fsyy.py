import streamlit as st
import requests
import uuid
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
    /* 全局样式 */
    body {
        background-color: #f0f8ff;
        font-family: 'Arial', sans-serif;
        color: #333;
        transition: all 0.3s ease;
    }
    
    /* 背景图片和渐变 */
    .stApp {
        background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNjAwIiB2aWV3Qm94PSIwIDAgODAwIDYwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzhBMkJFMjtzdG9wLW9wYWNpdHk6MC44IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjUwJSIgc3R5bGU9InN0b3AtY29sb3I6IzRCMDA4MjtzdG9wLW9wYWNpdHk6MC42IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM5MzcwREI7c3RvcC1vcGFjaXR5OjAuNyIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQyIiB4MT0iMTAwJSIgeTE9IjAlIiB4Mj0iMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzAwQ0VEMTtzdG9wLW9wYWNpdHk6MC42IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyMEIyQUE7c3RvcC1vcGFjaXR5OjAuNCIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8ZmlsdGVyIGlkPSJibHVyIiB4PSItNTAlIiB5PSItNTAlIiB3aWR0aD0iMjAwJSIgaGVpZ2h0PSIyMDAlIj4KICAgICAgPGZlR2F1c3NpYW5CbHVyIGluPSJTb3VyY2VHcmFwaGljIiBzdGREZXZpYXRpb249IjMwIiAvPgogICAgPC9maWx0ZXI+CiAgPC9kZWZzPgogIAogIDwhLS0g6IOM5pmv5riQ5Y+YIC0tPgogIDxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JhZDEpIiAvPgogIAogIDwhLS0g6KOF6aWw5ZyG5b2iIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjE1MCIgcj0iMTAwIiBmaWxsPSJ1cmwoI2dyYWQyKSIgZmlsdGVyPSJ1cmwoI2JsdXIpIiAvPgogIDxjaXJjbGUgY3g9IjYwMCIgY3k9IjQwMCIgcj0iMTIwIiBmaWxsPSIjRkY2OUI0IiBvcGFjaXR5PSIwLjQiIGZpbHRlcj0idXJsKCNibHVyKSIgLz4KICA8Y2lyY2xlIGN4PSIxMDAiIGN5PSI1MDAiIHI9IjgwIiBmaWxsPSIjNDY4MkI0IiBvcGFjaXR5PSIwLjUiIGZpbHRlcj0idXJsKCNibHVyKSIgLz4KICA8Y2lyY2xlIGN4PSI3MDAiIGN5PSIxMDAiIHI9IjYwIiBmaWxsPSIjMzJDRDMyIiBvcGFjaXR5PSIwLjQiIGZpbHRlcj0idXJsKCNibHVyKSIgLz4KICA8IS0tIOmfs+azqOijhemlsCAtLT4KICA8cGF0aCBkPSJNNDAwLDEwMCBRNDIwLDgwIDQ0MCwxMDAgVDQ4MCwxMDAiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC43IiAvPgogIDxwYXRoIGQ9Ik00ODAsMTAwIEw0ODAsMTcwIFE0NjAsMTkwIDQ4MCwyMTAgVDQ4MCwyNTAiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC43IiAvPgogIDxjaXJjbGUgY3g9IjQ4MCIgY3k9IjI1MCIgcj0iMTUiIGZpbGw9IndoaXRlIiBvcGFjaXR5PSIwLjciIC8+CiAgPHBhdGggZD0iTTMwMCwyMDAgUTMyMCwxODAgMzQwLDIwMCBUMzgwLDIwMCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIiBvcGFjaXR5PSIwLjYiIC8+CiAgPHBhdGggZD0iTTM4MCwyMDAgTDM4MCwyNzAgUTM2MCwyOTAgMzgwLDMxMCBUMzgwLDM1MCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIiBvcGFjaXR5PSIwLjYiIC8+CiAgPGNpcmNsZSBjeD0iMzgwIiBjeT0iMzUwIiByPSIxNSIgZmlsbD0id2hpdGUiIG9wYWNpdHk9IjAuNiIgLz4KICA8cGF0aCBkPSJNNTAwLDMwMCBRNTIwLDI4MCA1NDAsMzAwIFQ1ODAsMzAwIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIG9wYWNpdHk9IjAuNSIgLz4KICA8cGF0aCBkPSJNNTgwLDMwMCBMNTgwLDM3MCBRNTYwLDM5MCA1ODAsNDEwIFQ1ODAsNDUwIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIG9wYWNpdHk9IjAuNSIgLz4KICA8Y2lyY2xlIGN4PSI1ODAiIGN5PSI0NTAiIHI9IjE1IiBmaWxsPSJ3aGl0ZSIgb3BhY2l0eT0iMC41IiAvPgo8L3N2Zz4=');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* 标题样式 */
    h1 {
        font-size: 3.5rem;
        font-weight: bold;
        color: #fff;
        text-align: center;
        margin-top: 30px;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5);
        background: linear-gradient(45deg, #FF6B6B, #FFD166, #06D6A0, #118AB2, #073B4C);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        animation: gradient 10s ease infinite;
        background-size: 300% 300%;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    h2 {
        font-size: 1.8rem;
        color: #fff;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 300;
        text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* 音乐波形动画 */
    .music-wave {
        width: 100%;
        height: 100px;
        margin: 20px 0;
        background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgODAwIDIwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9IndhdmVHcmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGRjZCNkIiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iNTAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkZEMTY2IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMwNkQ2QTAiIC8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogIDwvZGVmcz4KICAKICA8IS0tIOmfs+mHj+azqOW9oiAtLT4KICA8ZyBjbGFzcz0id2F2ZS1ncm91cCI+CiAgICA8cGF0aCBkPSJNMCwxMDAgUTQwLDIwIDgwLDEwMCBUMTYwLDEwMCBUMjQwLDEwMCBUMzIwLDEwMCBUNDAwLDEwMCBUNDgwLDEwMCBUNTYwLDEwMCBUNjQwLDEwMCBUNzIwLDEwMCBUODAwLDEwMCIgCiAgICAgICAgICBzdHJva2U9InVybCgjd2F2ZUdyYWQpIiBzdHJva2Utd2lkdGg9IjMiIGZpbGw9Im5vbmUiPgogICAgICA8YW5pbWF0ZSBhdHRyaWJ1dGVOYW1lPSJkIiAKICAgICAgICAgICAgICAgdmFsdWVzPSJNMCwxMDAgUTQwLDIwIDgwLDEwMCBUMTYwLDEwMCBUMjQwLDEwMCBUMzIwLDEwMCBUNDAwLDEwMCBUNDgwLDEwMCBUNTYwLDEwMCBUNjQwLDEwMCBUNzIwLDEwMCBUODAwLDEwMDsKICAgICAgICAgICAgICAgICAgICAgIE0wLDEwMCBRNDAsMTAwIDgwLDE4MCBUMTYwLDEwMCBUMjQwLDE4MCBUMzIwLDEwMCBUNDAwLDE4MCBUNDgwLDEwMCBUNTYwLDE4MCBUNjQwLDEwMCBUNzIwLDE4MCBUODAwLDEwMDsKICAgICAgICAgICAgICAgICAgICAgIE0wLDEwMCBRNDAsMjAgODAsMTAwIFQxNjAsMTAwIFQyNDAsMTAwIFQzMjAsMTAwIFQ0MDAsMTAwIFQ0ODAsMTAwIFQ1NjAsMTAwIFQ2NDAsMTAwIFQ3MjAsMTAwIFQ4MDAsMTAwIiAKICAgICAgICAgICAgICAgZHVyPSIxMHMiIAogICAgICAgICAgICAgICByZXBlYXRDb3VudD0iaW5kZWZpbml0ZSIgLz4KICAgIDwvcGF0aD4KICAgIAogICAgPHBhdGggZD0iTTAsMTAwIFE0MCw2MCA4MCwxMDAgVDE2MCwxMDAgVDI0MCwxMDAgVDMyMCwxMDAgVDQwMCwxMDAgVDQ4MCwxMDAgVDU2MCwxMDAgVDY0MCwxMDAgVDcyMCwxMDAgVDgwMCwxMDAiIAogICAgICAgICAgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuNSkiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSI+CiAgICAgIDxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9ImQiIAogICAgICAgICAgICAgICB2YWx1ZXM9Ik0wLDEwMCBRNDAsNjAgODAsMTAwIFQxNjAsMTAwIFQyNDAsMTAwIFQzMjAsMTAwIFQ0MDAsMTAwIFQ0ODAsMTAwIFQ1NjAsMTAwIFQ2NDAsMTAwIFQ3MjAsMTAwIFQ4MDAsMTAwOwogICAgICAgICAgICAgICAgICAgICAgTTAsMTAwIFE0MCwxMDAgODAsMTQwIFQxNjAsMTAwIFQyNDAsMTQwIFQzMjAsMTAwIFQ0MDAsMTQwIFQ0ODAsMTAwIFQ1NjAsMTQwIFQ2NDAsMTAwIFQ3MjAsMTQwIFQ4MDAsMTAwOwogICAgICAgICAgICAgICAgICAgICAgTTAsMTAwIFE0MCw2MCA4MCwxMDAgVDE2MCwxMDAgVDI0MCwxMDAgVDMyMCwxMDAgVDQwMCwxMDAgVDQ4MCwxMDAgVDU2MCwxMDAgVDY0MCwxMDAgVDcyMCwxMDAgVDgwMCwxMDAiIAogICAgICAgICAgICAgICBkdXI9IjdzIiAKICAgICAgICAgICAgICAgcmVwZWF0Q291bnQ9ImluZGVmaW5pdGUiIC8+CiAgICA8L3BhdGg+CiAgICAKICAgIDxwYXRoIGQ9Ik0wLDEwMCBRNDAsODAgODAsMTAwIFQxNjAsMTAwIFQyNDAsMTAwIFQzMjAsMTAwIFQ0MDAsMTAwIFQ0ODAsMTAwIFQ1NjAsMTAwIFQ2NDAsMTAwIFQ3MjAsMTAwIFQ4MDAsMTAwIiAKICAgICAgICAgIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjMpIiBzdHJva2Utd2lkdGg9IjEuNSIgZmlsbD0ibm9uZSI+CiAgICAgIDxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9ImQiIAogICAgICAgICAgICAgICB2YWx1ZXM9Ik0wLDEwMCBRNDAsODAgODAsMTAwIFQxNjAsMTAwIFQyNDAsMTAwIFQzMjAsMTAwIFQ0MDAsMTAwIFQ0ODAsMTAwIFQ1NjAsMTAwIFQ2NDAsMTAwIFQ3MjAsMTAwIFQ4MDAsMTAwOwogICAgICAgICAgICAgICAgICAgICAgTTAsMTAwIFE0MCwxMDAgODAsMTIwIFQxNjAsMTAwIFQyNDAsMTIwIFQzMjAsMTAwIFQ0MDAsMTIwIFQ0ODAsMTAwIFQ1NjAsMTIwIFQ2NDAsMTAwIFQ3MjAsMTIwIFQ4MDAsMTAwOwogICAgICAgICAgICAgICAgICAgICAgTTAsMTAwIFE0MCw4MCA4MCwxMDAgVDE2MCwxMDAgVDI0MCwxMDAgVDMyMCwxMDAgVDQwMCwxMDAgVDQ4MCwxMDAgVDU2MCwxMDAgVDY0MCwxMDAgVDcyMCwxMDAgVDgwMCwxMDAiIAogICAgICAgICAgICAgICBkdXI9IjVzIiAKICAgICAgICAgICAgICAgcmVwZWF0Q291bnQ9ImluZGVmaW5pdGUiIC8+CiAgICA8L3BhdGg+CiAgPC9nPgo8L3N2Zz4=');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
    }
    
    /* 音乐卡片样式 */
    .music-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.18);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .music-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.3);
    }
    
    .music-card h3 {
        font-size: 1.4rem;
        color: #fff;
        margin-bottom: 15px;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    .music-card p {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 8px;
    }
    
    .music-card a {
        display: inline-block;
        margin-top: 15px;
        padding: 10px 20px;
        background: linear-gradient(45deg, #FF6B6B, #FFD166);
        color: white;
        text-decoration: none;
        border-radius: 30px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .music-card a:hover {
        background: linear-gradient(45deg, #FFD166, #06D6A0);
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }
    
    /* 装饰元素 */
    .decoration {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: -1;
        overflow: hidden;
    }
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        h1 {
            font-size: 2.5rem;
        }
        
        h2 {
            font-size: 1.3rem;
        }
        
        .music-card {
            padding: 15px;
        }
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


# 添加音乐波形动画
st.markdown('<div class="music-wave"></div>', unsafe_allow_html=True)

# 添加标题和描述
st.markdown('<div style="text-align: center; margin-bottom: 30px;"><h3 style="color: #fff; text-shadow: 1px 1px 3px rgba(0,0,0,0.3);">为您推荐的放松音乐</h3><p style="color: rgba(255,255,255,0.8);">以下音乐经过精心筛选，帮助您缓解压力，放松身心</p></div>', unsafe_allow_html=True)

# 将响应包装在音乐卡片中显示
st.markdown(f'<div class="music-card">{final_response}</div>', unsafe_allow_html=True)

# 添加页脚
st.markdown('<div style="text-align: center; margin-top: 50px; padding: 20px; color: rgba(255,255,255,0.6);"><p>音乐是心灵的良药，愿美妙的旋律伴您度过美好时光</p><div style="margin-top: 10px;"><span style="display: inline-block; margin: 0 10px; font-size: 24px;">🎵</span><span style="display: inline-block; margin: 0 10px; font-size: 24px;">🎹</span><span style="display: inline-block; margin: 0 10px; font-size: 24px;">🎧</span><span style="display: inline-block; margin: 0 10px; font-size: 24px;">🎼</span></div></div>', unsafe_allow_html=True)
