import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    d = datetime.datetime.today()
    return {
        'year': d.year
    }
