# /home/maksim/Документы/DMA/fap_test_system/utils/theme_loader.py
"""
Модуль для автоматической загрузки тем (ФАПов) из папки themes/
"""
import os
import json
import glob
from typing import Dict, List, Any

def scan_themes() -> Dict[str, Any]:
    """
    Сканирует папку themes/ и загружает все .json файлы как темы
    Возвращает словарь с темами
    """
    themes = {}
    
    # Получаем абсолютный путь к папке themes
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    themes_dir = os.path.join(project_root, "themes")
    
    print(f"🔍 Ищем темы в папке: {themes_dir}")
    
    theme_files = glob.glob(os.path.join(themes_dir, "*.json"))
    print(f"📁 Найдено файлов: {theme_files}")
    
    for theme_file in theme_files:
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            # Извлекаем ID темы из имени файла (fap297.json -> fap297)
            theme_id = os.path.basename(theme_file).replace('.json', '')
            
            # Добавляем тему в словарь
            themes[theme_id] = theme_data
            print(f"✅ Загружена тема: {theme_data.get('name', theme_id)}")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки темы {theme_file}: {e}")
    
    return themes

def get_categories_for_theme(themes: Dict, theme_id: str) -> List[str]:
    """Получить категории вопросов для указанной темы"""
    if theme_id not in themes:
        return []
    
    categories = set()
    for question in themes[theme_id].get('questions', []):
        if question.get('category'):
            categories.add(question['category'])
    
    return sorted(list(categories))

def save_theme(theme_id: str, theme_data: Dict) -> bool:
    """Сохранить тему в файл"""
    try:
        # Получаем путь к папке themes
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        themes_dir = os.path.join(project_root, "themes")
        
        # Создаем папку если её нет
        os.makedirs(themes_dir, exist_ok=True)
        
        # Сохраняем файл
        theme_path = os.path.join(themes_dir, f"{theme_id}.json")
        with open(theme_path, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Тема '{theme_id}' сохранена в {theme_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения темы {theme_id}: {e}")
        return False