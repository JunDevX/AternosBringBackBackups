![alt text](https://raw.githubusercontent.com/JunDevX/AternosBringBackBackups/refs/heads/main/abbb.jpg)

<p align="center" style="text-align: center;">
  <a href="https://dsc.gg/minecraftheal"><img src="https://tr7zw.github.io/uikit/social_buttons_icon/Discord-Button-64.png" alt="Discord" style="margin: 5px 10px;"></a>
  <a href="https://github.com/JunDevX/AternosBringBackBackups"><img src="https://tr7zw.github.io/uikit/social_buttons_icon/Github-Button-64.png" alt="GitHub" style="margin: 5px 10px;"></a>
</p>

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

<img src="https://tr7zw.github.io/uikit/headlines/large/About.png" alt="About" style="margin: 5px 10px;">

This utility is built on an optimized script designed to download backups (by default) to your desktop from your Aternos servers; if you are planning to switch hosting providers for your server, this utility is the perfect solution!

## 🆕 Версия 2.0 - Прямое подключение к Aternos!

Новая версия программы теперь использует **прямое подключение к API Aternos**, что делает её более надёжной и функциональной:

- ✅ **Прямая авторизация** через логин/пароль Aternos
- ✅ **Скачивание всех файлов сервера**: миры, плагины, конфиги, логи
- ✅ **Интерактивный выбор** сервера и типа данных для скачивания
- ✅ **Сохранение учётных данных** для быстрого входа
- ✅ **Автоматическая сборка** в .exe через GitHub Actions

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

<br>![Features](https://tr7zw.github.io/uikit/headlines/large/Features.png)

### Быстрый старт

#### Вариант 1: Скачать готовый релиз
1. Перейдите в раздел [Releases](https://github.com/JunDevX/AternosBringBackBackups/releases)
2. Скачайте последнюю версию для вашей ОС
3. Запустите и следуйте инструкциям

#### Вариант 2: Собрать из исходников
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск скрипта
python abbb_v2.py

# Или собрать .exe (требуется PyInstaller)
pyinstaller --onefile --name "ABBB" abbb_v2.py
```

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

<br>![How to Use](https://tr7zw.github.io/uikit/headlines/large/How%20to%20Use.png)

### Пошаговая инструкция

1. **Запустите программу** (ABBB.exe или `python abbb_v2.py`)
2. **Введите учётные данные** от вашего аккаунта Aternos
3. **Выберите сервер** из списка ваших серверов
4. **Выберите тип скачивания**:
   - Всё (миры, плагины, конфиги)
   - Только миры
   - Только плагины
5. **Дождитесь завершения** — файлы будут сохранены на рабочем столе в папке `AternosBackups`

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

<br>![Known Issues](https://tr7zw.github.io/uikit/headlines/medium/Known%20Issues.png)

Если вы encounter технические проблемы, сначала проверьте раздел Issues — возможно решение уже найдено; если это не поможет, обратитесь через канал Discord.

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

<br>![FAQ](https://tr7zw.github.io/uikit/headlines/medium/FAQ.png)

### Часто задаваемые вопросы

**Q: Безопасно ли вводить пароль от Aternos?**  
A: Да, программа отправляет данные напрямую на серверы Aternos через защищённое HTTPS-соединение. Пароль нигде не сохраняется (если вы сами не включите опцию сохранения).

**Q: Почему не работает старая версия через Google Drive?**  
A: Aternos изменил способ создания резервных копий. Новая версия использует прямое API, что надёжнее.

**Q: Можно ли скачать конкретный файл?**  
A: В текущей версии можно выбрать тип данных (миры/плагины/всё). Индивидуальный выбор файлов планируется в будущих версиях.

**Q: Программа не запускается на Windows**  
A: Убедитесь, что у вас установлены Visual C++ Redistributable. Также попробуйте запустить от имени администратора.

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

<br>![Build Status](https://tr7zw.github.io/uikit/headlines/medium/Build%20Status.png)

[![Build and Release](https://github.com/JunDevX/AternosBringBackBackups/actions/workflows/build.yml/badge.svg)](https://github.com/JunDevX/AternosBringBackBackups/actions/workflows/build.yml)

<br>![Divider](https://tr7zw.github.io/uikit/divider_faded/Divider_03.png)

**Лицензия:** MIT  
**Автор:** JunDevX  
**Поддержка:** [Discord](https://dsc.gg/minecraftheal)
