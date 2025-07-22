import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY  # Храним ключ в .env

def generate_reminder_email(company_name):
    prompt = f"""
    Напиши вежливое follow-up письмо клиенту {company_name}. 
    Они давно не делали отгрузок. 
    Упомяни, что мы готовы организовать логистику, если есть потребность.
    Стиль — деловой, краткий, дружелюбный.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ты профессиональный менеджер по продажам"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response['choices'][0]['message']['content']
