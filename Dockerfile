FROM python:3.12-slim

WORKDIR /app

COPY packages ./packages
COPY requirements.txt .

RUN pip install --no-index --find-links=./packages -r requirements.txt

COPY backend ./backend

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]