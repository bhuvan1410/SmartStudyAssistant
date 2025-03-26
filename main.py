
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json

app = FastAPI()

OPENAI_API_KEY = "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"

class StudyRequest(BaseModel):
    notes: str
    model: str = "gpt-3.5-turbo"
    num_questions: int = 3

@app.post("/study")
def process_notes(req: StudyRequest):
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=req.model)

    summary_prompt = PromptTemplate.from_template(
        "Summarize the following study material in a concise and clear way:\n\n{notes}"
    )
    summary_chain = LLMChain(llm=llm, prompt=summary_prompt)

    quiz_prompt = PromptTemplate.from_template(
        """
        Create {num_questions} multiple-choice quiz questions based on the text below.

        For each question, return JSON in the format:
        {{
          "question": "...",
          "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
          "answer": "B"
        }}

        Only return a list of questions as a valid JSON array — no explanation or extra text.

        Study material:
        {notes}
        """
    )
    quiz_chain = LLMChain(llm=llm, prompt=quiz_prompt)

    summary = summary_chain.invoke({"notes": req.notes})
    quiz = quiz_chain.invoke({"notes": req.notes, "num_questions": req.num_questions})

    try:
        quiz_data = json.loads(quiz["text"])
    except Exception as e:
        print("❌ Failed to parse quiz JSON:", e)
        quiz_data = []

    return {
        "summary": summary["text"],
        "quiz": quiz_data
    }

class ExplainRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"

@app.post("/explain")
def explain_answer(req: ExplainRequest):
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=req.model)
    response = llm.invoke(req.prompt)
    return {"explanation": response.content}
