import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
# from langchain_openai import OpenAI
import time
import pandas as pd
import numpy as np
from enum import Enum
from pydantic import BaseModel
import json
from ast import literal_eval

# NOTE: gather of data
sample_data = pd.read_csv("./Daily_Sugar_Intake_Data.csv").to_json()

class ContentType(str, Enum):
    clarifying_question = "clarifying_question"
    explanation = "explanation"
    disclaimer = "disclaimer"
    
class ResponseType(str, Enum):
    text = "text"

class Response(BaseModel):
    category: ContentType
    content: str
    type: ResponseType
    
openai_api_key = st.secrets.get("OPENAI_API_KEY")
org_id = st.secrets.get("OPENAI_ORG_ID")


# client = OpenAI(
#     api_key=openai_api_key, 
#     organization=org_id
# )

client = OpenAI(
    api_key=st.secrets.get("OPENAI_API_KEY"), 
    organization=st.secrets.get("OPENAI_ORG_ID")
)

st.sidebar.title("Visualization")

with st.sidebar:
    components.iframe(
        "https://human.biodigital.com/viewer/?id=5mtE&ui-anatomy-descriptions=true&ui-anatomy-pronunciations=true&ui-anatomy-labels=true&ui-audio=true&ui-chapter-list=false&ui-fullscreen=true&ui-help=true&ui-info=true&ui-label-list=true&ui-layers=true&ui-skin-layers=true&ui-loader=circle&ui-media-controls=full&ui-menu=true&ui-nav=true&ui-search=true&ui-tools=true&ui-tutorial=false&ui-undo=true&ui-whiteboard=true&initial.none=true&disable-scroll=false&uaid=LxpSS&paid=o_26da67b2",
        height=600,
        width=400
    )

st.title("Quectonic Prototype")

def stream_data(data):
    # silent = False
    # data = ""
    for item in data.split(" "):
        # try:    
        #     if (item == "<bar>"):
        #         silent = not silent
        #         data = data + item
                
        #         if (silent == False):
        #             x = data.replace('<bar>', '').split("|")[1].strip()
        #             y = data.replace('<bar>', '').split("|")[2].strip()
                    
        #             x_list = literal_eval('[' + x + ']')
        #             y_list = literal_eval('[' + y + ']')
                    
        #             if (all(isinstance(i, (int, float))) for i in x_list):
        #                 st.bar_chart(pd.DataFrame({"x": x_list, "y": y_list}))
            
        #     if (silent): 
        #         continue
        # except:
        #     continue
        
        yield item + " "
        time.sleep(0.05)
          
# Initialize chat history
if "messages" not in st.session_state:
    st.sidebar.write("Initializing chat history")
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a medical professional with rich medical knowledge and only answer medically relevant questions. "
                "You will take the conversation step by step and not respond with a conclusion right after a prompt is enter. "
                "Instead, you will ask user detailed clarification questions, one at a time, for further information, such as what user did "
                "for the past few days or if they remember any minor accidents they had and might be related to their described conditions, if needed. "
                "When you have sufficient information obtained by asking user clarification questions, you will answer with explanation, "
                "such as cause and physiology of conditions, self-care options, how most people respond to the mentioned incoming problems or concerns, "
                "and compare the conditions to other historical records of similar medical cases, if applicable. "
                "If the incoming question is highly specific for an answer of a specific questions, you will solve the specific question first. \n\n"
                "You also emphasize that your answer might not be perfect or applicable to everyone because of different physiological setup for every human. "
                "You will provide disclaimer that your response is not a clinical diagnosis or recommendation of personalized treatment when you are answering "
                "questions and have similar text in your answer. \n\n"
                "Your summary response will be clearly segmented by coverage of topics, such as causes, common responses, resources, etc."
            )
        },
        {
            "role": "system",
            "content": "Here are some premise data for user's health. The sugar metric of user is described in this data: " + sample_data + ". Use this data and compare if it is relevant to user's query. If it is, respond based on this data and reference it. If you want to visualize those data using bar graph, use '''<bar>[strictly the name of data source, such as 'sugar metric' in this case]|x-values separated by ','|y-values separated by ','<bar>'''"
        },
        {
            "role": "assistant",
            "content": "Hello! How can I help with your health related questions?"
        }
    ] 

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if (message["role"] == "system"):
        continue
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        elif message["role"] == "assistant":
            if (': <ans>' in message["content"]):
                st.markdown(message["content"].split(': <ans> ')[1])
            else:
                st.markdown(message["content"])
    
        
if prompt := st.chat_input("What are your concerns?"):
    with st.chat_message("user"):
        st.markdown(prompt)
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    ## Call OpenAI API for model output
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=st.session_state.messages,
        temperature=1,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format=Response
    )
    
    content = response.choices[0].message.parsed
    
    # Display assistant response in chat message container
    with st.chat_message("Quectonic Bot"):
        st.write_stream(stream_data(content.content))
    # Add assistant response to chat history
    
    ## NOTE: ADD RESPONSE META DATA TO DATABASE IF APPLICABLE
    ## NOTE: ADD VALIDATION LOGICS 
    
    st.session_state.messages.append({"role": "assistant", "content": f"{content.category}, {content.type}: <ans> {content.content}"})
    
    st.sidebar.write("Chat history updated, count: ", len(st.session_state.messages))
    st.sidebar.write(st.session_state.messages)

