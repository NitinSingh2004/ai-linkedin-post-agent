import os
import requests
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Load variables from .env into system environment
load_dotenv()

# Access variables using os.getenv
api_key = os.getenv("GROQ_API_KEY")

# --- CONFIGURATION ---
# Replace these with your actual credentials or environment variables
LINKEDIN_ACCESS_TOKEN = "AQU-4p0o50LyEdrIu6ueP2IqV3vAy99-3eaCVKxWEglBjurvk8uCxUT2rVpVFEgvdYHhwCYL-E9yv1NXC9rhOPMSmuUXcoZPJzo2I9waEPDqVOsx_hrNZ_5oP11lx5hFKPKxDDmcFJrCDWIGxHbyIankdzxSEtJTSd6U26IjAg3suHhntIRCc_EpF9rtXk6YmD2XKOJJTizXeqPVHnLuJSUU63Cu204J-6mopdAi7cR_p30U6JocNya-HBBpHltwf363J0KQaNDgZ0wlHeIX8ZTXPIfjWcOqMURwI6Vzt-FKUzobeaWX6Xsw3VkMd7ZTzL6Gz3f555vpZ3CCcFbsISf8J4718A"
LINKEDIN_PERSON_URN = "urn:li:person:zg1XFz_LoW" # e.g., urn:li:person:AbC123Xyz
LINKEDIN_API_VERSION = "202604" # Manually setting the latest version

# 1. Define the State
class AgentState(TypedDict):
    query: str
    content: str
    approval_status: Literal["pending", "approved", "rejected"]

# 2. Writer Node: Generates the content
def writer_node(state: AgentState):
    llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=api_key
)
    
    system_msg = (
        "You are an expert LinkedIn Strategist. Output ONLY the final post text. "
        "Strict Rules: Use plain text only. No **bold**, no # headers. "
        "Use short sentences and bullet points (•) for readability."
    )
    
    response = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=state['query'])
    ])
    
    return {"content": response.content.strip(), "approval_status": "pending"}

# 3. Poster Node: Custom API Call to LinkedIn
def poster_node(state: AgentState):
    if state["approval_status"] != "approved":
        print("\n[SKIP] Post not approved.")
        return state

    print("\n[API] Sending post to LinkedIn...")
    
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "LinkedIn-Version": LINKEDIN_API_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    post_body = {
        "author": LINKEDIN_PERSON_URN,
        "commentary": state["content"],
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, headers=headers, json=post_body)
    
    if response.status_code == 201:
        print("✅ Successfully posted to LinkedIn!")
    else:
        print(f"❌ Failed to post: {response.status_code} - {response.text}")
        
    return state

# 4. Build and Compile the Graph
workflow = StateGraph(AgentState)
workflow.add_node("writer", writer_node)
workflow.add_node("poster", poster_node)

workflow.set_entry_point("writer")
workflow.add_edge("writer", "poster")
workflow.add_edge("poster", END)

# Memory for Human-in-the-Loop interrupts
memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["poster"])

# # --- EXECUTION ---
# if __name__ == "__main__":
#     thread_config = {"configurable": {"thread_id": "post_v1"}}
    
#     # Start the flow
#     user_query = "The importance of Human-in-the-loop in AI agentic workflows."
#     app.invoke({"query": user_query}, thread_config)

#     # Review step
#     current_state = app.get_state(thread_config)
#     print(f"\n--- DRAFT POST ---\n{current_state.values['content']}\n------------------")
    
#     choice = input("Approve this post for LinkedIn? (y/n): ").lower()
    
#     if choice == 'y':
#         # Update state and resume
#         app.update_state(thread_config, {"approval_status": "approved"}, as_node="writer")
#         app.invoke(None, thread_config)
#     else:
#         print("Post rejected.")







