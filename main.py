from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from PyPDF2 import PdfReader
import io
import json
import os

app = FastAPI()

openai_key = os.environ.get("OPENAI_API_KEY")


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        reader = PdfReader(io.BytesIO(contents))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        llm = ChatOpenAI(api_key=openai_key, model="gpt-3.5-turbo")


        summary_prompt = PromptTemplate.from_template(
            "Summarize the following study material:\n\n{notes}"
        )
        summary_chain = LLMChain(llm=llm, prompt=summary_prompt)
        summary = summary_chain.invoke({"notes": text})["text"]


        plan_prompt = PromptTemplate.from_template(
            "Generate a 3-day personalized study plan for this content:\n\n{notes}"
        )
        plan_chain = LLMChain(llm=llm, prompt=plan_prompt)
        plan_raw = plan_chain.invoke({"notes": text})["text"]
        study_plan = [line for line in plan_raw.strip().split("\n") if line.strip()]


        question_prompt = PromptTemplate.from_template(
            "Based on the text below, generate one thoughtful quiz question:\n\n{notes}"
        )
        question_chain = LLMChain(llm=llm, prompt=question_prompt)
        starter_question = question_chain.invoke({"notes": text})["text"].strip()

        return {
            "filename": file.filename,
            "summary": summary,
            "study_plan": study_plan,
            "starter_question": starter_question
        }

    except Exception as e:
        return {
            "filename": None,
            "summary": "",
            "study_plan": [],
            "starter_question": "",
            "error": str(e)
        }


class AnswerRequest(BaseModel):
    context: str
    question: str
    answer: str
    model: str = "gpt-3.5-turbo"

@app.post("/check_answer")
def check_answer(req: AnswerRequest):
    llm = ChatOpenAI(api_key=openai_key, model=req.model)

    if req.answer == "N/A":
        prompt = f"{req.question}"
        response = llm.invoke(prompt)
        return {"feedback": response.content.strip()}

  
    prompt = (
        f"Here is the context:\n{req.context}\n\n"
        f"Question: {req.question}\n"
        f"User's answer: {req.answer}\n"
        f"Evaluate the answer briefly. Is it correct? Give feedback in 1-2 lines."
    )
    response = llm.invoke(prompt)
    return {"feedback": response.content.strip()}
