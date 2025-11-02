#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Bridge: Синхронизация связывания Telegram аккаунтов
"""

import json
import os
from datetime import datetime

# Настройки
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BRIDGE_SECRET = os.environ.get('BRIDGE_SECRET', 'your_bridge_secret_key_123')

def handler(request):
    """Обработчик синхронизации Telegram связывания"""
    
    try:
        # Проверяем авторизацию
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or auth_header != f'Bearer {BRIDGE_SECRET}':
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        if request.method == 'POST':
            from supabase import create_client
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            data = request.json
            
            action = data.get('action')
            
            if action == 'link_telegram':
                user_data = data.get('user')
                telegram_data = data.get('telegram')
                
                # Синхронизируем пользователя в Supabase
                user_result = supabase.table('user').upsert({
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'role': user_data['role']
                }, on_conflict='email').execute()
                
                if user_result.data:
                    supabase_user_id = user_result.data[0]['id']
                    
                    # Синхронизируем Telegram пользователя
                    telegram_result = supabase.table('telegram_user').upsert({
                        'telegram_id': telegram_data['telegram_id'],
                        'username': telegram_data.get('username'),
                        'first_name': telegram_data.get('first_name'),
                        'last_name': telegram_data.get('last_name'),
                        'user_id': supabase_user_id
                    }, on_conflict='telegram_id').execute()
                    
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'success': True,
                            'message': 'Telegram account linked in Supabase',
                            'user_id': supabase_user_id,
                            'telegram_id': telegram_data['telegram_id']
                        })
                    }
                else:
                    return {
                        'statusCode': 500,
                        'body': json.dumps({'error': 'Failed to sync user'})
                    }
            
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Unknown action'})
                }
        
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
