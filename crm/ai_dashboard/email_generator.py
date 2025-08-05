from openai import OpenAI
from django.conf import settings

# ✅ Создаём клиент
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_reminder_email(company_name):
    prompt = f"""
    Напиши вежливое follow-up письмо клиенту {company_name}. 
    Они давно не делали отгрузок. 
    Упомяни, что мы готовы организовать логистику, если есть потребность.
    Стиль — деловой, краткий, дружелюбный.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # ✅ Работает на всех аккаунтах
        messages=[
            {"role": "system", "content": "Ты профессиональный менеджер по продажам"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content
