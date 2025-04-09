import streamlit as st
import requests
import uuid


st.set_page_config(page_title="Smart Study Assistant", layout="wide")
st.title("Smart Study Assistant")

backend_url = "https://fastapi-backend-819039865212.us-central1.run.app"


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.filename = None
    st.session_state.summary = None
    st.session_state.study_plan = []
    st.session_state.starter_question = None
    st.session_state.user_answers = []
    st.session_state.feedback = None
    st.session_state.summary_loaded = False


with st.sidebar:
    st.header("Upload your study material (PDF)")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file and not st.session_state.summary_loaded:
        with st.spinner("Processing PDF and generating plan/answering question..."):
            try:
                res = requests.post(
                    f"{backend_url}/upload_pdf",
                    files={"file": (uploaded_file.name, uploaded_file, "application/pdf")},
                    timeout=20
                )
                data = res.json()
                if "filename" in data:
                    st.session_state.filename = data["filename"]
                    st.session_state.summary = data["summary"]
                    st.session_state.study_plan = data["study_plan"]
                    st.session_state.starter_question = data["starter_question"]
                    st.session_state.user_answers = []
                    st.session_state.feedback = None
                    st.session_state.summary_loaded = True  
                    st.success("✅ PDF processed successfully!")
                else:
                    st.error("Unexpected backend response.")
            except Exception as e:
                st.error(f"Upload failed: {e}")


if st.session_state.summary:
    st.subheader("📄 Summary")
    st.write(st.session_state.summary)

    st.subheader("🗓️ Personalized Study Plan")
    for day in st.session_state.study_plan:
        st.write(f"• {day}")

    st.markdown("---")


if st.session_state.starter_question:
    st.subheader("AI Sample Question")
    st.write(f"**{st.session_state.starter_question}**")

    user_answer = st.text_input("Your Answer:", key="answer_input")

    if st.button("Submit Answer"):
        st.session_state.pending_question_check = {
            "question": st.session_state.starter_question,
            "answer": user_answer
        }
        st.rerun()


if "pending_question_check" in st.session_state:
    data = st.session_state.pending_question_check
    res = requests.post(f"{backend_url}/check_answer", json={
        "context": st.session_state.summary,
        "question": data["question"],
        "answer": data["answer"]
    })

    if res.status_code == 200:
        feedback = res.json().get("feedback", "")
        st.session_state.user_answers.append((data["question"], data["answer"], feedback))
        st.session_state.feedback = feedback
    else:
        st.session_state.feedback = "Error processing answer."

    del st.session_state.pending_question_check
    st.rerun()


if st.session_state.feedback:
    st.success("✅ Feedback:")
    st.write(st.session_state.feedback)

    st.markdown("---")
    st.markdown("### ➕ What would you like to do next?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Get Another Quiz Question?"):
            followup_prompt = f"Based on this study material, give another thoughtful quiz question:\n\n{st.session_state.summary}"
            res = requests.post(f"{backend_url}/check_answer", json={
                "context": st.session_state.summary,
                "question": followup_prompt,
                "answer": "N/A"
            })

            if res.status_code == 200:
                new_q = res.json()["feedback"]
                st.session_state.starter_question = new_q
                st.session_state.feedback = None
                st.rerun()

    with col2:
        custom_q = st.text_input("💬 Ask a custom question about the PDF", key="custom_input")
        if st.button("Ask"):
            try:
                res = requests.post(f"{backend_url}/check_answer", json={
                    "context": st.session_state.summary,
                    "question": custom_q,
                    "answer": "N/A"
                })
                if res.status_code == 200:
                    answer = res.json().get("feedback", "")
                    st.markdown("### Answer:")
                    st.write(answer)
            except Exception as e:
                st.error(f"Error asking question: {e}")


if st.session_state.user_answers:
    st.markdown("### 📝 Answer History")
    for i, (q, a, f) in enumerate(st.session_state.user_answers):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"**Your answer:** {a}")
        st.markdown(f"**Feedback:** {f}")
        st.markdown("---")
