import os
import json
import random
import time

import streamlit as st
from dotenv import load_dotenv
from google import genai
from streamlit_autorefresh import st_autorefresh


# --------------------------------------------------
# LOAD API KEY
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key is missing. Please check your .env file.")
    st.stop()


# --------------------------------------------------
# GEMINI CLIENT
# --------------------------------------------------

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="centered"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "quiz" not in st.session_state:
    st.session_state.quiz = []

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "answers" not in st.session_state:
    st.session_state.answers = []

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if "quiz_finished" not in st.session_state:
    st.session_state.quiz_finished = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "time_limit" not in st.session_state:
    st.session_state.time_limit = 30

if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None


# --------------------------------------------------
# RESTART FUNCTION
# --------------------------------------------------

def restart_quiz():
    st.session_state.quiz = []
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.quiz_started = False
    st.session_state.quiz_finished = False
    st.session_state.start_time = None
    st.session_state.selected_answer = None


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🧠 AI Quiz Generator")

st.write(
    "Generate an AI-powered multiple-choice quiz "
    "from any topic and test your knowledge."
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Quiz Settings")

    difficulty = st.selectbox(
        "Quiz Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    category = st.selectbox(
        "Subject / Category",
        [
            "General Knowledge",
            "Python Programming",
            "Artificial Intelligence",
            "Machine Learning",
            "Web Development",
            "Generative AI",
            "Computer Science"
        ]
    )

    timer_per_question = st.selectbox(
        "Timer per Question",
        [15, 30, 60],
        index=1
    )

    st.write("⏱️ Time per question:", timer_per_question, "seconds")


# --------------------------------------------------
# INPUT AREA
# --------------------------------------------------

topic = st.text_input(
    "Enter Quiz Topic",
    placeholder="e.g. Python Programming"
)

number_of_questions = st.number_input(
    "Number of Questions",
    min_value=1,
    max_value=20,
    value=5,
    step=1
)


# --------------------------------------------------
# GENERATE QUIZ
# --------------------------------------------------

if st.button("🎯 Generate Quiz"):

    if not topic.strip():

        st.warning("Please enter a topic first.")

    else:

        prompt = f"""
You are an expert educational quiz generator.

Create exactly {number_of_questions} multiple-choice questions.

Topic:
{topic}

Category:
{category}

Difficulty:
{difficulty}

Requirements:

1. Generate exactly {number_of_questions} questions.
2. Each question must have exactly four options.
3. Options must be A, B, C, and D.
4. Each question must have one correct answer.
5. Questions must be relevant to the topic.
6. Questions must match the selected difficulty.
7. Make the questions clear and educational.
8. Return ONLY valid JSON.
9. Do not include markdown or explanations outside the JSON.

Use exactly this JSON structure:

[
    {{
        "question": "Question text",
        "options": [
            "Option A",
            "Option B",
            "Option C",
            "Option D"
        ],
        "answer": "Option A"
    }}
]
"""

        try:

            with st.spinner("🤖 Generating your quiz..."):

                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt
                )

            quiz_text = response.text.strip()

            if quiz_text.startswith("```"):
                quiz_text = quiz_text.replace("```json", "")
                quiz_text = quiz_text.replace("```", "")
                quiz_text = quiz_text.strip()

            quiz_data = json.loads(quiz_text)

            # Randomize questions
            random.shuffle(quiz_data)

            st.session_state.quiz = quiz_data
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.answers = []
            st.session_state.quiz_started = True
            st.session_state.quiz_finished = False
            st.session_state.start_time = time.time()
            st.session_state.time_limit = timer_per_question
            st.session_state.selected_answer = None

            st.rerun()

        except json.JSONDecodeError:

            st.error(
                "The AI returned an unexpected format. "
                "Please click Generate Quiz again."
            )

        except Exception as e:

            st.error(
                f"Something went wrong while generating the quiz: {e}"
            )


# --------------------------------------------------
# QUIZ DISPLAY
# --------------------------------------------------

if st.session_state.quiz_started and not st.session_state.quiz_finished:

    quiz = st.session_state.quiz

    current_index = st.session_state.current_question

    total_questions = len(quiz)

    # TIMER

    elapsed_time = time.time() - st.session_state.start_time

    remaining_time = (
        st.session_state.time_limit - int(elapsed_time)
    )

    st_autorefresh(
        interval=1000,
        key="quiz_timer"
    )

    if remaining_time <= 0:

        st.warning("⏰ Time is up!")

        st.session_state.quiz_finished = True

        st.rerun()

    else:

        st.info(
            f"⏱️ Time remaining: {remaining_time} seconds"
        )

    # PROGRESS

    st.progress(
        (current_index + 1) / total_questions
    )

    st.subheader(
        f"Question {current_index + 1} of {total_questions}"
    )

    # CURRENT QUESTION

    question_data = quiz[current_index]

    st.write(
        f"### {question_data['question']}"
    )

    selected_answer = st.radio(
        "Select your answer:",
        question_data["options"],
        key=f"question_{current_index}"
    )

    # NEXT QUESTION

    if current_index < total_questions - 1:

        if st.button("➡️ Next Question"):

            correct_answer = question_data["answer"]

            if selected_answer == correct_answer:
                st.session_state.score += 1

            st.session_state.answers.append(
                {
                    "question": question_data["question"],
                    "selected": selected_answer,
                    "correct": correct_answer
                }
            )

            st.session_state.current_question += 1

            st.session_state.start_time = time.time()

            st.rerun()

    else:

        if st.button("🏁 Finish Quiz"):

            correct_answer = question_data["answer"]

            if selected_answer == correct_answer:
                st.session_state.score += 1

            st.session_state.answers.append(
                {
                    "question": question_data["question"],
                    "selected": selected_answer,
                    "correct": correct_answer
                }
            )

            st.session_state.quiz_finished = True

            st.rerun()


# --------------------------------------------------
# FINAL SCORE
# --------------------------------------------------

if st.session_state.quiz_finished:

    total = len(st.session_state.quiz)

    score = st.session_state.score

    st.success("🎉 Quiz Completed!")

    st.header("🏆 Final Score")

    st.metric(
        "Your Score",
        f"{score} / {total}"
    )

    percentage = (score / total) * 100

    st.write(
        f"### Percentage: {percentage:.1f}%"
    )

    if percentage >= 80:

        st.success("🌟 Excellent work!")

    elif percentage >= 60:

        st.info("👍 Good job! Keep practicing.")

    else:

        st.warning("📚 Keep practicing and try again!")

    # ANSWER REVIEW

    st.subheader("📋 Answer Review")

    for index, answer in enumerate(
        st.session_state.answers,
        start=1
    ):

        st.write(
            f"**Q{index}. {answer['question']}**"
        )

        st.write(
            f"Your answer: {answer['selected']}"
        )

        st.write(
            f"Correct answer: {answer['correct']}"
        )

        st.divider()

    # DOWNLOAD QUIZ

    download_text = "AI QUIZ GENERATOR\n\n"

    download_text += f"Topic: {topic}\n"
    download_text += f"Category: {category}\n"
    download_text += f"Difficulty: {difficulty}\n\n"

    download_text += (
        f"Final Score: {score}/{total}\n"
    )

    download_text += (
        f"Percentage: {percentage:.1f}%\n\n"
    )

    download_text += "QUESTIONS AND ANSWERS\n\n"

    for index, item in enumerate(
        st.session_state.quiz,
        start=1
    ):

        download_text += (
            f"Question {index}: "
            f"{item['question']}\n"
        )

        for option_index, option in enumerate(
            item["options"]
        ):

            letter = chr(65 + option_index)

            download_text += (
                f"{letter}. {option}\n"
            )

        download_text += (
            f"Correct Answer: "
            f"{item['answer']}\n\n"
        )

    st.download_button(
        label="📥 Download Quiz",
        data=download_text,
        file_name="ai_quiz.txt",
        mime="text/plain"
    )

    # RESTART QUIZ

    if st.button("🔄 Restart Quiz"):

        restart_quiz()

        st.rerun()