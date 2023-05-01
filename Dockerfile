FROM python:3.10

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN SECRET_KEY=NOT_IMPORTANT_VALUE python manage.py collectstatic --no-input

CMD ["python", "-m", "gunicorn", "-b", "127.0.0.1:8080", "star_burger.wsgi:application"]

