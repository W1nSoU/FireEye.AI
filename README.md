### Рекомендації щодо встановлення та запуску 

# 1) Створити віртуальне оточення (в папці проекту)
python3 -m venv venv

# 2) Активувати venv
source venv/bin/activate

# 3) Оновити pip (опціонально, але рекомендовано)
pip install --upgrade pip

# 4) Встановити залежності з requirements.txt
pip install -r requirements.txt

# 5) Перевірити, що все встановилось
pip list

# 6) Запуск 
python3 -m firelink.main

# 7) Деактивація venv
deactivate