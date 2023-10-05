from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain import PromptTemplate

import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# initializing pinecone db
print('[+] Initializing pinecone db...')
pinecone.init(
    api_key=os.getenv('PINECONE_API_KEY'),
    environment=os.getenv('PINECONE_REGION'),
)

index_name = 'draft'

qa_template = """ 
You are a helpful Ecommerce expert/mentor. Your name is Ecom Genie. Your users are trying to setup your ecommerce business. You provide accurate and descriptive answers to user questions based on the context provided. You understand the context and then answer the user questions keeping in mind that the end goal is to provide answers to users which helps them in setting up their ecommerce business. If you don't know the answer, just say you don't know. Do NOT try to make up an answer.
If you cannot answer a question, politely respond that this is beyond the scope of your knowledge.
Use as much detail as possible when responding.
=========
question: {question}
======
"""

QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["question"])

llm = ChatOpenAI(openai_api_key=os.getenv('OPENAI_API_KEY'),
                 model_name='gpt-4',
                 temperature=0.3, verbose=True)

embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENAI_API_KEY'))

# chain
chain = load_qa_chain(llm, chain_type="stuff", verbose=False)

# for searching relevant docs
docsearch = Pinecone.from_existing_index(index_name, embeddings)



def get_response(query):
    # relevant docs
    print("[+] - aibot2 get_response called: function query: ", query)
    try:
        docs = docsearch.similarity_search(query)
        print("[+] - aibot2 docsearch.similarity_search(query) called")
    except:
        print("[-] - aibot2 Exception Occured in Pinecone DocSearch")
        print("[-] - aibot2 setting docs to []")
        docs = []
    print("[+] - aibot2 Relevant docs: ", docs)
    # await asyncio.sleep(1)
    response = chain(
        {
            "input_documents": docs,
            "question": QA_PROMPT.format(question=query)
        },
        return_only_outputs=True
    )
    print("[+] - aibot2 response :", response)
    res = {
        'model': 'gpt-4',
        'choices': [
            {
                'index': 0,
                'message': {'role': 'assistant', 'content': response["output_text"]}
            }
        ]
    }
    print('[+] - aibot2 #######################################################################')
    print('[+] - aibot2', res)
    return res


if __name__ == "__main__":
    print("START THE CHAT:\n")
    chat_hist = ConversationBufferMemory()
    while True:
        query = input("[+] [You]: ")
        if query=='end':
            print("[+] ending the conversation...")
            print("[+] exiting...")
            break
        response = get_response(query)
        print("[+] [bot]: ", response['choices'][0]['message']['content'])
