#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram бот с интеграцией через API Bridge
"""

import json
import os
import logging
import requests
from datetime import datetime

# Настройки
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
PYTHONANYWHERE_API = "https://auniverquizes.pythonanywhere.com/api"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None

def get_user_from_pythonanywhere(telegram_id):
    """Получение пользователя из PythonAnywhere по Telegram ID"""
    try:
        response = requests.get(f"{PYTHONANYWHERE_API}/telegram/user/{telegram_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Ошибка получения пользователя: {e}")
        return None

def link_account_via_pythonanywhere(email, password, telegram_data):
    """Связывание аккаунта через PythonAnywhere API"""
    try:
        data = {
            'email': email,
            'password': password,
            'telegram_data': telegram_data
        }
        
        response = requests.post(f"{PYTHONANYWHERE_API}/telegram/link", json=data, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Ошибка связывания аккаунта: {e}")
        return None

def get_subjects_from_pythonanywhere():
    """Получение предметов из PythonAnywhere"""
    try:
        response = requests.get(f"{PYTHONANYWHERE_API}/subjects", timeout=10)
        if response.status_code == 200:
            return response.json().get('subjects', [])
        return []
    except Exception as e:
        logger.error(f"Ошибка получения предметов: {e}")
        return []

def get_user_stats_from_pythonanywhere(user_id):
    """Получение статистики пользователя из PythonAnywhere"""
    try:
        response = requests.get(f"{PYTHONANYWHERE_API}/user/{user_id}/stats", timeout=10)
        if response.status_code == 200:
            return response.json().get('stats', {})
        return {}
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {}

def get_or_create_telegram_user_supabase(telegram_data):
    """Получить или создать Telegram пользователя в Supabase"""
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        telegram_id = telegram_data['id']
        
        # Проверяем существующего пользователя
        result = supabase.table('telegram_user')\
            .select('*')\
            .eq('telegram_id', telegram_id)\
            .execute()
        
        if result.data:
            return result.data[0]
        
        # Создаем нового пользователя
        new_user = {
            'telegram_id': telegram_id,
            'username': telegram_data.get('username'),
            'first_name': telegram_data.get('first_name'),
            'last_name': telegram_data.get('last_name'),
            'user_id': None
        }
        
        create_result = supabase.table('telegram_user').insert(new_user).execute()
        return create_result.data[0] if create_result.data else None
        
    except Exception as e:
        logger.error(f"Ошибка работы с Supabase: {e}")
        return None

def handle_start_command(chat_id, user_data):
    """Обработка команды /start"""
    # Сначала проверяем PythonAnywhere
    user_info = get_user_from_pythonanywhere(user_data['id'])
    
    if user_info and user_info.get('success'):
        # Пользователь уже связан
        user = user_info['user']
        text = f"""
🎉 <b>Добро пожаловать, {user['name']}!</b>

Ваш аккаунт связан с системой тестирования.

📚 Доступные команды:
/subjects - Список предметов
/stats - Ваша статистика
/help - Помощь

🌐 <a href="https://auniverquizes.pythonanywhere.com">Перейти на сайт</a>
        """
    else:
        # Пользователь не связан
        text = f"""
👋 <b>Добро пожаловать в систему тестирования!</b>

Для начала работы необходимо связать ваш Telegram аккаунт.

🔗 <b>Как связать аккаунт:</b>
1. Используйте команду /link
2. Введите ваш email
3. Введите ваш пароль

📝 Если у вас нет аккаунта:
🌐 <a href="https://auniverquizes.pythonanywhere.com/register">Зарегистрируйтесь на сайте</a>

📚 Команды:
/link - Связать аккаунт
/help - Помощь
        """
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔗 Связать аккаунт', 'callback_data': 'link_account'}],
            [{'text': '🌐 Открыть сайт', 'url': 'https://auniverquizes.pythonanywhere.com'}],
            [{'text': '❓ Помощь', 'callback_data': 'help'}]
        ]
    }
    
    send_message(chat_id, text, keyboard)
    
    # Также создаем запись в Supabase для аналитики
    get_or_create_telegram_user_supabase(user_data)

def handle_link_command(chat_id):
    """Обработка команды /link"""
    text = """
🔗 <b>Связывание аккаунта</b>

Для связывания вашего Telegram аккаунта:

1️⃣ Отправьте ваш email в формате:
<code>email:ваш@email.com</code>

2️⃣ Затем отправьте пароль в формате:
<code>password:ваш_пароль</code>

📝 Пример:
<code>email:student@example.com</code>
<code>password:mypassword123</code>

⚠️ <b>Важно:</b> Используйте те же данные, что и для входа на сайт.

🌐 Нет аккаунта? <a href="https://auniverquizes.pythonanywhere.com/register">Зарегистрируйтесь</a>
    """
    
    send_message(chat_id, text)

def handle_subjects_command(chat_id, user_data):
    """Обработка команды /subjects"""
    # Проверяем связанность аккаунта
    user_info = get_user_from_pythonanywhere(user_data['id'])
    
    if not user_info or not user_info.get('success'):
        send_message(chat_id, "❌ Сначала свяжите аккаунт командой /link")
        return
    
    # Получаем предметы из PythonAnywhere
    subjects = get_subjects_from_pythonanywhere()
    
    if not subjects:
        send_message(chat_id, "📚 Предметы пока не добавлены.")
        return
    
    text = "📚 <b>Доступные предметы:</b>\n\n"
    
    current_faculty = None
    for subject in subjects:
        faculty_name = subject['faculty_name']
        
        if current_faculty != faculty_name:
            current_faculty = faculty_name
            text += f"\n🏛️ <b>{faculty_name}</b>\n"
        
        question_count = subject['question_count']
        text += f"  📖 {subject['name']} ({question_count} вопросов)\n"
    
    text += f"\n🌐 <a href='https://auniverquizes.pythonanywhere.com/test_select'>Пройти тест на сайте</a>"
    
    send_message(chat_id, text)

def handle_stats_command(chat_id, user_data):
    """Обработка команды /stats"""
    # Проверяем связанность аккаунта
    user_info = get_user_from_pythonanywhere(user_data['id'])
    
    if not user_info or not user_info.get('success'):
        send_message(chat_id, "❌ Сначала свяжите аккаунт командой /link")
        return
    
    user_id = user_info['user']['id']
    
    # Получаем статистику из PythonAnywhere
    stats = get_user_stats_from_pythonanywhere(user_id)
    
    if stats and stats.get('total_tests', 0) > 0:
        text = f"""
📊 <b>Ваша статистика:</b>

🎯 Пройдено тестов: {stats.get('total_tests', 0)}
📈 Средний результат: {stats.get('avg_percentage', 0)}%
🏆 Лучший результат: {stats.get('best_percentage', 0)}%
📚 Предметов изучено: {stats.get('subjects_tested', 0)}

🌐 <a href="https://auniverquizes.pythonanywhere.com/dashboard">Подробная статистика</a>
        """
    else:
        text = """
📊 <b>Статистика пуста</b>

Вы еще не проходили тесты.

🌐 <a href="https://auniverquizes.pythonanywhere.com/test_select">Пройти первый тест</a>
        """
    
    send_message(chat_id, text)

def handle_text_message(chat_id, text, user_data):
    """Обработка текстовых сообщений"""
    if text.startswith('email:'):
        # Сохраняем email в Supabase для временного хранения
        email = text[6:].strip()
        
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            supabase.table('telegram_user')\
                .update({'link_code': f'email:{email}'})\
                .eq('telegram_id', user_data['id'])\
                .execute()
            
            send_message(chat_id, f"✅ Email сохранен: {email}\n\nТеперь отправьте пароль в формате:\n<code>password:ваш_пароль</code>")
        except Exception as e:
            logger.error(f"Ошибка сохранения email: {e}")
            send_message(chat_id, "❌ Ошибка сохранения email. Попробуйте еще раз.")
        
    elif text.startswith('password:'):
        # Обрабатываем пароль и связываем аккаунт
        password = text[9:].strip()
        
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Получаем сохраненный email
            tg_user = supabase.table('telegram_user')\
                .select('*')\
                .eq('telegram_id', user_data['id'])\
                .execute()
            
            if not tg_user.data or not tg_user.data[0].get('link_code', '').startswith('email:'):
                send_message(chat_id, "❌ Сначала отправьте email в формате:\n<code>email:ваш@email.com</code>")
                return
            
            email = tg_user.data[0]['link_code'][6:]  # Убираем 'email:'
            
            # Связываем аккаунт через PythonAnywhere API
            result = link_account_via_pythonanywhere(email, password, user_data)
            
            if result and result.get('success'):
                user = result['user']
                
                # Очищаем временный код
                supabase.table('telegram_user')\
                    .update({'link_code': None})\
                    .eq('telegram_id', user_data['id'])\
                    .execute()
                
                text = f"""
🎉 <b>Аккаунт успешно связан!</b>

👤 Добро пожаловать, {user['name']}!

📚 Теперь вы можете:
/subjects - Посмотреть предметы
/stats - Посмотреть статистику
        
🌐 <a href="https://auniverquizes.pythonanywhere.com/dashboard">Перейти в личный кабинет</a>
                """
                
                send_message(chat_id, text)
            else:
                send_message(chat_id, "❌ Неверный email или пароль. Попробуйте еще раз.")
                
        except Exception as e:
            logger.error(f"Ошибка связывания аккаунта: {e}")
            send_message(chat_id, "❌ Ошибка связывания аккаунта. Попробуйте позже.")
        
    else:
        # Неизвестная команда
        send_message(chat_id, """
❓ Неизвестная команда.

📚 Доступные команды:
/start - Начать работу
/link - Связать аккаунт
/subjects - Список предметов
/stats - Статистика
/help - Помощь

🔗 Для связывания аккаунта используйте:
<code>email:ваш@email.com</code>
<code>password:ваш_пароль</code>
        """)

def handler(request):
    """Основной обработчик webhook"""
    try:
        if request.method == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'ok',
                    'message': 'Telegram bot webhook is working with API Bridge',
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Получаем данные от Telegram
        update = request.json
        
        if not update:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No data'})
            }
        
        logger.info(f"Получено обновление: {update.get('update_id')}")
        
        # Обрабатываем сообщение
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_data = message['from']
            text = message.get('text', '')
            
            # Обрабатываем команды
            if text == '/start':
                handle_start_command(chat_id, user_data)
            elif text == '/link':
                handle_link_command(chat_id)
            elif text == '/subjects':
                handle_subjects_command(chat_id, user_data)
            elif text == '/stats':
                handle_stats_command(chat_id, user_data)
            elif text == '/help':
                handle_start_command(chat_id, user_data)  # Показываем стартовое сообщение
            else:
                handle_text_message(chat_id, text, user_data)
        
        # Обрабатываем callback запросы
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            data = callback['data']
            
            if data == 'link_account':
                handle_link_command(chat_id)
            elif data == 'help':
                handle_start_command(chat_id, callback['from'])
        
        return {
            'statusCode': 200,
            'body': json.dumps({'ok': True})
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
