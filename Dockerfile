# Python-ning barqaror versiyasini tanlaymiz
FROM python:3.10-slim

# Ishchi papkani yaratamiz
WORKDIR /app

# Kutubxonalar ro'yxatini nusxalaymiz va o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodlarni nusxalaymiz
COPY . .

# Botni ishga tushirish buyrug'i 
# (Agar asosiy faylingiz nomi main.py bo'lmasa, uni o'zgartiring)
CMD ["python", "bot.py"]
