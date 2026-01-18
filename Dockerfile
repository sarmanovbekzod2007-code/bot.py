FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Agar faylingiz nomi main.py bo'lsa:
CMD ["python", "bot.py"] 
