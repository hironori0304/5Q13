import pandas as pd
import streamlit as st
import io
import random
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.font_manager as fm
import pytz

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

# 成績証明書の生成
def generate_certificate(name, selected_years, selected_categories, correct_answers_count, total_questions):
    """成績証明書を生成する関数"""
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
            f"実施日時: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"選択した問題: {', '.join(selected_years)}\n\n"
            f"選択した分野: {', '.join(selected_categories)}\n\n"
            f"正答数: {correct_answers_count} / {total_questions}\n\n"
            f"正答率: {correct_answers_count / total_questions * 100:.2f}%"
        )

        ax.text(0.5, 0.9, "成績証明書", fontsize=24, ha='center', va='center', fontproperties=font_prop, weight='bold')
        ax.text(0.1, 0.5, text, fontsize=16, ha='left', va='top', fontproperties=font_prop)

        timestamp = current_time.strftime('%Y%m%d_%H%M%S')
        file_name = f"成績証明書_{timestamp}.png"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png", prefix="certificate_")
        plt.savefig(temp_file.name, bbox_inches='tight', pad_inches=1)
        plt.close(fig)

        return temp_file.name, file_name
    except Exception as e:
        st.error(f"成績証明書の生成に失敗しました: {e}")
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
    if "certificate_path" not in st.session_state:
        st.session_state.certificate_path = None

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
                        st.write(f"**問題 {i+1}:** {quiz['question']}")

                        options = quiz["options"]
                        selected_option = st.radio(
                            f"選択肢を選んでください:", options, key=f"question_{i}")

                        # 選択された解答をセッションに保存
                        if selected_option:
                            st.session_state.answers[quiz['question']] = selected_option

                    # 氏名の入力
                    name = st.text_input("氏名を入力してください", st.session_state.name)

                    # 解答の提出ボタン
                    if st.button("解答を提出する"):
                        if name:
                            st.session_state.name = name
                            st.session_state.submit_count += 1
                            st.session_state.correct_answers_count = 0
                            st.session_state.total_questions = len(st.session_state.current_quiz_data)

                            incorrect_questions = []

                            for i, quiz in enumerate(st.session_state.current_quiz_data):
                                selected_option = st.session_state.answers[quiz['question']]
                                correct_option = quiz["correct_option"]

                                if selected_option == correct_option:
                                    st.session_state.correct_answers_count += 1
                                else:
                                    incorrect_questions.append(quiz)

                            st.session_state.incorrect_data = incorrect_questions
                            st.session_state.show_result = True

                            # 成績証明書の生成
                            cert_path, cert_file_name = generate_certificate(
                                name, selected_years, selected_categories,
                                st.session_state.correct_answers_count, st.session_state.total_questions)

                            if cert_path:
                                st.session_state.certificate_path = cert_path
                                st.success(f"成績証明書が生成されました: {cert_file_name}")
                                with open(cert_path, "rb") as file:
                                    st.download_button(label="成績証明書をダウンロード", data=file, file_name=cert_file_name, mime="image/png")
                        else:
                            st.error("氏名を入力してください。")

                # 解答結果の表示
                    if st.session_state.show_result:
                        st.write(f"正答数: {st.session_state.correct_answers_count} / {st.session_state.total_questions}")
                        st.write(f"正答率: {st.session_state.correct_answers_count / st.session_state.total_questions * 100:.2f}%")

                        # 不正解の問題を表示
                        if st.session_state.incorrect_data:
                            st.write("不正解の問題:")
                            for i, quiz in enumerate(st.session_state.incorrect_data):
                                st.write(f"**問題 {i+1}:** {quiz['question']}")
                                st.write(f"正解: {quiz['correct_option']}")
                                st.write(f"選択した解答: {st.session_state.answers[quiz['question']]}")

                        # 成績証明書の表示
                        if st.session_state.certificate_path:
                            st.image(st.session_state.certificate_path, use_column_width=True)

if __name__ == "__main__":
    main()
