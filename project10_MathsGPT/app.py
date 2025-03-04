import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMMathChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.agents.agent_types import AgentType
from langchain.agents import Tool, initialize_agent
from langchain.callbacks import StreamlitCallbackHandler

## Set upi the streamlit App
st.set_page_config(page_title="Text To MAth Problem Solver And Data Serach Assistant",page_icon="🧮",layout="wide")
st.title("Maths GPT for Text To Math Problem Solver BY Bhevin 🤖")

groq_api_key=st.sidebar.text_input(label="Groq API Key",type="password")


if not groq_api_key:
    st.info("Please add your Groq API key to continue")
    st.stop()



# llm=ChatGroq(model="llama-3.3-70b-versatile",groq_api_key=groq_api_key)
llm=ChatGroq(model="mixtral-8x7b-32768",groq_api_key=groq_api_key)

## Initializing the tools
wikipedia_wrapper=WikipediaAPIWrapper()
wikipedia_tool=Tool(
    name="Wikipedia",
    func=wikipedia_wrapper.run,
    description="A tool for searching the Internet to find the vatious information on the topics mentioned"

)

## Initializa the MAth tool

math_chain=LLMMathChain.from_llm(llm=llm)
calculator=Tool(
    name="Calculator",
    func=math_chain.run,
    description="A tools for answering math related questions. Only input mathematical expression need to bed provided"
)

prompt="""
Your a agent tasked for solving users mathemtical question. Logically arrive at the solution and provide a detailed explanation
and display it point wise for the question below

"Explain the step-by-step process you used to solve the problem. Show all your work clearly and concisely, ensuring it is legible and
understandable. Provide the final answer in the designated space."

**Step-by-Step Process:**

**Understand the Problem:**
   - Identify the key mathematical concepts involved.
   - Break down the problem into manageable steps.


**Choose an Appropriate Method:**
   - Select the best mathematical method or formula to solve the problem.


**Solve the Problem:**
   - Apply the chosen method to the problem.
   - Perform the necessary calculations and steps.
   - Check for accuracy and completeness.


**Explain the Solution:**
   - Outline the step-by-step process used to solve the problem.
   - Explain the mathematical concepts and principles employed.
   - Provide clear and concise explanations of the steps taken.


**Provide the Answer:**
   - Clearly display the final answer in the designated space.
   - Ensure the answer is accurate and matches the problem requirements.


**Additional Tips:**

* Use clear and concise language.
* Ensure legibility and readability.
* Display all work clearly and step-by-step.

Question:{question}
Answer:
"""
prompt_template=PromptTemplate(
    input_variables=["question"],
    template=prompt
)

## Combine all the tools into chain
chain=LLMChain(llm=llm,prompt=prompt_template)

reasoning_tool=Tool(
    name="Reasoning tool",
    func=chain.run,
    description="A tool for answering logic-based and reasoning questions."
)

## Initialize the agents

assistant_agent=initialize_agent(
    tools=[wikipedia_tool,calculator,reasoning_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True   
)

if "messages" not in st.session_state:
    st.session_state["messages"]=[
        {"role":"assistant","content":"Hi, I'm a Bhevin MAth chatbot who can answer all your maths questions"}
    ]
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg['content'])

## LETS Start the Interaction
question=st.text_area("Enter youe question:","The modulation invariance of the oscillatory integral operator")

if st.button("find my answer"):
    if question:
        with st.spinner("Generate response.."):
            st.session_state.messages.append({"role":"user","content":question})
            st.chat_message("user").write(question)

            st_cb=StreamlitCallbackHandler(st.container(),expand_new_thoughts=False)
            response=assistant_agent.run(st.session_state.messages,callbacks=[st_cb]
                                         )
            st.session_state.messages.append({'role':'assistant',"content":response})
            st.write('### Response:')
            st.success(response)

    else:
        st.warning("Please enter the question")


### streamlit run app.py 