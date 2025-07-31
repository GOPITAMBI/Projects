import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent
from langchain_community.tools import TavilySearchResults
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from tavily import TavilyClient
from langgraph.graph import MessageGraph, END


load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
SEARCH_API_KEY = os.getenv("TAVILY_API_KEY")

model = ChatGoogleGenerativeAI(

    model="gemini-2.0-flash",
    api_key=API_KEY)

# response = model.invoke("Who is the CM of AP?")
# print(response.content)

search = TavilySearchResults(tavily_api_key=SEARCH_API_KEY)
tools_list = [search]
agent = initialize_agent(tools = tools_list, llm = model, verbose=False, agent = "zero-shot-react-description")
# agent.invoke('Who is the current CM of Andhra Pradesh?')


tavily = TavilyClient(api_key=SEARCH_API_KEY)

#------Tools--------

@tool
def parse_resume(text: str) -> str:
<<<<<<< HEAD
  """Extract relevant skills, roles, and professional experience from the provided text."""
  prompt = f"Extract structured info like skils, roles, years of experience from this text:\n\n{text}"
  return model.invoke([HumanMessage(content=prompt)]).content
=======
  """Extract skills, roles, years of experience from resume text"""
  prompt = f"Extract structured info like skils, roles, years of experience from this resume:\n\n{text}"
  return model.invoke([HumanMessage(content=prompt)])
>>>>>>> 14501d5bb959c04f2d8705d6389c6cdab03f7c8a

@tool
def search_jobs_tavily(query: str) -> str:
  """Search for related jobs using Tavily and returns simplified results."""
  results = tavily.search(query)
  #print(results)
  return results["results"]

#-----nodes-----

def profile_node(state: list[BaseMessage]) ->List[BaseMessage]:
  resume = state[-1].content
  profile = parse_resume.invoke(resume)
  return state + [AIMessage(content=f"Extracted Profile\n {profile}")]

def job_search_node(state: List[BaseMessage]) -> List[BaseMessage]:
  profile = state[-2].content
  query = model.invoke([HumanMessage(content=f"Base on this profile, write a job search query:\n {profile}, keep the query very short for search engines to search")]).content
  job = search_jobs_tavily.invoke(query)
  return state + [AIMessage(content=f"Found Job\n {job}")]

def matcher_node(state: List[BaseMessage]) -> List[BaseMessage]:
  profile = state[-2].content
  jobs = state[-1].content
  prompt = f"given this profile:\n{profile}\n\n Rank and recommend only top3 jobs from:\n{jobs}"
  ranked = model.invoke([HumanMessage(content=prompt)])
  return state + [ranked]

def cover_letter_node(state: List[BaseMessage]) -> List[BaseMessage]:
  profile = state[-3].content
  best_job = state[-1].content
  prompt = f"Write a personalized short cover letter for this job:\n\n Job Info:\n {best_job} \n\n Based on Profile:\n{profile}"
  letter = model.invoke([HumanMessage(content=prompt)])
  return state + [letter]

#------LangGraph--------
graph = MessageGraph()

graph.add_node("profile", profile_node)
graph.add_node("search", job_search_node)
graph.add_node("match", matcher_node)
graph.add_node("cover", cover_letter_node)

graph.set_entry_point("profile")
graph.add_edge("profile", "search")
graph.add_edge("search", "match")
graph.add_edge("match", "cover")
graph.add_edge("cover", END)

app = graph.compile()

#-------Run Example-------
st.title("Career AI Agent")
question = st.text_input("Enter your question here:")

input_msg = HumanMessage(content=question)
results = app.invoke([input_msg])
st.markdown("Answer:")
for msg in results:
  st.write(msg.content)

# print("\n--- Output ---\n")
# for msg in results:
#   print(f"{type(msg).__name__}: {msg.content}\n")



