# Мини-мидлвар для прокидывания текущей компании в объект запроса

class CompanyContextMiddleware:
    """
    Кладёт в request.current_company словарь с данными выбранной компании из сессии.
    Это чисто удобство для шаблонов/логирования и не влияет на безопасность.
    """

    # Инициализируем middleware ссылкой на следующий обработчик
    def __init__(self, get_response):
        self.get_response = get_response

    # Основной вызов middleware на каждый запрос
    def __call__(self, request):
        # Достаём из сессии slug и name; если их нет — считаем, что компания пока не выбрана
        slug = request.session.get("company_slug")
        name = request.session.get("company_name")
        target = request.session.get("company_target")

        # Формируем простой словарь (или None, если не выбрано)
        request.current_company = (
            {"slug": slug, "name": name, "target": target} if slug and name else None
        )

        # Передаём управление дальше по цепочке
        response = self.get_response(request)
        return response
