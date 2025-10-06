#!/usr/bin/env python3
"""
Скрипт инициализации проекта - создает необходимые файлы и папки
"""

import os
import json

def create_theme_file():
    """Создает пример файла темы"""
    theme_data = {
        "id": "fap297",
        "name": "ФАП 297", 
        "description": "Подготовка и выполнение полетов в гражданской авиации",
        "questions": [
            {
                "id": 1,
                "type": "single_choice",
                "question": "Минимальная высота полета над населенным пунктом:",
                "options": ["300 метров", "500 метров", "1000 метров", "1500 метров"],
                "correct": "1000 метров",
                "explanation": "Согласно ФАП 297, минимальная высота полета над населенными пунктами составляет 1000 метров.",
                "category": "Высоты и эшелоны"
            }
        ]
    }
    
    themes_dir = os.path.join(os.path.dirname(__file__), "themes")
    os.makedirs(themes_dir, exist_ok=True)
    
    theme_path = os.path.join(themes_dir, "fap297.json")
    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(theme_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создан файл темы: {theme_path}")

def create_template_files():
    """Создает необходимые шаблоны"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Шаблоны типов вопросов
    question_types = {
        "single_choice": {
            "name": "Один правильный ответ",
            "description": "Выбор одного варианта из нескольких",
            "template": {
                "type": "single_choice",
                "question": "",
                "options": [],
                "correct": "",
                "explanation": "",
                "category": ""
            }
        },
        "multiple_choice": {
            "name": "Несколько правильных ответов", 
            "description": "Выбор нескольких вариантов",
            "template": {
                "type": "multiple_choice",
                "question": "",
                "options": [],
                "correct": [],
                "explanation": "",
                "category": ""
            }
        }
        # ... остальные типы можно добавить позже
    }
    
    template_path = os.path.join(templates_dir, "question_types.json")
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(question_types, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создан файл шаблонов: {template_path}")

if __name__ == "__main__":
    print("🚀 Инициализация проекта...")
    create_theme_file()
    create_template_files()
    print("✅ Проект успешно инициализирован!")
    print("📁 Запустите: streamlit run main.py")