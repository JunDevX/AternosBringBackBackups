#!/usr/bin/env python3
"""
AternosBringBackBackups (ABBB)
CLI-инструмент для скачивания резервных копий Aternos из Google Drive
"""

import os
import sys
import argparse
import json
import socket
from pathlib import Path
from datetime import datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.exceptions import RefreshError
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
except ImportError:
    print("❌ Ошибка: Не установлены необходимые библиотеки!")
    print("Установите их командой: pip install -r requirements.txt")
    sys.exit(1)

# Константы
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
CLIENT_SECRET_FILE = 'client_secret.json'
APP_NAME = 'AternosBringBackBackups'
VERSION = '1.0.0'


class ABBB:
    """Основной класс приложения"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.setup_directories()
    
    def setup_directories(self):
        """Настройка базовых директорий"""
        self.home_dir = Path.home()
        self.desktop_dir = self.home_dir / 'Desktop'
        self.downloads_dir = self.home_dir / 'Downloads'
        
        # Создаём директории если их нет
        self.desktop_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)
    
    def check_dns(self):
        """Проверка, что DNS резолвит домены Google (частая причина ошибок на дебloat-сборках Windows)"""
        hosts_to_check = ['oauth2.googleapis.com', 'www.googleapis.com', 'accounts.google.com']
        unresolved = []
        for host in hosts_to_check:
            try:
                socket.getaddrinfo(host, 443)
            except socket.gaierror:
                unresolved.append(host)
        
        if unresolved:
            print("❌ Не удаётся разрешить DNS-имена Google:")
            for host in unresolved:
                print(f"   - {host}")
            print("\n💡 Это проблема сети/DNS на этом ПК, а не в скрипте. Проверь:")
            print("   1. Файл C:\\Windows\\System32\\drivers\\etc\\hosts — нет ли там строк с google/googleapis")
            print("   2. Службу 'DNS Client' (services.msc) — должна быть Running")
            print("   3. Фаервол/антивирус — не блокирует ли python.exe")
            print("   4. Попробуй прописать DNS вручную: 8.8.8.8 и 8.8.4.4")
            print("   5. Отключи VPN/системный прокси, если используешь")
            sys.exit(1)
    
    def authenticate(self):
        """Аутентификация через Google OAuth2"""
        print("🔐 Аутентификация в Google...")
        
        self.check_dns()
        
        # Проверяем наличие client_secret.json
        if not os.path.exists(CLIENT_SECRET_FILE):
            print(f"❌ Файл {CLIENT_SECRET_FILE} не найден!")
            print("\n📋 Инструкция по получению:")
            print("1. Перейди на https://console.cloud.google.com/")
            print("2. Создай новый проект")
            print("3. Включи Google Drive API")
            print("4. Создай OAuth 2.0 Client ID (Desktop app)")
            print("5. Скачай JSON и сохрани как client_secret.json")
            sys.exit(1)
        
        # Загружаем существующие credentials если есть
        if os.path.exists(CREDENTIALS_FILE):
            try:
                self.creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
            except Exception as e:
                print(f"⚠️  Ошибка загрузки credentials: {e}")
                self.creds = None
        
        # Если нет credentials или они невалидны
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    print("✅ Токен обновлён")
                except RefreshError:
                    print("⚠️  Токен недействителен, требуется повторная авторизация")
                    self.creds = None
            
            if not self.creds:
                print("🌐 Открываю браузер для авторизации...")
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)
                
                # Сохраняем credentials
                with open(CREDENTIALS_FILE, 'w') as token:
                    token.write(self.creds.to_json())
                print("✅ Авторизация успешна!")
        
        # Создаём сервис Google Drive
        self.service = build('drive', 'v3', credentials=self.creds)
        print("✅ Подключение к Google Drive установлено\n")
    
    def find_aternos_backups(self):
        """Поиск резервных копий Aternos в Google Drive"""
        print("🔍 Поиск резервных копий Aternos...")
        
        # Ищем файлы в папке Aternos или с определёнными паттернами
        query_patterns = [
            "name contains 'aternos'",
            "name contains 'backup'",
            "name contains 'world'",
            "mimeType = 'application/zip'",
            "mimeType = 'application/octet-stream'"
        ]
        
        all_files = []
        
        for query in query_patterns:
            try:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, size, modifiedTime, mimeType, parents)',
                    pageSize=1000
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
            except Exception as e:
                print(f"⚠️  Ошибка при поиске: {e}")
        
        # Удаляем дубликаты
        unique_files = {f['id']: f for f in all_files}.values()
        
        # Фильтруем только файлы Aternos (по имени или размеру)
        aternos_files = []
        for file in unique_files:
            name_lower = file['name'].lower()
            if any(keyword in name_lower for keyword in ['aternos', 'backup', 'world', 'mcworld']):
                aternos_files.append(file)
        
        if not aternos_files:
            print("❌ Резервные копии Aternos не найдены!")
            print("\n💡 Возможные причины:")
            print("- Резервные копии не настроены в Aternos")
            print("- Файлы находятся в другой папке")
            print("- Нет доступа к Google Drive")
            return []
        
        print(f"✅ Найдено файлов: {len(aternos_files)}\n")
        return list(aternos_files)
    
    def download_file(self, file_info, download_dir):
        """Скачивание отдельного файла"""
        file_id = file_info['id']
        file_name = file_info['name']
        file_size = int(file_info.get('size', 0))
        
        # Создаём безопасное имя файла
        safe_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.'))
        file_path = download_dir / safe_name
        
        print(f"📥 Скачивание: {file_name}")
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(file_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"   Прогресс: {progress}%", end='\r')
            
            print(f"\n✅ Сохранено: {file_path}")
            return True
            
        except Exception as e:
            print(f"\n❌ Ошибка скачивания {file_name}: {e}")
            return False
    
    def download_all_backups(self, files, download_dir):
        """Скачивание всех резервных копий"""
        print(f"📂 Директория для скачивания: {download_dir}\n")
        
        success_count = 0
        fail_count = 0
        
        for i, file_info in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]")
            if self.download_file(file_info, download_dir):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n{'='*50}")
        print(f"📊 Итого скачано: {success_count}")
        print(f"❌ Ошибок: {fail_count}")
        print(f"{'='*50}")
    
    def get_download_path(self, path_type, custom_path=None):
        """Получение пути для скачивания"""
        if path_type == 'desktop':
            return self.desktop_dir
        elif path_type == 'downloads':
            return self.downloads_dir
        elif path_type == 'custom' and custom_path:
            custom_dir = Path(custom_path)
            custom_dir.mkdir(parents=True, exist_ok=True)
            return custom_dir
        else:
            return self.desktop_dir  # По умолчанию


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='AternosBringBackBackups (ABBB) - Скачивание резервных копий Aternos из Google Drive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  abbb.py                          # Скачать на рабочий стол
  abbb.py --path downloads         # Скачать в папку Загрузки
  abbb.py --path custom --dir ./my_backups  # Скачать в указанную папку
  abbb.py --list                   # Только показать список файлов
        """
    )
    
    parser.add_argument(
        '--path',
        choices=['desktop', 'downloads', 'custom'],
        default='desktop',
        help='Куда скачивать файлы (по умолчанию: desktop)'
    )
    
    parser.add_argument(
        '--dir',
        type=str,
        help='Пользовательская директория для скачивания (используется с --path custom)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Только показать список файлов без скачивания'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} {VERSION}'
    )
    
    args = parser.parse_args()
    
    # Выводим заголовок
    print(f"\n{'='*50}")
    print(f"🎮 {APP_NAME} v{VERSION}")
    print(f"{'='*50}\n")
    
    # Инициализация приложения
    app = ABBB()
    
    try:
        # Аутентификация
        app.authenticate()
        
        # Поиск файлов
        files = app.find_aternos_backups()
        
        if not files:
            sys.exit(1)
        
        # Если только показать список
        if args.list:
            print("📋 Список найденных файлов:\n")
            for i, file in enumerate(files, 1):
                size_mb = int(file.get('size', 0)) / (1024 * 1024)
                print(f"{i}. {file['name']} ({size_mb:.2f} MB)")
            sys.exit(0)
        
        # Получаем путь для скачивания
        download_dir = app.get_download_path(args.path, args.dir)
        
        # Подтверждение
        print(f"\n⚠️  Будет скачано {len(files)} файлов в: {download_dir}")
        response = input("Продолжить? (y/n): ").strip().lower()
        
        if response != 'y':
            print("❌ Отменено пользователем")
            sys.exit(0)
        
        # Скачивание
        app.download_all_backups(files, download_dir)
        
        print(f"\n🎉 Готово! Файлы сохранены в: {download_dir}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()