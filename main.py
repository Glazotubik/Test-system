# /home/maksim/Документы/DMA/fap_test_system/main.py
import streamlit as st
import random
import sys
import os
import time
from datetime import datetime
from fpdf import FPDF

# Добавляем путь для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from theme_loader import scan_themes, get_categories_for_theme

# Настройка страницы
st.set_page_config(
    page_title="Тесты по ФАП - Модульная версия",
    page_icon="✈️",
    layout="wide"
)

# Загрузка тем
@st.cache_data
def load_themes():
    return scan_themes()

def initialize_session_state():
    """Инициализация состояния сессии"""
    default_state = {
        'test_started': False,
        'test_finished': False,
        'current_question': 0,
        'score': 0,
        'user_answers': {},
        'show_results': False,
        'selected_questions': [],
        'selected_theme': None,
        'test_config': {'category': 'Все категории', 'num_questions': 5},
        'question_start_time': None,
        'question_times': [],
        'answers_checked': {},
        'question_scores': {},
        'user_info': None,
        'user_logged_in': False
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

def format_time(seconds):
    """Форматирование времени в читаемый вид (минуты:секунды)"""
    seconds_rounded = round(seconds)
    minutes = seconds_rounded // 60
    seconds_display = seconds_rounded % 60
    return f"{minutes:02d}:{seconds_display:02d}"

def calculate_partial_score(question, user_answer):
    """Расчет частичных баллов для разных типов вопросов"""
    
    if question["type"] == "single_choice":
        return 1.0 if user_answer == question["correct"] else 0.0
    
    elif question["type"] == "multiple_choice":
        user_set = set(user_answer or [])
        correct_set = set(question["correct"])
        
        if not user_set:
            return 0.0
            
        correct_answers = len(user_set & correct_set)
        wrong_answers = len(user_set - correct_set)
        total_possible = len(correct_set)
        
        score = max(0, (correct_answers - wrong_answers)) / total_possible
        return round(score, 2)
    
    elif question["type"] == "matching":
        if not user_answer:
            return 0.0
            
        correct_count = 0
        total_pairs = len(question['correct_mapping'])
        
        for left_item, correct_right in question['correct_mapping'].items():
            if user_answer.get(left_item) == correct_right:
                correct_count += 1
        
        return round(correct_count / total_pairs, 2)
    
    elif question["type"] == "dropdown":
        return 1.0 if user_answer == question["correct"] else 0.0
    
    elif question["type"] == "double_dropdown":
        if not user_answer:
            return 0.0
            
        correct_count = 0
        total_subquestions = len(question["subquestions"])
        
        for subq in question["subquestions"]:
            if user_answer.get(subq["key"]) == subq["correct"]:
                correct_count += 1
        
        return round(correct_count / total_subquestions, 2)
    
    elif question["type"] == "ordering":
        if not user_answer:
            return 0.0
            
        data = user_answer
        user_sequence = []
        for idx, item in enumerate(data["items"]):
            user_sequence.append((data["user_order"][idx], item))
        
        user_sequence.sort()
        user_order = [item for _, item in user_sequence]
        correct_order = question["correct_order"]
        
        if len(user_order) != len(correct_order):
            return 0.0
            
        correct_positions = 0
        for i in range(len(user_order)):
            if user_order[i] == correct_order[i]:
                correct_positions += 1
        
        return round(correct_positions / len(correct_order), 2)
    
    return 0.0

def check_answer(question, answer_key):
    """Проверка ответа с системой частичных баллов"""
    user_answer = st.session_state.user_answers.get(answer_key)
    if user_answer is None:
        st.warning("⚠️ Сначала выберите ответ!")
        return False
    
    score = calculate_partial_score(question, user_answer)
    
    # Сохраняем балл за вопрос
    st.session_state.question_scores[answer_key] = score
    
    # Обновляем общий счет
    st.session_state.score += score
    
    # Отмечаем что ответ проверен
    st.session_state.answers_checked[answer_key] = True
    
    # Визуальная обратная связь
    if score == 1.0:
        st.success("✅ Отлично! Полный балл!")
    elif score >= 0.7:
        st.success(f"✅ Хорошо! {score:.2f} балла из 1.00")
    elif score >= 0.5:
        st.warning(f"⚠️ Неплохо! {score:.2f} балла из 1.00")
    elif score > 0:
        st.warning(f"⚠️ Частично верно! {score:.2f} балла из 1.00")
    else:
        st.error("❌ Неправильно! 0.00 баллов")
    
    st.info(f"**Объяснение:** {question['explanation']}")
    
    return True

def get_answer_key(question):
    """Получение ключа ответа"""
    type_map = {
        "single_choice": "single",
        "multiple_choice": "multiple", 
        "dropdown": "dropdown",
        "double_dropdown": "double",
        "ordering": "ordering",
        "matching": "matching"
    }
    return f"q_{question['id']}_{type_map[question['type']]}"

def render_login_form():
    """Форма ввода данных пользователя"""
    st.header("👤 Введите ваши данные")
    
    with st.form("user_login"):
        col1, col2 = st.columns(2)
        
        with col1:
            last_name = st.text_input("Фамилия:*", placeholder="Иванов")
            first_name = st.text_input("Имя:*", placeholder="Иван")
        
        with col2:
            middle_name = st.text_input("Отчество:", placeholder="Иванович")
            position = st.text_input("Должность:*", placeholder="Техник по эксплуатации")
        
        st.markdown("**Обязательные поля отмечены звездочкой (*)**")
        
        if st.form_submit_button("🚀 Начать тестирование", type="primary", use_container_width=True):
            if last_name.strip() and first_name.strip() and position.strip():
                st.session_state.user_info = {
                    'last_name': last_name.strip(),
                    'first_name': first_name.strip(), 
                    'middle_name': middle_name.strip(),
                    'position': position.strip(),
                    'login_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.user_logged_in = True
                st.rerun()
            else:
                st.error("❌ Заполните все обязательные поля!")
def render_question_selection():
    """Выбор темы и настройка теста"""
    st.write("### 🎯 Настройка теста")
    
    themes = load_themes()
    if not themes:
        st.error("❌ Темы не найдены! Сначала создайте темы в редакторе.")
        return
    
    # Выбор ФАП
    theme_options = {theme_id: f"{data['name']} - {data['description']}" 
                    for theme_id, data in themes.items()}
    selected_theme_id = st.selectbox(
        "Выберите тему для тестирования:",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x]
    )
    
    st.session_state.selected_theme = themes[selected_theme_id]
    
    # Выбор категории
    categories = ["Все категории"] + get_categories_for_theme(themes, selected_theme_id)
    selected_category = st.selectbox(
        "Выберите категорию вопросов:",
        categories
    )
    
    # Получаем вопросы для выбранной категории
    theme_questions = st.session_state.selected_theme["questions"]
    if selected_category != "Все категории":
        theme_questions = [q for q in theme_questions if q.get('category') == selected_category]
    
    # Настройка количества вопросов
    if len(theme_questions) == 0:
        st.warning("⚠️ В выбранной категории нет вопросов")
        num_questions = 0
    elif len(theme_questions) == 1:
        st.write(f"**Будет задан 1 вопрос**")
        num_questions = 1
    else:
        num_questions = st.slider(
            "Количество вопросов в тесте:",
            min_value=1,
            max_value=len(theme_questions),
            value=min(10, len(theme_questions))
        )
    
    st.session_state.test_config = {
        'category': selected_category,
        'num_questions': num_questions
    }
    
    # Кнопка начала теста
    if len(theme_questions) > 0:
        if st.button("🚀 Начать тест", type="primary", use_container_width=True):
            # Выбираем случайные вопросы
            if len(theme_questions) == 1:
                selected_questions = theme_questions
            else:
                selected_questions = random.sample(theme_questions, num_questions)
            
            # Перемешиваем порядок вопросов
            random.shuffle(selected_questions)
            
            st.session_state.selected_questions = selected_questions
            st.session_state.test_started = True
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.user_answers = {}
            st.session_state.answers_checked = {}
            st.session_state.question_times = [0] * len(selected_questions)
            st.session_state.question_scores = {}
            st.session_state.question_start_time = time.time()
            
            # СОХРАНЯЕМ ТЕКУЩИЙ ТЕСТ ДЛЯ ВОЗМОЖНОГО ПОВТОРЕНИЯ
            # Это перезаписывает предыдущий сохраненный тест
            st.session_state.last_test_questions = selected_questions.copy()
            st.session_state.last_test_theme = st.session_state.selected_theme
            
            st.rerun()
    else:
        st.button("🚀 Начать тест", disabled=True, use_container_width=True, 
                 help="Нет вопросов в выбранной категории")

def update_question_time():
    """Обновляет время для текущего вопроса"""
    if (st.session_state.test_started and not st.session_state.test_finished and 
        st.session_state.question_start_time is not None):
        current_time = time.time()
        elapsed = current_time - st.session_state.question_start_time
        
        # Обновляем время в массиве
        q_index = st.session_state.current_question
        if q_index < len(st.session_state.question_times):
            st.session_state.question_times[q_index] = elapsed

def render_single_choice_question(question, q_index):
    """Вопрос с одним правильным ответом"""
    st.subheader(f"❓ Вопрос {q_index + 1}")
    st.write(f"**{question['question']}**")
    
    answer_key = f"q_{question['id']}_single"
    
    # Инициализация ответа
    if answer_key not in st.session_state.user_answers:
        st.session_state.user_answers[answer_key] = None
    
    options = question["options"]
    
    # Если ответ уже проверен - показываем результат
    if st.session_state.answers_checked.get(answer_key, False):
        selected = st.radio(
            "Выберите один правильный ответ:",
            options,
            index=options.index(st.session_state.user_answers[answer_key]) if st.session_state.user_answers[answer_key] in options else 0,
            key=f"locked_{question['id']}",
            disabled=True
        )
        # Показываем результат проверки
        score = st.session_state.question_scores.get(answer_key, 0)
        if score == 1.0:
            st.success("✅ Правильно!")
        else:
            st.error(f"❌ Неправильно! Правильный ответ: {question['correct']}")
        st.info(f"**Объяснение:** {question['explanation']}")
    else:
        selected = st.radio(
            "Выберите один правильный ответ:",
            options,
            key=f"single_{question['id']}"
        )
        st.session_state.user_answers[answer_key] = selected
    
    render_navigation_buttons(question, q_index, answer_key)

def render_multiple_choice_question(question, q_index):
    """Вопрос с несколькими правильными ответами"""
    st.subheader(f"❓ Вопрос {q_index + 1}")
    st.write(f"**{question['question']}**")
    st.write("*Выберите все правильные ответы:*")
    
    answer_key = f"q_{question['id']}_multiple"
    
    # Инициализация ответа
    if answer_key not in st.session_state.user_answers:
        st.session_state.user_answers[answer_key] = []
    
    options = question["options"]
    
    # Если ответ уже проверен - показываем результат
    if st.session_state.answers_checked.get(answer_key, False):
        selected_options = st.session_state.user_answers[answer_key]
        
        for i, option in enumerate(options):
            is_checked = option in selected_options
            st.checkbox(option, value=is_checked, disabled=True, key=f"locked_multi_{question['id']}_{i}")
        
        # Показываем результат проверки
        score = st.session_state.question_scores.get(answer_key, 0)
        if score == 1.0:
            st.success("✅ Все ответы правильные!")
        else:
            st.error("❌ Не все ответы правильные!")
        st.info(f"**Объяснение:** {question['explanation']}")
    else:
        selected_options = []
        for i, option in enumerate(options):
            if st.checkbox(option, key=f"multi_{question['id']}_{i}"):
                selected_options.append(option)
        
        st.session_state.user_answers[answer_key] = selected_options
    
    render_navigation_buttons(question, q_index, answer_key)

def render_dropdown_question(question, q_index):
    """Вопрос с выпадающим списком"""
    st.subheader(f"❓ Вопрос {q_index + 1}")
    st.write(f"**{question['question']}**")
    
    answer_key = f"q_{question['id']}_dropdown"
    
    if answer_key not in st.session_state.user_answers:
        st.session_state.user_answers[answer_key] = None
    
    options = ["Выберите ответ..."] + question["options"]
    
    # Если ответ уже проверен - показываем результат
    if st.session_state.answers_checked.get(answer_key, False):
        selected = st.selectbox(
            "Выберите правильный ответ:",
            options,
            index=options.index(st.session_state.user_answers[answer_key]) if st.session_state.user_answers[answer_key] in options else 0,
            key=f"locked_drop_{question['id']}",
            disabled=True
        )
        # Показываем результат проверки
        score = st.session_state.question_scores.get(answer_key, 0)
        if score == 1.0:
            st.success("✅ Правильно!")
        else:
            st.error(f"❌ Неправильно! Правильный ответ: {question['correct']}")
        st.info(f"**Объяснение:** {question['explanation']}")
    else:
        selected = st.selectbox(
            "Выберите правильный ответ:",
            options,
            key=f"drop_{question['id']}"
        )
        
        if selected != "Выберите ответ...":
            st.session_state.user_answers[answer_key] = selected
    
    render_navigation_buttons(question, q_index, answer_key)
def render_matching_question(question, q_index):
    """Версия matching вопроса с единообразным отображением результатов"""
    answer_key = f"q_{question['id']}_matching"
    
    # Инициализация
    if answer_key not in st.session_state.user_answers:
        st.session_state.user_answers[answer_key] = {}
    
    # Перемешиваем правый столбец
    right_options = question['right_column'].copy()
    random.shuffle(right_options)
    
    st.subheader(f"🔗 Вопрос {q_index + 1}")
    st.write(f"**{question['question']}**")
    
    answer_key = f"q_{question['id']}_matching"
    
    # Инициализация ответов пользователя
    if answer_key not in st.session_state.user_answers:
        st.session_state.user_answers[answer_key] = {}
    
    # Перемешиваем правый столбец для вариантов ответа
    right_options = question['right_column'].copy()
    random.shuffle(right_options)
    
    st.write("---")
    
    # Отображение пар для сопоставления
    all_answered = True
    any_changes = False
    is_checked = st.session_state.answers_checked.get(answer_key, False)
    
    for i, left_item in enumerate(question['left_column']):
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.write(f"**{left_item}**")
        
        with col2:
            current_value = st.session_state.user_answers[answer_key].get(left_item, "Выберите...")
            
            # Уникальный ключ для selectbox
            select_key = f"match_{question['id']}_{i}_{q_index}"
            if select_key not in st.session_state:
                st.session_state[select_key] = current_value
            
            # Если ответ уже проверен - показываем заблокированное поле
            if is_checked:
                st.selectbox(
                    f"Соответствие для {left_item}:",
                    options=["Выберите..."] + right_options,
                    index=right_options.index(current_value) + 1 if current_value in right_options else 0,
                    key=f"locked_{select_key}",
                    disabled=True,
                    label_visibility="collapsed"
                )
                
                # Показываем результат проверки как в single_choice
                user_answer = st.session_state.user_answers[answer_key].get(left_item, "Выберите...")
                correct_answer = question['correct_mapping'][left_item]
                
                if user_answer == correct_answer:
                    st.success("✅ Правильно!")
                else:
                    st.error(f"❌ Неправильно! Правильный ответ: {correct_answer}")
                    
            else:
                # Активное поле для выбора
                selected = st.selectbox(
                    f"Выберите соответствие для {left_item}:",
                    options=["Выберите..."] + right_options,
                    index=right_options.index(st.session_state[select_key]) + 1 if st.session_state[select_key] in right_options else 0,
                    key=select_key,
                    label_visibility="collapsed"
                )
                
                # Обновляем session_state для selectbox
                if selected != st.session_state[select_key]:
                    st.session_state[select_key] = selected
                    any_changes = True
                
                # Обновляем ответы пользователя
                if selected != current_value:
                    st.session_state.user_answers[answer_key][left_item] = selected
                    any_changes = True
            
            # Проверяем, выбран ли ответ
            if st.session_state.user_answers[answer_key].get(left_item, "Выберите...") == "Выберите...":
                all_answered = False
        
        st.write("---")
    
    # Принудительный rerun при изменениях
    if any_changes:
        st.rerun()
    
    # Если ответ проверен - показываем объяснение (как в single_choice)
    if is_checked:
        score = st.session_state.question_scores.get(answer_key, 0)
        
        # Визуальная обратная связь как в single_choice
        if score == 1.0:
            st.success("✅ Отлично! Полный балл!")
        elif score >= 0.7:
            st.success(f"✅ Хорошо! {score:.2f} балла из 1.00")
        elif score >= 0.5:
            st.warning(f"⚠️ Неплохо! {score:.2f} балла из 1.00")
        elif score > 0:
            st.warning(f"⚠️ Частично верно! {score:.2f} балла из 1.00")
        else:
            st.error("❌ Неправильно! 0.00 баллов")
        
        st.info(f"**Объяснение:** {question['explanation']}")
    
    render_navigation_buttons(question, q_index, answer_key, all_answered)

def render_double_dropdown_question(question, q_index):
    """Вопрос с несколькими выпадающими списками"""
    st.subheader(f"❓ Вопрос {q_index + 1}")
    st.write(f"**{question['question']}**")
    
    answer_key = f"q_{question['id']}_double"
    
    if answer_key not in st.session_state.user_answers:
        st.session_state.user_answers[answer_key] = {}
        for subq in question["subquestions"]:
            st.session_state.user_answers[answer_key][subq["key"]] = None
    
    st.write("---")
    
    all_answered = True
    is_checked = st.session_state.answers_checked.get(answer_key, False)
    
    for subq in question["subquestions"]:
        st.write(f"**{subq['text']}**")
        
        options = ["Выберите ответ..."] + subq["options"]
        
        if is_checked:
            # Показываем заблокированные с результатом
            selected = st.selectbox(
                "",
                options,
                index=options.index(st.session_state.user_answers[answer_key][subq["key"]]) if st.session_state.user_answers[answer_key][subq["key"]] in options else 0,
                key=f"locked_double_{question['id']}_{subq['key']}",
                disabled=True,
                label_visibility="collapsed"
            )
            # Показываем правильность для каждого подвопроса
            user_ans = st.session_state.user_answers[answer_key][subq["key"]]
            if user_ans == subq["correct"]:
                st.success(f"✅ Правильно: {user_ans}")
            else:
                st.error(f"❌ Неправильно! Ваш ответ: {user_ans}, Правильный: {subq['correct']}")
        else:
            # Активные выпадающие списки
            selected = st.selectbox(
                "",
                options,
                key=f"double_{question['id']}_{subq['key']}",
                label_visibility="collapsed"
            )
            
            if selected != "Выберите ответ...":
                st.session_state.user_answers[answer_key][subq["key"]] = selected
            else:
                all_answered = False
        
        st.write("")
    
    st.write("---")
    
    if is_checked:
        st.info(f"**Объяснение:** {question['explanation']}")
    
    render_navigation_buttons(question, q_index, answer_key, all_answered if not is_checked else True)

def render_ordering_question(question, q_index):
    """Вопрос на упорядочивание"""
    st.subheader(f"❓ Вопрос {q_index + 1}")
    st.write(f"**{question['question']}**")
    st.write("*Пронумеруйте этапы от 1 (первый) до 4 (последний)*")
    
    answer_key = f"q_{question['id']}_ordering"
    
    if answer_key not in st.session_state.user_answers:
        shuffled_items = question["items"].copy()
        random.shuffle(shuffled_items)
        st.session_state.user_answers[answer_key] = {
            "items": shuffled_items,
            "user_order": [i+1 for i in range(len(shuffled_items))]
        }
    
    data = st.session_state.user_answers[answer_key]
    is_checked = st.session_state.answers_checked.get(answer_key, False)
    
    st.write("---")
    for i, item in enumerate(data["items"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{item}**")
        with col2:
            if is_checked:
                st.number_input(
                    f"Порядок",
                    value=data["user_order"][i],
                    key=f"locked_order_{question['id']}_{i}",
                    disabled=True
                )
            else:
                order = st.number_input(
                    f"Порядок",
                    min_value=1,
                    max_value=len(data["items"]),
                    value=data["user_order"][i],
                    key=f"order_{question['id']}_{i}"
                )
                data["user_order"][i] = order
    
    st.write("---")
    
    if is_checked:
        # Показываем результат проверки
        score = st.session_state.question_scores.get(answer_key, 0)
        if score == 1.0:
            st.success("✅ Порядок правильный!")
        else:
            st.error("❌ Порядок неправильный!")
        st.info(f"**Объяснение:** {question['explanation']}")
    
    render_navigation_buttons(question, q_index, answer_key)

def render_navigation_buttons(question, q_index, answer_key, all_answered=True):
    """Кнопки навигации с проверкой ответов"""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if q_index > 0:
            if st.button("← Назад", key=f"back_{question['id']}"):
                # Сохраняем время текущего вопроса
                update_question_time()
                st.session_state.current_question = q_index - 1
                st.session_state.question_start_time = time.time()
                st.rerun()
    
    with col2:
        is_checked = st.session_state.answers_checked.get(answer_key, False)
        
        if not is_checked:
            check_enabled = all_answered
            if question["type"] in ["single_choice", "multiple_choice", "dropdown"]:
                check_enabled = st.session_state.user_answers.get(answer_key) is not None
                if question["type"] == "multiple_choice":
                    check_enabled = len(st.session_state.user_answers.get(answer_key, [])) > 0
            
            if check_enabled:
                if st.button("✅ Проверить ответ", type="primary", key=f"check_{question['id']}"):
                    if check_answer(question, answer_key):
                        st.rerun()
            else:
                st.button("✅ Проверить ответ", disabled=True, key=f"check_disabled_{question['id']}")
        else:
            st.button("✅ Ответ проверен", disabled=True, key=f"checked_{question['id']}")
    
    with col3:
        if q_index < len(st.session_state.selected_questions) - 1:
            if st.button("Далее →", key=f"next_{question['id']}"):
                # Сохраняем время
                update_question_time()
                st.session_state.current_question = q_index + 1
                st.session_state.question_start_time = time.time()
                st.rerun()
        else:
            if st.button("🏁 Завершить тест", type="secondary", key=f"finish_{question['id']}"):
                # Сохраняем время последнего вопроса
                update_question_time()
                st.session_state.show_results = True
                st.session_state.test_finished = True
                st.rerun()
def create_user_folder(user_info):
    """Создает папку для пользователя на основе ФИО и даты"""
    try:
        # Транслитерация ФИО для имени папки
        last_name = user_info['last_name']
        first_name = user_info['first_name']
        
        # Форматируем дату и время для имени папки
        test_time = datetime.now()
        folder_time = test_time.strftime("%d_%m_%Y_%H_%M")
        
        # Создаем имя папки
        folder_name = f"{last_name}_{first_name}_{folder_time}"
        
        # Создаем папку в protocols
        protocols_dir = os.path.join(os.path.dirname(__file__), "protocols")
        user_folder = os.path.join(protocols_dir, folder_name)
        os.makedirs(user_folder, exist_ok=True)
        
        return user_folder
        
    except Exception as e:
        st.error(f"❌ Ошибка создания папки пользователя: {e}")
        return None

def generate_main_protocol(protocol_data, user_folder):
    """Генерация основного протокола тестирования"""
    try:
        user = protocol_data['user_info']
        results = protocol_data['results']
        
        text = f"""
ПРОТОКОЛ ТЕСТИРОВАНИЯ
=====================

Дата генерации: {protocol_data['protocol_info']['generated_at']}

ДАННЫЕ ТЕСТИРУЕМОГО:
-------------------
ФИО: {user['last_name']} {user['first_name']} {user['middle_name']}
Должность: {user['position']}
Дата тестирования: {user['login_time']}

ИНФОРМАЦИЯ О ТЕСТЕ:
------------------
Тема: {protocol_data['test_info']['theme']}
Категория: {protocol_data['test_info']['category']}
Количество вопросов: {protocol_data['test_info']['total_questions']}

РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:
-----------------------
Набрано баллов: {results['total_score']} из {results['max_score']}
Процент выполнения: {results['percentage']}%
Общее время: {results['total_time_formatted']}
Среднее время на вопрос: {results['average_time_formatted']}

ОЦЕНКА:
------
{"ОТЛИЧНО - Тест пройден успешно!" if results['percentage'] >= 80 else 
 "ХОРОШО - Тест пройден, рекомендуется повторение материала." if results['percentage'] >= 60 else 
 "НЕУДОВЛЕТВОРИТЕЛЬНО - Требуется дополнительное обучение."}

=====================
Детальная статистика по вопросам сохранена в отдельном файле.
"""
        
        # Сохраняем основной протокол
        filename = f"Протокол_тестирования_{user['last_name']}_{user['first_name']}.txt"
        filepath = os.path.join(user_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return filepath
        
    except Exception as e:
        st.error(f"❌ Ошибка генерации основного протокола: {e}")
        return None

def generate_detailed_statistics(protocol_data, user_folder):
    """Генерация детальной статистики по вопросам с полной информацией"""
    try:
        user = protocol_data['user_info']
        
        text = f"""
ДЕТАЛЬНАЯ СТАТИСТИКА ПО ВОПРОСАМ
================================

ФИО: {user['last_name']} {user['first_name']} {user['middle_name']}
Тема тестирования: {protocol_data['test_info']['theme']}
Дата тестирования: {user['login_time']}

СТАТИСТИКА ПО ВОПРОСАМ:
======================
"""
        
        for i, detail in enumerate(protocol_data['detailed_results']):
            question = st.session_state.selected_questions[i]
            user_answer = st.session_state.user_answers.get(get_answer_key(question))
            
            text += f"""
Вопрос {detail['question_number']}:
╔═══════════════════════════════════════════════════════════════════
║ Баллы: {detail['score']:.2f}/1.00
║ Время: {detail['time_formatted']}
╟───────────────────────────────────────────────────────────────────
║ ВОПРОС: {question['question']}
╟───────────────────────────────────────────────────────────────────
"""
            
            # Обработка разных типов вопросов
            if question['type'] == 'single_choice':
                text += f"║ ВАРИАНТЫ: {', '.join(question['options'])}\n"
                text += f"║ ВАШ ОТВЕТ: {user_answer}\n"
                text += f"║ ПРАВИЛЬНЫЙ ОТВЕТ: {question['correct']}\n"
                text += f"║ СТАТУС: {'✅ ВЕРНО' if user_answer == question['correct'] else '❌ НЕВЕРНО'}\n"
                
            elif question['type'] == 'multiple_choice':
                text += f"║ ВАРИАНТЫ: {', '.join(question['options'])}\n"
                text += f"║ ВАШИ ОТВЕТЫ: {', '.join(user_answer) if user_answer else 'Нет ответа'}\n"
                text += f"║ ПРАВИЛЬНЫЕ ОТВЕТЫ: {', '.join(question['correct'])}\n"
                user_set = set(user_answer or [])
                correct_set = set(question['correct'])
                if user_set == correct_set:
                    text += "║ СТАТУС: ✅ ВСЕ ОТВЕТЫ ВЕРНЫ\n"
                else:
                    text += "║ СТАТУС: ⚠️ ЧАСТИЧНО ВЕРНО\n"
                    
            elif question['type'] == 'matching':
                text += "║ СООТВЕТСТВИЯ:\n"
                for left_item in question['left_column']:
                    user_ans = user_answer.get(left_item, 'Не ответил')
                    correct_ans = question['correct_mapping'][left_item]
                    is_correct = user_ans == correct_ans
                    status = '✅ ВЕРНО' if is_correct else '❌ НЕВЕРНО'
                    text += f"║   • {left_item}: {user_ans} → {correct_ans} ({status})\n"
                    
            elif question['type'] == 'dropdown':
                text += f"║ ВАРИАНТЫ: {', '.join(question['options'])}\n"
                text += f"║ ВАШ ОТВЕТ: {user_answer}\n"
                text += f"║ ПРАВИЛЬНЫЙ ОТВЕТ: {question['correct']}\n"
                text += f"║ СТАТУС: {'✅ ВЕРНО' if user_answer == question['correct'] else '❌ НЕВЕРНО'}\n"
                
            elif question['type'] == 'double_dropdown':
                text += "║ ПОДВОПРОСЫ:\n"
                for subq in question['subquestions']:
                    user_ans = user_answer.get(subq['key'], 'Не ответил')
                    is_correct = user_ans == subq['correct']
                    status = '✅ ВЕРНО' if is_correct else '❌ НЕВЕРНО'
                    text += f"║   • {subq['text']}: {user_ans} → {subq['correct']} ({status})\n"
                    
            elif question['type'] == 'ordering':
                # Восстанавливаем порядок пользователя
                data = user_answer
                user_sequence = []
                for idx, item in enumerate(data["items"]):
                    user_sequence.append((data["user_order"][idx], item))
                user_sequence.sort()
                user_order = [item for _, item in user_sequence]
                
                text += f"║ ЭЛЕМЕНТЫ: {', '.join(question['items'])}\n"
                text += f"║ ВАШ ПОРЯДОК: {', '.join(user_order)}\n"
                text += f"║ ПРАВИЛЬНЫЙ ПОРЯДОК: {', '.join(question['correct_order'])}\n"
                text += f"║ СТАТУС: {'✅ ВЕРНО' if user_order == question['correct_order'] else '❌ НЕВЕРНО'}\n"
            
            text += "╚═══════════════════════════════════════════════════════════════════\n"
        
        text += "\n" + "="*70
        text += "\nСтатистика сгенерирована автоматически системой тестирования ФАП"
        
        # Сохраняем детальную статистику
        filename = f"Детальная_статистика_{user['last_name']}_{user['first_name']}.txt"
        filepath = os.path.join(user_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return filepath
        
    except Exception as e:
        st.error(f"❌ Ошибка генерации детальной статистики: {e}")
        return None

def generate_protocol_data():
    """Генерация данных для протокола"""
    user_info = st.session_state.user_info
    total_questions = len(st.session_state.selected_questions)
    total_score = st.session_state.score
    max_possible_score = total_questions
    total_time = sum(st.session_state.question_times)
    percentage = (total_score / max_possible_score) * 100
    
    protocol = {
        "protocol_info": {
            "title": "Протокол тестирования",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "user_info": user_info,
        "test_info": {
            "theme": st.session_state.selected_theme['name'],
            "total_questions": total_questions,
            "category": st.session_state.test_config['category']
        },
        "results": {
            "total_score": round(total_score, 2),
            "max_score": max_possible_score,
            "percentage": round(percentage, 1),
            "total_time_seconds": round(total_time),
            "total_time_formatted": format_time(total_time),
            "average_time_seconds": round(total_time / total_questions) if total_questions > 0 else 0,
            "average_time_formatted": format_time(total_time / total_questions) if total_questions > 0 else "00:00"
        },
        "detailed_results": []
    }
    
    # Добавляем детальную информацию по каждому вопросу
    for i, question in enumerate(st.session_state.selected_questions):
        answer_key = get_answer_key(question)
        question_time = st.session_state.question_times[i] if i < len(st.session_state.question_times) else 0
        question_score = st.session_state.question_scores.get(answer_key, 0)
        
        protocol["detailed_results"].append({
            "question_number": i + 1,
            "question_text": question['question'],
            "score": round(question_score, 2),
            "time_seconds": round(question_time),
            "time_formatted": format_time(question_time),
            "category": question.get('category', 'Не указана')
        })
    
    return protocol

def render_results():
    """Отображение результатов с раздельными протоколами"""
    st.balloons()
    
    # Генерируем протоколы только если они еще не созданы для этого теста
    if 'protocols_created' not in st.session_state:
        protocol_data = generate_protocol_data()
        user_folder = create_user_folder(protocol_data['user_info'])
        
        if user_folder:
            main_protocol_file = generate_main_protocol(protocol_data, user_folder)
            detailed_stats_file = generate_detailed_statistics(protocol_data, user_folder)
            
            # Сохраняем информацию о созданных протоколах
            st.session_state.protocols_created = True
            st.session_state.protocol_data = protocol_data
            st.session_state.protocol_files = {
                'main': main_protocol_file,
                'detailed': detailed_stats_file,
                'folder': user_folder
            }
        else:
            st.error("❌ Не удалось создать папку для протоколов")
            return
    else:
        # Используем уже созданные протоколы
        protocol_data = st.session_state.protocol_data
        main_protocol_file = st.session_state.protocol_files['main']
        detailed_stats_file = st.session_state.protocol_files['detailed']
        user_folder = st.session_state.protocol_files['folder']
    
    st.success("## 📋 Протоколы тестирования")
    
    # Отображаем информацию о созданных файлах
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ Основной протокол")
        if main_protocol_file:
            with open(main_protocol_file, "rb") as file:
                st.download_button(
                    label="📄 Скачать основной протокол",
                    data=file,
                    file_name=os.path.basename(main_protocol_file),
                    mime="text/plain",
                    use_container_width=True,
                    key="download_main_protocol"
                )
    
    with col2:
        st.success("✅ Детальная статистика")
        if detailed_stats_file:
            with open(detailed_stats_file, "rb") as file:
                st.download_button(
                    label="📈 Скачать детальную статистику",
                    data=file,
                    file_name=os.path.basename(detailed_stats_file),
                    mime="text/plain",
                    use_container_width=True,
                    key="download_detailed_stats"
                )
    
    # Информация о папке
    if user_folder:
        st.info(f"📁 **Все протоколы сохранены в папке:** `{os.path.basename(user_folder)}`")
    
    # Отображаем краткую информацию в интерфейсе
    st.write("---")
    
    # Информация о пользователе
    user_info = st.session_state.user_info
    st.write("### 👤 Данные тестируемого:")
    st.write(f"**ФИО:** {user_info['last_name']} {user_info['first_name']} {user_info['middle_name']}")
    st.write(f"**Должность:** {user_info['position']}")
    st.write(f"**Дата и время тестирования:** {user_info['login_time']}")
    
    # Результаты теста
    st.write("### 📊 Результаты тестирования:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Набрано баллов", f"{protocol_data['results']['total_score']}/{protocol_data['results']['max_score']}")
    with col2:
        st.metric("Процент выполнения", f"{protocol_data['results']['percentage']}%")
    with col3:
        st.metric("Общее время", protocol_data['results']['total_time_formatted'])
    with col4:
        st.metric("Среднее время на вопрос", protocol_data['results']['average_time_formatted'])
    
    # Оценка
    st.write("### 🎯 Оценка:")
    if protocol_data['results']['percentage'] >= 80:
        st.success("## 🏆 ОТЛИЧНО - Тест пройден успешно!")
    elif protocol_data['results']['percentage'] >= 60:
        st.warning("## 👍 ХОРОШО - Тест пройден, рекомендуется повторение материала.")
    else:
        st.error("## 📚 НЕУДОВЛЕТВОРИТЕЛЬНО - Требуется дополнительное обучение.")
    
    # Краткий просмотр детальной статистики
    st.write("---")
    st.write("## 📝 Краткий обзор статистики:")
    
    for i, detail in enumerate(protocol_data['detailed_results'][:3]):  # Показываем первые 3 вопроса
        question = st.session_state.selected_questions[i]
        with st.expander(f"Вопрос {detail['question_number']}: {detail['score']:.2f} балла - {detail['time_formatted']}", expanded=False):
            st.write(f"**Вопрос:** {question['question']}")
            st.write(f"**Время:** {detail['time_formatted']}")
            st.write(f"**Баллы:** {detail['score']:.2f} из 1.00")
            
            if detail['score'] == 1.0:
                st.success("✅ Полный балл")
            elif detail['score'] > 0:
                st.warning(f"⚠️ Частично верно")
            else:
                st.error("❌ 0 баллов")
    
    if len(protocol_data['detailed_results']) > 3:
        st.info(f"*И еще {len(protocol_data['detailed_results']) - 3} вопросов... Полная статистика в скачиваемом файле.*")
    
    # Одна кнопка для нового теста
    st.write("---")
    
    if st.button("🔄 Пройти новый тест", type="primary", use_container_width=True, key="new_test_button"):
        # Сбрасываем ВСЕ состояния связанные с текущим тестом
        keys_to_keep = ['user_info', 'user_logged_in', 'selected_theme', 'test_config']
        state_backup = {}
        
        # Сохраняем только важные состояния для нового теста
        for key in keys_to_keep:
            if key in st.session_state:
                state_backup[key] = st.session_state[key]
        
        # Полная очистка session_state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Восстанавливаем только то, что нужно для нового теста
        for key, value in state_backup.items():
            st.session_state[key] = value
        
        # Инициализируем заново
        initialize_session_state()
        st.rerun()

def main():
    st.title("✈️ Тесты по Федеральным авиационным правилам")
    st.write("**Модульная версия** - каждый ФАП в отдельном файле")
    
    initialize_session_state()
    
    # Если пользователь не авторизован - показываем форму входа
    if not st.session_state.user_logged_in and not st.session_state.test_started:
        render_login_form()
        return
    
    if not st.session_state.test_started and not st.session_state.show_results:
        # Показываем информацию о пользователе
        user_info = st.session_state.user_info
        st.success(f"👤 **Тестируемый:** {user_info['last_name']} {user_info['first_name']} {user_info['middle_name']} | **Должность:** {user_info['position']}")
        
        # Выбор темы и настройка теста
        render_question_selection()
        
        # Информация о доступных темах
        st.write("---")
        st.write("### 📚 Доступные темы:")
        
        themes = load_themes()
        for theme_id, theme_data in themes.items():
            with st.expander(f"📖 {theme_data['name']} - {theme_data.get('description', '')}"):
                st.write(f"**Всего вопросов:** {len(theme_data.get('questions', []))}")
                categories = get_categories_for_theme(themes, theme_id)
                if categories:
                    st.write("**Категории:**", ", ".join(categories))
    
    elif st.session_state.test_started and not st.session_state.show_results:
        # Обновляем время текущего вопроса
        update_question_time()
        
        # Отображение прогресса
        questions = st.session_state.selected_questions
        progress = (st.session_state.current_question + 1) / len(questions)
        st.progress(progress)
        
        # Информация о пользователе
        user_info = st.session_state.user_info
        st.write(f"👤 **{user_info['last_name']} {user_info['first_name'][0]}.{user_info['middle_name'][0] if user_info['middle_name'] else ''}** | 📚 **Тема:** {st.session_state.selected_theme['name']} | **Вопрос** {st.session_state.current_question + 1} из {len(questions)}")
        
        # Отображение текущего вопроса
        current_q = st.session_state.current_question
        question = questions[current_q]
        
        render_functions = {
            "single_choice": render_single_choice_question,
            "multiple_choice": render_multiple_choice_question,
            "dropdown": render_dropdown_question,
            "double_dropdown": render_double_dropdown_question,
            "ordering": render_ordering_question,
            "matching": render_matching_question
        }
        
        render_func = render_functions.get(question["type"])
        if render_func:
            render_func(question, current_q)
        else:
            st.error(f"Неизвестный тип вопроса: {question['type']}")
    
    elif st.session_state.show_results:
        # Отображение результатов
        render_results()
        
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            # КНОПКА "ПРОЙТИ ТЕСТ ЕЩЕ РАЗ" - использует сохраненный последний тест
            if st.button("🔄 Пройти тест еще раз", type="primary", use_container_width=True, key="one_more_test_button"):
                # Проверяем, есть ли сохраненный тест для повторения
                if 'last_test_questions' in st.session_state and 'last_test_theme' in st.session_state:
                    
                    # Сбрасываем только состояния теста
                    st.session_state.test_started = True
                    st.session_state.test_finished = False
                    st.session_state.current_question = 0
                    st.session_state.score = 0
                    st.session_state.user_answers = {}
                    st.session_state.show_results = False
                    st.session_state.selected_questions = st.session_state.last_test_questions.copy()
                    st.session_state.selected_theme = st.session_state.last_test_theme
                    st.session_state.answers_checked = {}
                    st.session_state.question_times = [0] * len(st.session_state.last_test_questions)
                    st.session_state.question_scores = {}
                    st.session_state.question_start_time = time.time()
                    
                    # Сбрасываем флаг создания протоколов для генерации новых
                    if 'protocols_created' in st.session_state:
                        del st.session_state.protocols_created
                    if 'protocol_data' in st.session_state:
                        del st.session_state.protocol_data
                    if 'protocol_files' in st.session_state:
                        del st.session_state.protocol_files
                    
                    st.rerun()
                else:
                    st.error("❌ Нет сохраненного теста для повторения")
                
        with col2:
            if st.button("🚪 Выйти из системы", use_container_width=True):
                # Полный сброс
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                initialize_session_state()
                st.rerun()

if __name__ == "__main__":
    main()