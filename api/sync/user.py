#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Bridge: Синхронизация пользователей между PythonAnywhere и Supabase
"""

import json
import os
from datetime import datetime

# Настройки
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BRIDGE_SECRET = os.environ.get('BRIDGE_SECRET', 'your_bridge_secret_key_123')

def handler(request):
    """Обработчик синхронизации пользователей"""
    
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
            user_data = data.get('user')
            
            if action == 'user_registered':
                # Синхронизируем нового пользователя в Supabase
                result = supabase.table('user').upsert({
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'password_hash': user_data.get('password_hash', ''),
                    'role': user_data['role']
                }, on_conflict='email').execute()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'message': 'User synced to Supabase',
                        'supabase_id': result.data[0]['id'] if result.data else None
                    })
                }
            
            elif action == 'user_updated':
                # Обновляем пользователя в Supabase
                result = supabase.table('user').update({
                    'name': user_data['name'],
                    'role': user_data['role']
                }).eq('email', user_data['email']).execute()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'message': 'User updated in Supabase'
                    })
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
