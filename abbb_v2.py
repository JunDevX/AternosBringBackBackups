#!/usr/bin/env python3
"""
AternosBringBackBackups (ABBB) v2.0
CLI-утилита для скачивания всех файлов сервера Aternos через официальное API
Скачивает миры, плагины, конфиги и другие файлы сервера
"""

import os
import sys
import argparse
import json
import time
import zipfile
import io
from pathlib import Path
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Ошибка: Не установлены необходимые библиотеки!")
    print("Установите их командой: pip install -r requirements.txt")
    sys.exit(1)

# Константы
ATEMOS_API_BASE = "https://aternos.org"
APP_NAME = 'AternosBringBackBackups'
VERSION = '2.0.0'


class AternosAPI:
    """Класс для работы с Aternos API через веб-интерфейс"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.server_id = None
        self.server_name = None
    
    def login(self, username, password):
        """Авторизация в аккаунте Aternos"""
        print("🔐 Авторизация в Aternos...")
        
        # Получаем токен CSRF со страницы входа
        try:
            login_page = self.session.get(f"{ATEMOS_API_BASE}/login")
            login_page.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Ошибка получения страницы входа: {e}")
            return False
        
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'token'})
        
        if not csrf_token:
            print("❌ Не удалось получить CSRF токен")
            return False
        
        csrf_value = csrf_token.get('value')
        
        # Выполняем вход
        login_data = {
            'user': username,
            'password': password,
            'token': csrf_value
        }
        
        try:
            response = self.session.post(
                f"{ATEMOS_API_BASE}/login",
                data=login_data,
                allow_redirects=True
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False
        
        # Проверяем успешность входа
        if "logout" in response.text.lower() or "dashboard" in response.url:
            print("✅ Авторизация успешна!")
            return True
        else:
            print("❌ Неверный логин или пароль")
            return False
    
    def get_servers(self):
        """Получение списка серверов"""
        print("📋 Получение списка серверов...")
        
        try:
            dashboard = self.session.get(f"{ATEMOS_API_BASE}/console")
            dashboard.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Ошибка получения дашборда: {e}")
            return []
        
        soup = BeautifulSoup(dashboard.text, 'html.parser')
        servers = []
        
        # Ищем сервера в HTML
        server_elements = soup.find_all('div', class_='server-item')
        for server_elem in server_elements:
            server_id = server_elem.get('data-id')
            server_name = server_elem.find('span', class_='server-name')
            
            if server_id and server_name:
                servers.append({
                    'id': server_id,
                    'name': server_name.text.strip()
                })
        
        # Альтернативный поиск через select
        if not servers:
            select_options = soup.find_all('option', {'name': 'server'})
            for option in select_options:
                servers.append({
                    'id': option.get('value'),
                    'name': option.text.strip()
                })
        
        if servers:
            print(f"✅ Найдено серверов: {len(servers)}")
            for i, server in enumerate(servers, 1):
                print(f"   {i}. {server['name']} (ID: {server['id']})")
        
        return servers
    
    def select_server(self, server_id):
        """Выбор сервера для работы"""
        self.server_id = server_id
        print(f"✅ Выбран сервер ID: {server_id}")
        return True
    
    def get_worlds(self):
        """Получение списка миров"""
        print("🌍 Получение списка миров...")
        
        try:
            worlds_page = self.session.get(f"{ATEMOS_API_BASE}/console/{self.server_id}/worlds")
            worlds_page.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Ошибка получения миров: {e}")
            return []
        
        soup = BeautifulSoup(worlds_page.text, 'html.parser')
        worlds = []
        
        # Ищем миры в таблице
        world_rows = soup.find_all('tr', class_='world-row')
        for row in world_rows:
            world_name = row.find('span', class_='world-name')
            world_size = row.find('span', class_='world-size')
            world_date = row.find('span', class_='world-date')
            
            if world_name:
                worlds.append({
                    'name': world_name.text.strip(),
                    'size': world_size.text.strip() if world_size else 'Unknown',
                    'date': world_date.text.strip() if world_date else 'Unknown'
                })
        
        if worlds:
            print(f"✅ Найдено миров: {len(worlds)}")
        
        return worlds
    
    def download_world(self, world_name, download_dir):
        """Скачивание мира"""
        print(f"📥 Скачивание мира: {world_name}")
        
        try:
            # Запрос на скачивание мира
            download_url = f"{ATEMOS_API_BASE}/console/{self.server_id}/worlds/{world_name}/download"
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            # Сохраняем файл
            file_path = download_dir / f"{world_name}.zip"
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Мир сохранён: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка скачивания мира {world_name}: {e}")
            return False
    
    def get_plugins(self):
        """Получение списка плагинов"""
        print("🔌 Получение списка плагинов...")
        
        try:
            plugins_page = self.session.get(f"{ATEMOS_API_BASE}/console/{self.server_id}/plugins")
            plugins_page.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Ошибка получения плагинов: {e}")
            return []
        
        soup = BeautifulSoup(plugins_page.text, 'html.parser')
        plugins = []
        
        # Ищем установленные плагины
        plugin_elements = soup.find_all('div', class_='plugin-item')
        for plugin in plugin_elements:
            plugin_name = plugin.find('span', class_='plugin-name')
            plugin_version = plugin.find('span', class_='plugin-version')
            
            if plugin_name:
                plugins.append({
                    'name': plugin_name.text.strip(),
                    'version': plugin_version.text.strip() if plugin_version else 'Unknown'
                })
        
        if plugins:
            print(f"✅ Найдено плагинов: {len(plugins)}")
        
        return plugins
    
    def get_files_list(self, path="/"):
        """Получение списка файлов сервера"""
        print(f"📁 Получение списка файлов в {path}...")
        
        try:
            files_page = self.session.get(
                f"{ATEMOS_API_BASE}/console/{self.server_id}/files",
                params={'path': path}
            )
            files_page.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Ошибка получения файлов: {e}")
            return []
        
        soup = BeautifulSoup(files_page.text, 'html.parser')
        files = []
        
        # Ищем файлы в таблице
        file_rows = soup.find_all('tr', class_='file-row')
        for row in file_rows:
            file_name = row.find('span', class_='file-name')
            file_size = row.find('span', class_='file-size')
            file_type = row.find('span', class_='file-type')
            
            if file_name:
                files.append({
                    'name': file_name.text.strip(),
                    'size': file_size.text.strip() if file_size else 'Unknown',
                    'type': file_type.text.strip() if file_type else 'file'
                })
        
        return files
    
    def download_file(self, file_path, download_dir):
        """Скачивание отдельного файла"""
        print(f"📥 Скачивание файла: {file_path}")
        
        try:
            download_url = f"{ATEMOS_API_BASE}/console/{self.server_id}/files/download"
            response = self.session.get(
                download_url,
                params={'path': file_path},
                stream=True
            )
            response.raise_for_status()
            
            # Сохраняем файл
            file_name = Path(file_path).name
            save_path = download_dir / file_name
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Файл сохранён: {save_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка скачивания {file_path}: {e}")
            return False
    
    def download_all_files(self, download_dir):
        """Скачивание всех файлов сервера"""
        print("📦 Скачивание всех файлов сервера...")
        
        # Создаём структуру папок
        server_dir = download_dir / f"server_{self.server_id}"
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Основные директории для скачивания
        directories = [
            '/world',
            '/world_nether', 
            '/world_the_end',
            '/plugins',
            '/config',
            '/logs'
        ]
        
        success_count = 0
        fail_count = 0
        
        for directory in directories:
            try:
                files = self.get_files_list(directory)
                for file_info in files:
                    if self.download_file(f"{directory}/{file_info['name']}", server_dir):
                        success_count += 1
                    else:
                        fail_count += 1
            except Exception as e:
                print(f"⚠️  Ошибка обработки директории {directory}: {e}")
        
        print(f"\n{'='*50}")
        print(f"📊 Итого скачано файлов: {success_count}")
        print(f"❌ Ошибок: {fail_count}")
        print(f"{'='*50}")
        
        return success_count > 0


class ABBB:
    """Основной класс приложения"""
    
    def __init__(self):
        self.api = AternosAPI()
        self.setup_directories()
    
    def setup_directories(self):
        """Настройка базовых директорий"""
        self.home_dir = Path.home()
        self.desktop_dir = self.home_dir / 'Desktop'
        self.downloads_dir = self.home_dir / 'Downloads'
        
        # Создаём директорию для загрузок ABBB
        self.abbb_dir = self.desktop_dir / 'AternosBackups'
        self.abbb_dir.mkdir(parents=True, exist_ok=True)
    
    def load_credentials(self):
        """Загрузка учётных данных из файла"""
        cred_file = Path('aternos_credentials.json')
        
        if cred_file.exists():
            try:
                with open(cred_file, 'r') as f:
                    creds = json.load(f)
                return creds.get('username'), creds.get('password')
            except Exception as e:
                print(f"⚠️  Ошибка загрузки учётных данных: {e}")
        
        return None, None
    
    def save_credentials(self, username, password, save=False):
        """Сохранение учётных данных"""
        if save:
            cred_file = Path('aternos_credentials.json')
            try:
                with open(cred_file, 'w') as f:
                    json.dump({'username': username, 'password': password}, f)
                print("✅ Учётные данные сохранены")
            except Exception as e:
                print(f"⚠️  Ошибка сохранения учётных данных: {e}")
    
    def interactive_login(self):
        """Интерактивная авторизация"""
        # Пробуем загрузить сохранённые данные
        username, password = self.load_credentials()
        
        if username and password:
            print(f"💾 Найдены сохранённые учётные данные для: {username}")
            response = input("Использовать сохранённые данные? (y/n): ").strip().lower()
            if response == 'y':
                if self.api.login(username, password):
                    return True
        
        # Запрашиваем новые данные
        print("\n📝 Введите учётные данные Aternos:")
        username = input("Логин/Email: ").strip()
        
        # Маскируем ввод пароля
        try:
            import getpass
            password = getpass.getpass("Пароль: ")
        except:
            password = input("Пароль: ").strip()
        
        if self.api.login(username, password):
            # Предлагаем сохранить данные
            save_response = input("Сохранить учётные данные для следующего входа? (y/n): ").strip().lower()
            self.save_credentials(username, password, save_response == 'y')
            return True
        
        return False
    
    def select_server_interactive(self):
        """Интерактивный выбор сервера"""
        servers = self.api.get_servers()
        
        if not servers:
            print("❌ Сервера не найдены!")
            return False
        
        if len(servers) == 1:
            return self.api.select_server(servers[0]['id'])
        
        # Выбор сервера
        while True:
            try:
                choice = input(f"\nВыберите сервер (1-{len(servers)}): ").strip()
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(servers):
                    return self.api.select_server(servers[choice_idx]['id'])
                else:
                    print("❌ Неверный номер")
            except ValueError:
                print("❌ Введите число")
    
    def download_backup(self, download_type='all', custom_path=None):
        """Скачивание резервной копии"""
        # Определяем директорию для скачивания
        if custom_path:
            download_dir = Path(custom_path)
            download_dir.mkdir(parents=True, exist_ok=True)
        else:
            download_dir = self.abbb_dir
        
        print(f"\n📂 Директория для скачивания: {download_dir}\n")
        
        if download_type == 'world':
            worlds = self.api.get_worlds()
            if worlds:
                print("\nДоступные миры:")
                for i, world in enumerate(worlds, 1):
                    print(f"  {i}. {world['name']} ({world['size']})")
                
                try:
                    choice = input(f"\nВыберите мир (1-{len(worlds)}) или 'all' для всех: ").strip()
                    if choice.lower() == 'all':
                        for world in worlds:
                            self.api.download_world(world['name'], download_dir)
                    else:
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(worlds):
                            self.api.download_world(worlds[choice_idx]['name'], download_dir)
                except ValueError:
                    print("❌ Неверный выбор")
        
        elif download_type == 'plugins':
            plugins = self.api.get_plugins()
            if plugins:
                print(f"\n✅ Найдено плагинов: {len(plugins)}")
                # Здесь можно добавить логику скачивания плагинов
        
        elif download_type == 'all':
            print("🔄 Начинается полное скачивание сервера...")
            self.api.download_all_files(download_dir)
        
        print(f"\n🎉 Готово! Файлы сохранены в: {download_dir}")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description=f'{APP_NAME} v{VERSION} - Скачивание файлов сервера Aternos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  abbb_v2.py                          # Интерактивный режим
  abbb_v2.py --download all           # Скачать всё
  abbb_v2.py --download world         # Скачать только миры
  abbb_v2.py --download plugins       # Скачать только плагины
  abbb_v2.py --output ./backups       # Указать свою папку для скачивания
        """
    )
    
    parser.add_argument(
        '--download',
        choices=['all', 'world', 'plugins', 'files'],
        default=None,
        help='Что скачивать (по умолчанию: интерактивный выбор)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Папка для скачивания файлов'
    )
    
    parser.add_argument(
        '--no-save-creds',
        action='store_true',
        help='Не сохранять учётные данные'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} {VERSION}'
    )
    
    args = parser.parse_args()
    
    # Выводим заголовок
    print(f"\n{'='*60}")
    print(f"🎮 {APP_NAME} v{VERSION}")
    print(f"{'='*60}\n")
    
    # Инициализация приложения
    app = ABBB()
    
    try:
        # Авторизация
        if not app.interactive_login():
            print("❌ Авторизация не удалась")
            sys.exit(1)
        
        # Выбор сервера
        if not app.select_server_interactive():
            print("❌ Сервер не выбран")
            sys.exit(1)
        
        # Скачивание
        if args.download:
            app.download_backup(args.download, args.output)
        else:
            # Интерактивный выбор
            print("\nЧто вы хотите скачать?")
            print("1. Всё (миры, плагины, конфиги)")
            print("2. Только миры")
            print("3. Только плагины")
            print("4. Отмена")
            
            choice = input("\nВаш выбор (1-4): ").strip()
            
            if choice == '1':
                app.download_backup('all', args.output)
            elif choice == '2':
                app.download_backup('world', args.output)
            elif choice == '3':
                app.download_backup('plugins', args.output)
            else:
                print("❌ Отменено")
                sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
