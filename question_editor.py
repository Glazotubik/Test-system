# /home/maksim/Документы/DMA/fap_test_system/question_editor.py
import streamlit as st
import json
import os
import sys
import random
from datetime import datetime

# Добавляем путь для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from theme_loader import scan_themes, save_theme

# Настройка страницы
st.set_page_config(
    page_title="Редактор вопросов",
    page_icon="✏️",
    layout="wide"
)

def initialize_editor_state():
    """Инициализация состояния редактора"""
    if 'current_theme' not in st.session_state:
        st.session_state.current_theme = None
    if 'editing_question' not in st.session_state:
        st.session_state.editing_question = None
    if 'question_options' not in st.session_state:
        st.session_state.question_options = [
            {"text": "", "is_correct": False},
            {"text": "", "is_correct": False},
            {"text": "", "is_correct": False},
            {"text": "", "is_correct": False}
        ]
    if 'quick_options_text' not in st.session_state:
        st.session_state.quick_options_text = ""
    if 'question_type' not in st.session_state:
        st.session_state.question_type = "single_choice"
    if 'ordering_items' not in st.session_state:
        st.session_state.ordering_items = [""]
    if 'matching_pairs' not in st.session_state:
        st.session_state.matching_pairs = [
            {"left": "", "right": ""},
            {"left": "", "right": ""},
            {"left": "", "right": ""}
        ]

def show_theme_selector():
    """Выбор темы для редактирования"""
    st.header("📚 Выбор темы")
    
    themes = scan_themes()
    if not themes:
        st.error("❌ Темы не найдены! Сначала создайте тему.")
        return None
    
    theme_options = {theme_id: f"{data['name']} ({len(data.get('questions', []))} вопросов)" 
                    for theme_id, data in themes.items()}
    
    selected_theme = st.selectbox(
        "Выберите тему для редактирования:",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x]
    )
    
    return themes[selected_theme] if selected_theme else None

def manage_options():
    """Управление вариантами ответов с удобными текстовыми полями"""
    st.subheader("📝 Варианты ответов")
    st.write("**Введите варианты и отметьте правильные:**")
    
    # Отображение вариантов в отдельных текстовых полях
    st.write("### Введите варианты ответов:")
    
    options_to_remove = []
    
    for i, option in enumerate(st.session_state.question_options):
        # Создаем контейнер для каждого варианта
        with st.container():
            st.write(f"---")
            col1, col2, col3 = st.columns([6, 2, 1])
            
            with col1:
                # Большое текстовое поле для варианта
                option_text = st.text_area(
                    f"**Вариант {i+1}:**",
                    value=option['text'],
                    height=80,  # Высота поля для удобства
                    placeholder=f"Введите текст варианта {i+1}...\nМожно использовать несколько строк",
                    key=f"option_text_{i}",
                    help="Можно вводить многострочный текст"
                )
            
            with col2:
                st.write("")  # Отступ для выравнивания
                st.write("")
                # Выбор правильного ответа
                if st.session_state.question_type == "single_choice":
                    # Для одного ответа - radio button
                    is_correct = st.radio(
                        "Правильный ответ",
                        [False, True],
                        index=1 if option['is_correct'] else 0,
                        key=f"correct_{i}",
                        horizontal=True
                    )
                else:
                    # Для нескольких ответов - checkbox
                    is_correct = st.checkbox(
                        "Правильный",
                        value=option['is_correct'],
                        key=f"correct_{i}"
                    )
            
            with col3:
                st.write("")  # Отступ для выравнивания
                st.write("")
                # Кнопка удаления варианта (только если больше 2 вариантов)
                if len(st.session_state.question_options) > 2:
                    if st.button("🗑️ Удалить", key=f"delete_opt_{i}", use_container_width=True):
                        options_to_remove.append(i)
                else:
                    st.write("")  # Заполнитель для выравнивания
            
            # Обновляем данные варианта
            st.session_state.question_options[i] = {"text": option_text, "is_correct": is_correct}
    
    # Удаляем отмеченные для удаления варианты
    for i in sorted(options_to_remove, reverse=True):
        st.session_state.question_options.pop(i)
    
    if options_to_remove:
        st.rerun()
    
    # Кнопка добавления нового варианта
    st.write("---")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("➕ Добавить вариант", use_container_width=True, icon="➕"):
            st.session_state.question_options.append({"text": "", "is_correct": False})
            st.rerun()
    
    # Информация о текущем количестве вариантов
    valid_options = [opt for opt in st.session_state.question_options if opt['text'].strip()]
    st.info(f"📊 Заполнено вариантов: {len(valid_options)} из {len(st.session_state.question_options)}")
    
    # Подсказки по заполнению
    with st.expander("💡 Подсказки по заполнению", expanded=False):
        st.write("""
        **Рекомендации:**
        - Для вопросов с **одним ответом** отметьте только ОДИН правильный вариант
        - Для вопросов с **несколькими ответами** можно отметить несколько правильных
        - Минимальное количество вариантов: 2
        - Можно использовать многострочный текст в вариантах
        - Пустые варианты автоматически игнорируются при сохранении
        """)

def manage_matching_options():
    """Управление парами соответствия для типа matching с отдельными полями"""
    st.subheader("🔗 Установление соответствия")
    
    # Инициализация
    if 'matching_pairs' not in st.session_state:
        st.session_state.matching_pairs = [
            {"left": "", "right": ""},
            {"left": "", "right": ""},
            {"left": "", "right": ""}
        ]
    
    # Собираем все правые варианты для выпадающих списков
    all_right_options = set()
    for pair in st.session_state.matching_pairs:
        if pair['right'].strip():
            all_right_options.add(pair['right'])
    all_right_options = sorted(list(all_right_options))
    
    st.write("### Настройка пар соответствия:")
    
    pairs_to_remove = []
    
    for i, pair in enumerate(st.session_state.matching_pairs):
        st.write(f"**Пара {i+1}:**")
        col1, col2, col3 = st.columns([5, 5, 1])
        
        with col1:
            # Многострочное поле для левого элемента
            left_value = st.text_area(
                "Элемент левого столбца:",
                value=pair['left'],
                height=100,  # Высота для многострочного ввода
                placeholder="Введите элемент левого столбца...\nМожно использовать несколько строк",
                key=f"matching_left_{i}",
                help="Обычно термин, определение, название"
            )
        
        with col2:
            # Многострочное поле для правого элемента с возможностью выбора из существующих
            st.write("Элемент правого столбца:")
            
            # Поле для ввода нового значения
            new_right_value = st.text_area(
                "Введите новое значение:",
                value=pair['right'] if pair['right'] not in all_right_options else "",
                height=80,
                placeholder="Введите новое значение...\nИли выберите из существующих ниже",
                key=f"matching_right_new_{i}",
                help="Можно ввести новое значение или выбрать из существующих"
            )
            
            # Выпадающий список с существующими вариантами
            if all_right_options:
                selected_existing = st.selectbox(
                    "Или выберите из существующих:",
                    options=["-- Ввести новое значение --"] + all_right_options,
                    index=all_right_options.index(pair['right']) + 1 if pair['right'] in all_right_options else 0,
                    key=f"matching_right_select_{i}"
                )
                
                # Определяем итоговое значение
                if selected_existing != "-- Ввести новое значение --":
                    final_right_value = selected_existing
                else:
                    final_right_value = new_right_value
            else:
                final_right_value = new_right_value
        
        with col3:
            st.write("")  # Отступ
            st.write("")
            if len(st.session_state.matching_pairs) > 2:
                if st.button("🗑️", key=f"delete_matching_{i}", use_container_width=True):
                    pairs_to_remove.append(i)
        
        # Обновляем пару
        st.session_state.matching_pairs[i] = {
            "left": left_value,
            "right": final_right_value
        }
        
        st.write("---")
    
    # Удаляем отмеченные пары
    for i in sorted(pairs_to_remove, reverse=True):
        st.session_state.matching_pairs.pop(i)
    
    if pairs_to_remove:
        st.rerun()
    
    # Управление количеством пар
    st.write("**Управление парами:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ Добавить пару", use_container_width=True, icon="➕"):
            st.session_state.matching_pairs.append({"left": "", "right": ""})
            st.rerun()
    
    with col2:
        if st.button("🧹 Очистить все пары", use_container_width=True):
            st.session_state.matching_pairs = [
                {"left": "", "right": ""},
                {"left": "", "right": ""},
                {"left": "", "right": ""}
            ]
            st.rerun()
    
    # Валидация и предпросмотр
    valid_pairs = [p for p in st.session_state.matching_pairs if p['left'].strip() and p['right'].strip()]
    
    st.info(f"✅ Заполнено пар: {len(valid_pairs)} из {len(st.session_state.matching_pairs)}")
    
    if len(valid_pairs) < 2:
        st.error("❌ Добавьте хотя бы 2 пары соответствия!")
    
    # Предпросмотр
    if valid_pairs:
        st.write("### Предпросмотр соответствий:")
        for i, pair in enumerate(valid_pairs):
            with st.expander(f"Пара {i+1}: {pair['left'][:50]}... → {pair['right'][:50]}...", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Левый элемент:**")
                    st.info(pair['left'])
                with col2:
                    st.write("**Правый элемент:**")
                    st.success(pair['right'])
def manage_double_dropdown_options():
    """Управление подвопросами для double_dropdown с улучшенным интерфейсом"""
    st.subheader("🧩 Подвопросы с выпадающими списками")
    
    # Инициализация подвопросов
    if 'subquestions' not in st.session_state:
        st.session_state.subquestions = []
    
    # Форма для добавления нового подвопроса
    with st.expander("➕ Добавить новый подвопрос", expanded=True):
        st.write("**Новый подвопрос:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Многострочное поле для текста подвопроса
            new_subq_text = st.text_area(
                "Текст подвопроса:*",
                height=80,
                placeholder="Введите текст подвопроса...\nМожно использовать несколько строк",
                key="new_subq_text"
            )
            
            # Многострочное поле для вариантов ответов
            new_subq_options = st.text_area(
                "Варианты ответов (каждый с новой строки):*",
                height=100,
                placeholder="Первый вариант\nВторой вариант\nТретий вариант\n...",
                key="new_subq_options",
                help="Каждый вариант с новой строки"
            )
        
        with col2:
            new_subq_key = st.text_input(
                "Технический ключ:*", 
                placeholder="primary_radar",
                key="new_subq_key",
                help="Уникальный идентификатор на английском"
            )
            
            if new_subq_options:
                options_list = [opt.strip() for opt in new_subq_options.split('\n') if opt.strip()]
                if options_list:
                    new_subq_correct = st.selectbox(
                        "Правильный ответ:*", 
                        options_list,
                        key="new_subq_correct"
                    )
                else:
                    new_subq_correct = None
                    st.error("❌ Введите хотя бы один вариант ответа!")
            else:
                new_subq_correct = None
        
        if st.button("✅ Добавить подвопрос", key="add_subq", use_container_width=True):
            if all([new_subq_text.strip(), new_subq_key.strip(), new_subq_options.strip(), new_subq_correct]):
                st.session_state.subquestions.append({
                    "text": new_subq_text.strip(),
                    "key": new_subq_key.strip(),
                    "options": [opt.strip() for opt in new_subq_options.split('\n') if opt.strip()],
                    "correct": new_subq_correct
                })
                st.rerun()
            else:
                st.error("❌ Заполните все обязательные поля подвопроса!")
    
    # Отображение существующих подвопросов
    if st.session_state.subquestions:
        st.write("---")
        st.write("**Добавленные подвопросы:**")
        
        for i, subq in enumerate(st.session_state.subquestions):
            with st.expander(f"📋 Подвопрос {i+1}: {subq['text'][:50]}...", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Текст подвопроса:**")
                    st.info(subq['text'])
                    st.write(f"**Ключ:** `{subq['key']}`")
                    st.write("**Варианты ответов:**")
                    for opt in subq['options']:
                        st.write(f"- {opt}")
                    st.write(f"**Правильный ответ:** `{subq['correct']}`")
                
                with col2:
                    if st.button("🗑️ Удалить", key=f"delete_subq_{i}", use_container_width=True):
                        st.session_state.subquestions.pop(i)
                        st.rerun()
    else:
        st.info("📝 Добавьте хотя бы один подвопрос")

def manage_ordering_options():
    """Управление элементами для упорядочивания"""
    st.subheader("🔢 Элементы для упорядочивания")
    
    if 'ordering_items' not in st.session_state:
        st.session_state.ordering_items = [""]
    
    # Быстрое добавление элементов
    quick_ordering = st.text_area(
        "Быстрое добавление элементов (в правильном порядке, каждый с новой строки):",
        placeholder="Первый этап\nВторой этап\nТретий этап\n...",
        help="Элементы будут использованы в указанном порядке",
        key="quick_ordering"
    )
    
    if quick_ordering:
        items_list = [item.strip() for item in quick_ordering.split('\n') if item.strip()]
        st.session_state.ordering_items = items_list
    
    # Ручное управление элементами
    if not quick_ordering:
        st.write("**Или добавьте элементы по одному:**")
        
        for i, item in enumerate(st.session_state.ordering_items):
            col1, col2 = st.columns([5, 1])
            with col1:
                new_item = st.text_input(
                    f"Элемент {i+1}",
                    value=item,
                    key=f"ordering_item_{i}",
                    placeholder=f"Введите элемент {i+1}..."
                )
                st.session_state.ordering_items[i] = new_item
            
            with col2:
                if len(st.session_state.ordering_items) > 1:
                    if st.button("🗑️", key=f"delete_ordering_{i}"):
                        st.session_state.ordering_items.pop(i)
                        st.rerun()
        
        if st.button("➕ Добавить элемент", key="add_ordering_item"):
            st.session_state.ordering_items.append("")
            st.rerun()
    
    # Показ предварительного просмотра порядка
    if st.session_state.ordering_items and any(st.session_state.ordering_items):
        st.write("---")
        st.write("**Будет установлен следующий порядок:**")
        for i, item in enumerate(st.session_state.ordering_items):
            if item.strip():  # Показываем только непустые элементы
                st.write(f"{i+1}. {item}")

def show_question_form(theme):
    """Форма добавления/редактирования вопроса"""
    st.header("✏️ Добавление вопроса")
    
    # Основные поля
    col1, col2 = st.columns(2)
    
    with col1:
        question_text = st.text_area("Текст вопроса:*", height=100,
                                   placeholder="Введите текст вопроса...",
                                   key="question_text")
        category = st.text_input("Категория:*", 
                               placeholder="Например: Безопасность полетов",
                               key="category")
    
    with col2:
        # Сохраняем тип вопроса в session_state
        st.session_state.question_type = st.selectbox("Тип вопроса:*", [
            "single_choice", "multiple_choice", "dropdown", 
            "double_dropdown", "ordering", "matching"
        ], key="question_type_select")
        
        explanation = st.text_area("Объяснение:*", height=100,
                                 placeholder="Объяснение правильного ответа...",
                                 key="explanation")
    
    # Динамическое отображение в зависимости от типа вопроса
    if st.session_state.question_type == "double_dropdown":
        manage_double_dropdown_options()
    elif st.session_state.question_type == "ordering":
        manage_ordering_options()
    elif st.session_state.question_type == "matching":
        manage_matching_options()
    else:
        manage_options()  # single_choice, multiple_choice, dropdown
    
    # Кнопки управления
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("💾 Сохранить вопрос", use_container_width=True, type="primary"):
            process_question_submission(
                theme, 
                question_text, 
                st.session_state.question_type, 
                category, 
                explanation
            )
    
    with col3:
        if st.button("🔄 Очистить форму", use_container_width=True):
            safe_clear_form()
            st.rerun()

def safe_clear_form():
    """Безопасная очистка формы с сохранением структуры 4 полей"""
    # Очищаем тексты, но оставляем базовую структуру
    st.session_state.question_options = [
        {"text": "", "is_correct": False},
        {"text": "", "is_correct": False},
        {"text": "", "is_correct": False}, 
        {"text": "", "is_correct": False}
    ]
    st.session_state.matching_pairs = [
        {"left": "", "right": ""},
        {"left": "", "right": ""},
        {"left": "", "right": ""}
    ]
    st.session_state.quick_options_text = ""
    st.session_state.ordering_items = [""]
    if 'subquestions' in st.session_state:
        st.session_state.subquestions = []
    
    st.success("✅ Форма очищена! Можете вводить новый вопрос.")

def process_question_submission(theme, question_text, question_type, category, explanation):
    """Обработка сохранения вопроса"""
    # Валидация основных полей
    if not all([question_text, category, explanation]):
        st.error("❌ Заполните все обязательные поля!")
        return False
    
    # Валидация в зависимости от типа вопроса
    if question_type == "matching":
        valid_pairs = [p for p in st.session_state.matching_pairs if p['left'].strip() and p['right'].strip()]
        if len(valid_pairs) < 2:
            st.error("❌ Добавьте хотя бы 2 пары соответствия!")
            return False
        
        # Создаем структуру для matching вопроса
        left_column = [pair['left'] for pair in valid_pairs]
        right_column = list(set([pair['right'] for pair in valid_pairs]))  # Уникальные правые значения
        
        correct_mapping = {}
        for pair in valid_pairs:
            correct_mapping[pair['left']] = pair['right']
        
        new_question = {
            "id": len(theme.get('questions', [])) + 1,
            "type": question_type,
            "question": question_text,
            "left_column": left_column,
            "right_column": right_column,
            "correct_mapping": correct_mapping,
            "explanation": explanation,
            "category": category
        }
    
    elif question_type == "double_dropdown":
        if 'subquestions' not in st.session_state or not st.session_state.subquestions:
            st.error("❌ Добавьте хотя бы один подвопрос!")
            return False
        
        # Проверяем что все подвопросы заполнены правильно
        for i, subq in enumerate(st.session_state.subquestions):
            if not all([subq['text'], subq['key'], subq['options'], subq['correct']]):
                st.error(f"❌ Подвопрос {i+1} заполнен не полностью!")
                return False
        
        # Создаем вопрос double_dropdown
        new_question = {
            "id": len(theme.get('questions', [])) + 1,
            "type": question_type,
            "question": question_text,
            "subquestions": st.session_state.subquestions.copy(),
            "explanation": explanation,
            "category": category
        }
        
    elif question_type == "ordering":
        valid_items = [item.strip() for item in st.session_state.ordering_items if item.strip()]
        if len(valid_items) < 2:
            st.error("❌ Добавьте хотя бы 2 элемента для упорядочивания!")
            return False
        
        new_question = {
            "id": len(theme.get('questions', [])) + 1,
            "type": question_type,
            "question": question_text,
            "items": valid_items,
            "correct_order": valid_items,  # Предполагаем что порядок правильный
            "explanation": explanation,
            "category": category
        }
        
    else:  # single_choice, multiple_choice, dropdown
        # Валидация вариантов ответов
        valid_options = [opt for opt in st.session_state.question_options if opt['text'].strip()]
        if len(valid_options) < 2:
            st.error("❌ Добавьте хотя бы 2 варианта ответа!")
            return False
        
        # Определяем правильные ответы
        if question_type == "single_choice":
            correct_options = [opt['text'] for opt in valid_options if opt['is_correct']]
            if len(correct_options) != 1:
                st.error("❌ Для типа 'Один ответ' должен быть выбран РОВНО ОДИН правильный вариант!")
                return False
            correct_answer = correct_options[0]
        else:  # multiple_choice, dropdown
            correct_options = [opt['text'] for opt in valid_options if opt['is_correct']]
            if not correct_options:
                st.error("❌ Выберите хотя бы один правильный вариант!")
                return False
            correct_answer = correct_options
        
        new_question = {
            "id": len(theme.get('questions', [])) + 1,
            "type": question_type,
            "question": question_text,
            "options": [opt['text'] for opt in valid_options],
            "correct": correct_answer,
            "explanation": explanation,
            "category": category
        }
    
    # Добавляем в тему
    if 'questions' not in theme:
        theme['questions'] = []
    theme['questions'].append(new_question)
    
    # Сохраняем
    if save_theme(theme['id'], theme):
        st.success(f"✅ Вопрос добавлен в тему '{theme['name']}'!")
        safe_clear_form()
        return True
    else:
        st.error("❌ Ошибка сохранения вопроса!")
        return False

def show_existing_questions(theme):
    """Показ существующих вопросов"""
    if not theme.get('questions'):
        st.info("📝 В этой теме пока нет вопросов")
        return
    
    st.header("📋 Существующие вопросы")
    
    for i, question in enumerate(theme['questions']):
        with st.expander(f"❓ {question['question'][:50]}...", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Тип:** {question['type']}")
                st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                
                # Обработка разных типов вопросов
                if question['type'] == 'double_dropdown':
                    st.write("**Подвопросы:**")
                    for subq in question.get('subquestions', []):
                        st.write(f"- {subq['text']}: {subq['correct']}")
                        
                elif question['type'] == 'matching':
                    st.write("**Пары соответствия:**")
                    for left_item, right_item in question.get('correct_mapping', {}).items():
                        st.write(f"- {left_item} → {right_item}")
                        
                elif question['type'] == 'ordering':
                    st.write(f"**Правильный порядок:** {', '.join(question.get('correct_order', []))}")
                    
                else:  # single_choice, multiple_choice, dropdown
                    st.write(f"**Варианты:** {', '.join(question.get('options', []))}")
                    # Только для типов с полем 'correct'
                    if 'correct' in question:
                        if question['type'] == 'multiple_choice':
                            st.write(f"**Правильные ответы:** {', '.join(question['correct'])}")
                        else:
                            st.write(f"**Правильный ответ:** {question['correct']}")
                
                st.write(f"**Объяснение:** {question.get('explanation', 'Нет')}")
            
            with col2:
                if st.button("🗑️ Удалить", key=f"delete_{i}", use_container_width=True):
                    theme['questions'].pop(i)
                    if save_theme(theme['id'], theme):
                        st.success("✅ Вопрос удален!")
                        st.rerun()
                    break

def main():
    st.title("✏️ Редактор вопросов")
    st.write("Удобное добавление вопросов с отдельными полями для каждого варианта")
    
    initialize_editor_state()
    
    # Выбор темы
    theme = show_theme_selector()
    if not theme:
        return
    
    st.session_state.current_theme = theme
    
    # Показываем информацию о теме
    st.success(f"📚 Редактируем тему: **{theme['name']}**")
    st.write(f"**Описание:** {theme.get('description', 'Нет описания')}")
    st.write(f"**Текущее количество вопросов:** {len(theme.get('questions', []))}")
    
    # Форма добавления вопроса
    show_question_form(theme)
    
    # Существующие вопросы
    show_existing_questions(theme)

if __name__ == "__main__":
    main()        