import pandas as pd
import streamlit as st
import io
import random
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.font_manager as fm
import tempfile
import pytz  # タイムゾーン管理のためのライブラリ

# クイズデータの読み込み
def load_quiz_data(file):
    """CSVファイルからクイズデータを読み込む関数"""
    try:
        with io.TextIOWrapper(file, encoding='utf-8', errors='replace') as f:
            df = pd.read_csv(f)
        return df
    except Exception as e:
        st.error(f"ファイルの読み込みに失敗しました: {e}")
        return None

# データのフィルタリングとソート
def filter_and_sort_quiz_data(df, selected_years, selected_categories):
    """選択された過去問の回数と分野に基づいてデータをフィルタリングし、ソートする関数"""
    try:
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
    except Exception as e:
        st.error(f"データのフィルタリングとソートに失敗しました: {e}")
        return []

# 証明書の生成
def generate_certificate(name, selected_years, selected_categories, correct_answers_count, total_questions):
    """証明書を生成する関数"""
    try:
        fig, ax = plt.subplots(figsize=(8.3, 5.8))  # A4の半分のサイズ

        # フォント設定（日本語対応）
        font_path = "./msgothic.ttc"  # 使用するフォントファイルのパス
        font_prop = fm.FontProperties(fname=font_path)

        # 日本時間 (Tokyo) に設定
        jst = pytz.timezone('Asia/Tokyo')
        current_time = datetime.now(jst)  # JSTで現在の日時を取得

        ax.axis('off')

        text = (
            f"氏名: {name}\n\n"
            f"日時: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"問題の回数: {', '.join(selected_years)}\n\n"
            f"分野: {', '.join(selected_categories)}\n\n"
            f"正答数: {correct_answers_count} / {total_questions}\n\n"
            f"スコア: {correct_answers_count / total_questions * 100:.2f}%"
        )

        ax.text(0.5, 0.9, "証明書", fontsize=24, ha='center', va='center', fontproperties=font_prop, weight='bold')
        ax.text(0.1, 0.5, text, fontsize=16, ha='left', va='top', fontproperties=font_prop, wrap=True)

        timestamp = current_time.strftime('%Y%m%d_%H%M%S')
        file_name = f"証明書_{timestamp}.png"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png", prefix="certificate_")
        plt.savefig(temp_file.name, bbox_inches='tight', pad_inches=1)
        plt.close(fig)

        return temp_file.name, file_name
    except Exception as e:
        st.error(f"証明書の生成に失敗しました: {e}")
        return None, None

def main():
    st.title("国家試験対策アプリ")

    # セッション状態の初期化
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "incorrect_data" not in st.session_state:
        st.session_state.incorrect_data = []
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
    if "name" not in st.session_state:
        st.session_state.name = ""
    if "show_result" not in st.session_state:
        st.session_state.show_result = False
    if "correct_answers_count" not in st.session_state:
        st.session_state.correct_answers_count = 0
    if "total_questions" not in st.session_state:
        st.session_state.total_questions = 0

   # 問題データのアップロード
    uploaded_file = st.file_uploader("問題データのCSVファイルをアップロードしてください", type="csv")
    if uploaded_file is not None:
        df = load_quiz_data(uploaded_file)
        if df is not None:
            years = df['year'].unique().tolist()
            categories = df['category'].unique().tolist()

            years.insert(0, "すべて")
            categories.insert(0, "すべて")

            # 過去問の回数と分野の選択
            selected_years = st.multiselect("過去問の回数を選択してください", years)
            selected_categories = st.multiselect("分野を選択してください", categories)

            if selected_years and selected_categories:
                st.session_state.quiz_data = filter_and_sort_quiz_data(df, selected_years, selected_categories)
                st.session_state.current_quiz_data = st.session_state.quiz_data.copy()
                st.session_state.answers = {quiz["question"]: None for quiz in st.session_state.current_quiz_data}

                if st.session_state.current_quiz_data:
                    # 問題の表示
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

                    # 回答ボタン
                    if st.button("回答"):
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
                        st.session_state.score = score
                        st.session_state.accuracy_rate = accuracy_rate

                        st.write(f"あなたのスコア: {score} / {total_questions}")
                        st.write(f"正答率: {accuracy_rate:.2f}%")

                        # 結果を表示するフラグを立てる
                        st.session_state.show_result = True
                        
        if st.session_state.show_result:
                    # 氏名の入力フィールドと証明書発行ボタンを表示
                    st.session_state.name = st.text_input("氏名を入力してください", value=st.session_state.name)

      
        if st.button("証明書を発行"):
                            certificate_path, file_name = generate_certificate(
                                st.session_state.name,
                                selected_years,
                                selected_categories,
                                st.session_state.score,
                                st.session_state.accuracy_rate
                            )
                            if certificate_path:
                                st.image(certificate_path)

                                # ダウンロードボタンの表示
                                with open(certificate_path, "rb") as file:
                                    st.download_button(
                                        label="証明書をダウンロード",
                                        data=file,
                                        file_name=file_name,
                                        mime="image/png"
                                    )

if __name__ == "__main__":
    main()