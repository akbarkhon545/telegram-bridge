#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Bridge: Синхронизация результатов тестов между PythonAnywhere и Supabase
"""

import json
import os
from datetime import datetime

# Настройки
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BRIDGE_SECRET = os.environ.get('BRIDGE_SECRET', 'your_bridge_secret_key_123')

def handler(request):
    """Обработчик синхронизации результатов тестов"""
    
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
            
            if action == 'test_completed':
                user_email = data.get('user_email')
                result_data = data.get('result')
                
                # Находим пользователя в Supabase по email
                user_result = supabase.table('user').select('id').eq('email', user_email).execute()
                
                if not user_result.data:
                    return {
                        'statusCode': 404,
                        'body': json.dumps({'error': 'User not found in Supabase'})
                    }
                
                supabase_user_id = user_result.data[0]['id']
                
                # Сохраняем результат теста в Supabase
                test_result = supabase.table('test_result').insert({
                    'user_id': supabase_user_id,
                    'subject_id': result_data['subject_id'],
                    'correct_answers': result_data['correct_answers'],
                    'total_questions': result_data['total_questions']
                }).execute()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'message': 'Test result synced to Supabase',
                        'result_id': test_result.data[0]['id'] if test_result.data else None
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
