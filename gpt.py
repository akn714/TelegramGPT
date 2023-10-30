from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain import PromptTemplate

import asyncio

from dotenv import load_dotenv
import os

load_dotenv()

# initializing pinecone db
print('[+] Initializing pinecone db...')
pinecone.init(
    api_key=os.getenv('PINECONE_TOKEN'),
    environment=os.getenv('PINECONE_REGION'),
)

index_name = 'draft'

qa_template = """ 
You are an helpful assistent that assest users.
=========
question: {question}
======
"""

QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["question"])

llm = ChatOpenAI(openai_api_key=os.getenv('OPENAI_TOKEN'),
                 model_name='gpt-4',
                 temperature=0.3, verbose=True)

embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENAI_TOKEN'))

# chain
chain = load_qa_chain(llm, chain_type="stuff", verbose=False)

# for searching relevant docs
docsearch = Pinecone.from_existing_index(index_name, embeddings)

loop = asyncio.get_event_loop()

async def get_response(query):
    try:
        docs = await loop.run_in_executor(None, lambda: docsearch.similarity_search(query))
        print("[+] - aibot2 docsearch.similarity_search(query) called")
    except Exception as e:
        print("[-] - aibot2 Exception Occurred in Pinecone DocSearch:", e)
        print("[-] - aibot2 setting docs to []")
        docs = []
    print("[+] - aibot2 Relevant docs: ", docs)

    related_links = set()
    try:
        response = await loop.run_in_executor(None, lambda: chain({
            "input_documents": docs,
            "question": QA_PROMPT.format(question=query)
        }, return_only_outputs=True))
        print("[+] - aibot2 response :", response)
        
        # retrieving related links
        for i in range(len(docs)):
            related_links.add(docs[i].metadata.get('yt_link'))
        try:
            related_links.remove('')
        except:
            print("[++++] no link equal to ''")
    except Exception as e:
        response = {'output_text':'Too Many Requests! Please try again after some time.'}

        print('[+] error in aibot2.py, response edited!')
        print(e)
    
    print('[-----unique links-----] :', related_links)

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
    print('[+] - aibot2', res)
    return res



async def handle_request(query):
    response = await get_response(query)
    return response['choices'][0]['message']['content']

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
