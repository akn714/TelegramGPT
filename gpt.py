# from langchain.prompts import (SystemMessagePromptTemplate,
#                                HumanMessagePromptTemplate, ChatPromptTemplate,
#                                MessagesPlaceholder)
# from models.conversations import history, chat_history

from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationChain
from langchain.chains.question_answering import load_qa_chain
from langchain import PromptTemplate
# from services.environment_service import EnvService
# from pathlib import Path
# from typing import Union
# from langchain.schema import Document

import asyncio
from dotenv import load_dotenv
import os
# from services.environment_service import EnvService
# from services.pinecone_service import PineconeService
# from langchain.chains import ConversationalRetrievalChain

# from gpt3discord import pinecone_service

# load_dotenv(dotenv_path='.env')
load_dotenv()

# initializing pinecone db
print('[+] Initializing pinecone db...')
pinecone.init(
    api_key=os.getenv('PINECONE_TOKEN'),
    environment=os.getenv('PINECONE_REGION'),
)

index_name = 'draft'

# custom prompt
# GENIEPROMPT = "You are an Ecommerce expert/mentor. Your users are beginners in this field. You provide accurate and descriptive answers to user questions in under 2000 characters, after researching through the vector DB. Provide additional descriptions of any complex terms being used in the response.\n\n The following is a teaching conversation between a human and an AI. The AI is helping and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know. \n\nCurrent conversation: {history}\n\nUser: {input}\n\nAi: "

qa_template = """ 
You are a helpful Ecommerce expert/mentor. Your name is Ecom Genie. Your users are trying to setup your ecommerce business. You provide accurate and descriptive answers to user questions based on the context provided. You understand the context and then answer the user questions keeping in mind that the end goal is to provide answers to users which helps them in setting up their ecommerce business. If you don't know the answer, just say you don't know. Do NOT try to make up an answer.
If you cannot answer a question, politely respond that this is beyond the scope of your knowledge.
Use as much detail as possible when responding.
=========
question: {question}
======
"""

QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["question"])

llm = ChatOpenAI(openai_api_key=os.getenv('OPENAI_TOKEN'),
                 model_name='gpt-4',
                 temperature=0.3, verbose=True)
# llm = ChatOpenAI(openai_api_key="",
#                  model_name='gpt-3.5-turbo-16k',
#                  temperature=0.3, verbose=True)
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENAI_TOKEN'))

# chain
chain = load_qa_chain(llm, chain_type="stuff", verbose=False)

# for searching relevant docs
docsearch = Pinecone.from_existing_index(index_name, embeddings)

# custom prompt
# prompt_template = PromptTemplate.from_template(qa_template)

loop = asyncio.get_event_loop()

async def get_response(query):
    try:
        # Perform an asynchronous operation, e.g., accessing a database or making API requests
        # This operation can be awaited
        docs = await loop.run_in_executor(None, lambda: docsearch.similarity_search(query))
        print("[+] - aibot2 docsearch.similarity_search(query) called")
    except Exception as e:
        print("[-] - aibot2 Exception Occurred in Pinecone DocSearch:", e)
        print("[-] - aibot2 setting docs to []")
        docs = []
    print("[+] - aibot2 Relevant docs: ", docs)

    related_links = set()
    try:
        # asyncio.sleep(0.5)
        response = await loop.run_in_executor(None, lambda: chain({
            "input_documents": docs,
            "question": QA_PROMPT.format(question=query)
        }, return_only_outputs=True))
        print("[+] - aibot2 response :", response)
        
        # retrieving related links
        for i in range(len(docs)):
            related_links.add(docs[i].metadata.get('source'))
        try:
            related_links.remove('')
        except:
            print("[++++] no link equal to ''")
    except Exception as e:
        response = {'output_text':'Too Many Requests! Please try again after some time.'}

        print('[+] error in aibot2.py, response edited!')
        print(e)
        # raise e
    
    print('[-----unique links-----] 2 :', related_links)

    res = {
        'model': 'gpt-4',
        'choices': [
            {
                'index': 0,
                'message': {'role': 'assistant', 'content': response["output_text"]},
                'related_links': list(related_links)
            }
        ]
    }
    print('[+] - aibot2 #######################################################################')
    print('[+] - aibot2', res)
    return res



async def handle_request(query):
    response = await get_response(query)
    return response['choices'][0]['message']['content']
    # You can send or process the response as needed

# Create a list of queries to process concurrently
queries = ["Query 1", "Query 2", "Query 3"]  # Replace with your actual queries

# Create an asyncio event loop
async def main():
    while True:
        query = input("[+] [You]: ")
        await handle_request(query)  # Use "await" to run the task

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass


# async def fetch_async_response(query):
#     response = await get_response(query)
#     return response

# if __name__ == "__main__":
#     print("START THE CHAT:\n")
#     chat_hist = ConversationBufferMemory()
#     while True:
#         query = input("[+] [You]: ")
#         if query=='end':
#             print("[+] ending the conversation...")
#             print("[+] exiting...")
#             break
#         response = asyncio.run(fetch_async_response(query))
#         print("[+] [bot]: ", response['choices'][0]['message']['content'])
