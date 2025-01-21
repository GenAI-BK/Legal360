import os
from PyPDF2 import PdfReader
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from PyPDF2 import PdfReader
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

from langchain.chains.llm import LLMChain

# Setup base directory for cases
case="Cases" 

# Function to create a case directory and save files
def create_case(case_name, filename, content, tag):
    case_directory = os.path.join(case, case_name)
    if not os.path.exists(case_directory):
        os.makedirs(case_directory)
        logging.info(f"Directory created at {case_directory}")


    file_location = os.path.join(case_directory, f"{tag}_{filename}")
    with open(file_location, "wb") as file_object:
        file_object.write(content)
        logging.info(f"File saved to {file_location}")

    return f"File {filename} saved successfully with tag {tag}"





# Function to list all cases
def list_cases():
    try:
        cases = [d for d in os.listdir(case) if os.path.isdir(os.path.join(case, d))]
        logging.info(f"Cases listed: {cases}")
    except Exception as e:
        logging.error(f"Failed to list cases: {e}")
        raise Exception(f"Failed to list cases: {e}")

    return cases

# Function to load case files into memory

os.environ["GOOGLE_API_KEY"]="AIzaSyCTBP250-hxLf--88JNtWcx4zmknJiwgXo"
llm=ChatGoogleGenerativeAI(model="gemini-pro",temperature=0)
memory= ConversationBufferWindowMemory(memory_key="history",input_key="question", return_messages=True, k=5)


prompt_template = """You are a Question-Answering (QA) system designed to assist users by providing information relevant to the context provided. For lawyers, this context will include case files they submit. For general queries, the context will be derived from a preceding conversation.

Instructions:
1. Review the chat history and any provided context related to a case or general inquiry.
2. For each follow-up question, determine if it relates to the previous context:
   - If related, rephrase the follow-up question into a standalone question and answer it without altering its content.
   - If not related, answer the question directly.
3. If the answer to a question is unknown, state 'I do not know. Please specify the document.' Do not fabricate answers.
4. Please do not rephrase the question and give it as an answer 



Contextual Information for Lawyers:
{context}

Chat History:
{history}

Current Question:
{question}

Your Task:
Provide a helpful and accurate answer based on the context and chat history."""
qa_prompt = PromptTemplate(
    template=prompt_template, input_variables=["history","context", "question"]
)

def create_chain(prompt):
    chain =  LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory
        )
        
        
    
    return chain


def load_case_files(base_path, selected_case):
    # Construct the full path to the case directory
    case_path = os.path.join(base_path, selected_case)

    # Dictionary to hold the contents of each file, keyed by the first word of the file name
    case_files_content = {}

    # List PDF files in the directory
    for file_name in os.listdir(case_path):
        if file_name.endswith('.pdf'):
            # Extract the first word of the file name as the key
            key = file_name.split()[0]

            # Path to the PDF file
            file_path = os.path.join(case_path, file_name)

            # Read the PDF file content
            try:
                pdf_reader = PdfReader(file_path)
                text_content = []
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
                # Store the concatenated text of all pages under the key
                case_files_content[key] = "\n".join(text_content)
            except Exception as e:
                print(f"Failed to read {file_name}: {e}")

    return case_files_content

def find_sentiment(query,lst):
    prompt_template= PromptTemplate.from_template(
            
            template="""{query} is a question for which you need to identify which of the following document  might contain the answer:

                       {lst}

                     Ensure that your response corresponds to any one of these categories.
                     For example when the question is about someones identity then the aswer for it will be in Witness list,Similarly  a breif of case or financial information would be in discovery and finance statement file respectivily"""
        )
    chain=LLMChain(llm=llm,prompt=prompt_template)
    sentiment=chain.run({"query":query,"lst":lst})
    print(sentiment)
    return sentiment
# # history=[]
def query_answer(query,selected_case):
    
        
        dic=load_case_files(case,selected_case)
        lst=dic.keys()
        print(lst)
        sentiment = find_sentiment(query,lst)
        chain = create_chain(qa_prompt)
        
        # Determine the context based on the sentiment
        context=dic[sentiment]

        # Run the chain with the appropriate context
        answer = chain.run({"context": context, "question": query})
        
        return answer
def bot(ques,selected_case):
    
    ans=query_answer(ques,selected_case)
    return ans
def summarization(case_name):
    # case_name=request.case_name
    context=load_case_files(case,case_name)
    template="""Create a structured report of a legal case using the provided {context}. If information for any point is not available, do not fabricate content. Simply state 'Information not available.' 

        Guidelines for the Report:
        1. Case Title and Citation: Include the full name of the case and its citation.
        2. Jurisdiction: Specify the jurisdiction where the case was adjudicated.
        3. Date: Provide the date of the ruling.
        4. Parties Involved: List the main parties in the case.
        5. Facts of the Case: Briefly summarize the key facts that led to the legal dispute.
        6. Issues: Describe the main legal issues addressed by the court.
        7. Rulings: Summarize the court's decisions on the issues.
        8. Reasoning: Explain the rationale behind the court's decisions.
        9. Legal Principles/Precedents Applied: Note any significant legal principles or precedents that were applied.
        10. Outcome and Remedies: Outline the outcome of the case and any remedies ordered by the court.
        11. Dissenting Opinions: Summarize any dissenting opinions, if available.
        12. Impact and Significance: Discuss the broader impact of the case, including any implications for future legal interpretations or law changes.
        Follow the above points to generate the report."""
    prompt = PromptTemplate(
    template=template, input_variables=["context"]
)
    chain =  LLMChain(
        llm=llm,
        prompt=prompt
        
        )
    report=chain.run({"context":context})   
    
    return report
   