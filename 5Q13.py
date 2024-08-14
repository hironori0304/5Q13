import pandas as pd
import streamlit as st
import io
import random
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
from datetime import datetime
import pytz
import textwrap

def load_quiz_data(file):
    with io.TextIOWrapper(file, encoding='utf-8', errors='replace') as f:
        df = pd.read_csv(f)
    return df

def filter_and_sort_quiz_data(df, selected_years, selected_categories):
    if "すべて" in selected_years:
        selected_years = df['year'].unique().tolist()
    if "すべて" in selected_categories:
        selected_categories = df['category'].unique().tolist()
    
    filtered_df = df[df['year'].isin(selected_years) & df['category'].isin(selected_categories)]
    
    sorted_quizzes = []
    for category in selected_categories:
        category_df = filtered_df[filtered_df['category'] == category]
        for year in selected_years:
            year_df = category_df[category_df['year'] == year]
            sorted_quizzes.extend(year_df.to_dict('records'))
    
    quiz_data = []
    for quiz in sorted_quizzes:
        options = [quiz["option1"], quiz["option2"], quiz["option3"], quiz["option4"], quiz["option5"]]
        correct_option = quiz["answer"]
        shuffled_options = options[:]
        random.shuffle(shuffled_options)
        
        quiz_data.append({
            "question": quiz["question"],
            "options": shuffled_options,
            "correct_option": correct_option
        })
    
    return quiz_data

def generate_certificate(name, selected_years, selected_categories, score, total_questions):
    jst = pytz.timezone('Asia/Tokyo')
    current_datetime = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")
    accuracy_rate = (score / total_questions) * 100
    
    # フォント設定（日本語対応）
    font_path = "./msgothic.ttc"  # 使用するフォントファイルのパス
    font_prop = fm.FontProperties(fname=font_path)
    
    # A4の半分サイズ (8.27 x 5.85 インチ)
    plt.figure(figsize=(8.27, 5.85))
    plt.subplots_adjust(top=0.9)  # 上部のマージン調整

    def wrap_text(text, width=30):
        return textwrap.fill(text, width=width)

    # "証明書"を中央に配置
    plt.text(0.5, 0.95, "成績証明書", fontsize=24, ha='center', va='top', fontproperties=font_prop)

    plt.text(0.05, 0.85, wrap_text(f"氏名: {name}"), fontsize=14, ha='left', va='top', fontproperties=font_prop)
    plt.text(0.05, 0.75, wrap_text(f"日時: {current_datetime}"), fontsize=12, ha='left', va='top', fontproperties=font_prop)
    
    years_str = "、".join(selected_years) if selected_years else "選択なし"
    categories_str = "、".join(selected_categories) if selected_categories else "選択なし"
    
    plt.text(0.05, 0.65, wrap_text(f"問題: {years_str}"), fontsize=12, ha='left', va='top', fontproperties=font_prop)
    plt.text(0.05, 0.55, wrap_text(f"分野: {categories_str}"), fontsize=12, ha='left', va='top', fontproperties=font_prop)
    
    plt.text(0.05, 0.45, wrap_text(f"スコア: {score} / {total_questions}"), fontsize=14, ha='left', va='top', fontproperties=font_prop)
    plt.text(0.05, 0.35, wrap_text(f"正答率: {accuracy_rate:.2f}%"), fontsize=14, ha='left', va='top', fontproperties=font_prop)
    
    plt.axis('off')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    
    return buffer

def main():
    st.title("国家試験対策アプリ")

    # セッションステートの初期化
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "current_quiz_data" not in st.session_state:
        st.session_state.current_quiz_data = []
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "shuffled_options" not in st.session_state:
        st.session_state.shuffled_options = {}
    if "highlighted_questions" not in st.session_state:
        st.session_state.highlighted_questions = set()
    if "submit_count" not in st.session_state:
        st.session_state.submit_count = 0
    if "certificate_generated" not in st.session_state:
        st.session_state.certificate_generated = False
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "name" not in st.session_state:
        st.session_state.name = ""

    # ファイルアップローダー
    uploaded_file = st.file_uploader("問題データのCSVファイルをアップロードしてください", type="csv")
    if uploaded_file is not None:
        try:
            df = load_quiz_data(uploaded_file)
            years = df['year'].unique().tolist()
            categories = df['category'].unique().tolist()

            years.insert(0, "すべて")
            categories.insert(0, "すべて")

            selected_years = st.multiselect("過去問の回数を選択してください", years)
            selected_categories = st.multiselect("分野を選択してください", categories)

            if selected_years and selected_categories:
                st.session_state.quiz_data = filter_and_sort_quiz_data(df, selected_years, selected_categories)
                st.session_state.current_quiz_data = st.session_state.quiz_data.copy()
                st.session_state.answers = {quiz["question"]: None for quiz in st.session_state.current_quiz_data}
                
                if st.session_state.current_quiz_data:
                    st.write("問題を回答してください。")

                    for i, quiz in enumerate(st.session_state.current_quiz_data):
                        question_number = i + 1
                        is_highlighted = question_number in st.session_state.highlighted_questions
                        highlight_style = "background-color: #ffcccc;" if is_highlighted else ""

                        st.markdown(f"**<div style='padding: 10px; {highlight_style} font-size: 16px;'>問題 {question_number}</div>**", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin-bottom: 0; font-size: 16px;'>{quiz['question']}</p>", unsafe_allow_html=True)

                        if quiz["question"] not in st.session_state.shuffled_options:
                            st.session_state.shuffled_options[quiz["question"]] = quiz["options"]
                        
                        options = st.session_state.shuffled_options[quiz["question"]]

                        selected_option = st.radio(
                            "",
                            options=options,
                            index=st.session_state.answers.get(quiz["question"], None),
                            key=f"question_{i}_radio"
                        )

                        if selected_option is not None:
                            st.session_state.answers[quiz["question"]] = selected_option

                        st.write("")  # 次の問題との間にスペースを追加

                    name = st.text_input("氏名を入力してください", value=st.session_state.get("name", ""))
                    if st.button("回答"):
                        if name:
                            st.session_state.name = name
                            score = 0
                            total_questions = len(st.session_state.quiz_data)
                            incorrect_data = []
                            for i, quiz in enumerate(st.session_state.current_quiz_data):
                                correct_option = quiz["correct_option"]
                                selected_option = st.session_state.answers.get(quiz["question"], None)

                                is_correct = correct_option == selected_option

                                if is_correct:
                                    score += 1
                                    st.session_state.highlighted_questions.discard(i + 1)
                                else:
                                    incorrect_data.append(quiz)
                                    st.session_state.highlighted_questions.add(i + 1)

                            accuracy_rate = (score / total_questions) * 100
                            st.write(f"あなたのスコア: {score} / {total_questions}")
                            st.write(f"正答率: {accuracy_rate:.2f}%")

                            st.session_state.incorrect_data = incorrect_data
                            st.session_state.score = score
                            st.session_state.submit_count += 1

                            st.session_state.certificate_generated = True
                            
                            st.success("回答が完了しました。成績証明書を表示します。")
                            
                            buffer = generate_certificate(name, selected_years, selected_categories, st.session_state.score, total_questions)
                            st.image(buffer, use_column_width=True)
                            st.download_button("証明書をダウンロード", buffer, file_name="certificate.png", mime="image/png")
                        else:
                            st.error("氏名を入力してください。")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
