import streamlit as st
import requests
import time
import datetime

st.set_page_config(page_title=" Smart Study Assistant", layout="centered")
st.title(" Smart Study Assistant")


if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "score_history" not in st.session_state:
    st.session_state.score_history = []
if "submitted_answer" not in st.session_state:
    st.session_state.submitted_answer = False
if "last_question" not in st.session_state:
    st.session_state.last_question = None
if "last_selected" not in st.session_state:
    st.session_state.last_selected = ""
if "last_correct" not in st.session_state:
    st.session_state.last_correct = ""

# --- Input form ---
with st.form("study_form"):
    notes = st.text_area("📝 Paste your study notes:", height=300)
    model = st.selectbox("🤖 Choose the model:", ["gpt-3.5-turbo", "gpt-4"])
    num_questions = st.slider("❓ How many questions?", 1, 10, 3)
    submitted = st.form_submit_button("📚 Generate Summary & Quiz")

if submitted:
    if not notes.strip():
        st.warning("Please enter your study notes.")
    else:
        with st.spinner("Analyzing and generating quiz..."):
            res = requests.post("http://localhost:8000/study", json={
                "notes": notes,
                "model": model,
                "num_questions": num_questions
            })

            if res.status_code == 200:
                data = res.json()
                st.session_state.summary = data["summary"]
                st.session_state.quiz_data = data["quiz"]
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.session_state.quiz_active = True
                st.session_state.submitted_answer = False
                st.success("Ready to study!")
            else:
                st.error("Something went wrong.")


if st.session_state.get("summary"):
    st.subheader(" Summary:")
    st.write(st.session_state.summary)


if st.session_state.quiz_active and st.session_state.quiz_data:
    quiz = st.session_state.quiz_data
    q_num = st.session_state.current_q

    if q_num < len(quiz):
        st.subheader(f" Quiz Question: {q_num + 1}")
        q = quiz[q_num]
        st.write(q["question"])

        answer = st.radio("Choose your answer:", q["choices"], key=q_num)

        if not st.session_state.submitted_answer:
            if st.button("Submit Answer"):
                correct = q["answer"].strip().upper()
                selected = answer[0].strip().upper()

                st.session_state.submitted_answer = True
                st.session_state.last_question = q
                st.session_state.last_selected = selected
                st.session_state.last_correct = correct

                if selected == correct:
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Incorrect. Correct answer: {correct}")

        # 💡 Explain after submission
        if st.session_state.submitted_answer:
            if st.button("💡 Explain this answer"):
                with st.spinner("GPT is explaining..."):
                    explain_prompt = f"""
                    Explain why this is the correct answer:

                    Question: {q['question']}
                    Choices: {', '.join(q['choices'])}
                    Correct Answer: {q['answer']}
                    """
                    response = requests.post("http://localhost:8000/explain", json={
                        "prompt": explain_prompt,
                        "model": model
                    })
                    if response.status_code == 200:
                        explanation = response.json()["explanation"]
                        st.info(explanation)
                    else:
                        st.warning("Could not fetch explanation.")

            if st.button("➡️ Next Question"):
                st.session_state.current_q += 1
                st.session_state.submitted_answer = False
                st.rerun()

    else:

        st.success("🎉 Quiz completed!")
        st.write(f"Your score: {st.session_state.score} / {len(quiz)}")

        today = datetime.datetime.now().strftime("%b %d, %Y %I:%M %p")
        score_entry = {
            "date": today,
            "score": st.session_state.score,
            "total": len(quiz)
        }
        if score_entry not in st.session_state.score_history:
            st.session_state.score_history.append(score_entry)

        st.subheader("📈 Past Quiz Scores")
        for entry in st.session_state.score_history[-5:][::-1]:
            st.markdown(f"- {entry['date']}: **{entry['score']} / {entry['total']}**")

        if st.button("🔁 Start Over"):
            st.session_state.quiz_active = False
            st.session_state.quiz_data = []
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.summary = ""
            st.session_state.submitted_answer = False
            st.rerun()
else:
    st.info("⬆️ Paste notes above and generate quiz to begin!")
