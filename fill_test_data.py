"""Скрипт для заполнения базы данных тестовыми данными"""
import asyncio
import sys
import io

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bot.database.database import init_db, close_db, async_session_maker
from bot.database.repositories import GameRepository, ProfileRepository
from bot.database.models import ProfileGame


async def fill_test_data():
    """Заполнение базы данных тестовыми данными"""
    # Инициализация БД
    await init_db()
    print("✅ База данных инициализирована")
    
    async with async_session_maker() as session:
        # Список игр для добавления
        games_data = [
            "Dota 2",
            "League of Legends",
            "Counter-Strike 2",
            "Valorant",
            "Apex Legends",
            "Minecraft",
            "Garry's Mod",
            "Terraria",
            "Rainbow Six Siege",
            "Heroes of the Storm",
            "Warframe",
            "StarCraft II",
            "Total War",
            "Path of Exile",
            "Diablo IV",
            "Satisfactory",
            "Factorio",
            "Rust",
            "Subnautica",
            "Roblox",
            "ARK: Survival Evolved",
            "GTA V",
            "Forza Horizon",
            "BeamNG.drive",
            "Euro Truck Simulator 2",
            "Дурак",
            "R.E.P.O.",
        ]
        
        print("🎮 Добавление игр...")
        created_games = {}
        for game_name in games_data:
            try:
                game = await GameRepository.create(session, game_name)
                created_games[game_name] = game
                print(f"  ✅ {game_name}")
            except Exception as e:
                # Игра уже существует, получаем её из БД
                from sqlalchemy import select
                from bot.database.models import Game
                result = await session.execute(
                    select(Game).where(Game.name == game_name)
                )
                existing_game = result.scalar_one_or_none()
                if existing_game:
                    created_games[game_name] = existing_game
                print(f"  ⚠️ {game_name} (уже существует)")
        
        # Список анкет для добавления
        profiles_data = [
            {
                "name": "Lola",
                "age": 18,
                "description": "♡ Привет! Меня зовут Лола. Со мной ты сможешь расслабиться и поиграть в доту, посмотреть аниме или новый видос азазина, а может ты просто хочешь пообщаться? Я уже жду тебя в дискордике! ♡",
                "audio_chat_price": 500.0,
                "video_chat_price": 1600.0,
                "private_price": 1000.0,
                "channel_link": "@etlola",
                "games": ["Dota 2"],
                "photo_ids": ["test_photo_1", "test_photo_2", "test_photo_3"]  # Заглушки, реальные file_id нужно будет заменить
            },
            {
                "name": "Kaya",
                "age": 20,
                "description": "Привет! Я Кая, люблю играть в CS:GO и Valorant. Готова составить тебе компанию в игре или просто пообщаться! 😊",
                "audio_chat_price": 600.0,
                "video_chat_price": 1800.0,
                "private_price": 1200.0,
                "channel_link": "@kayaetime",
                "games": ["Counter-Strike 2", "Valorant"],
                "photo_ids": ["test_photo_4", "test_photo_5", "test_photo_6"]
            },
            {
                "name": "Maya",
                "age": 22,
                "description": "Хей! Меня зовут Мая. Обожаю Minecraft и Terraria, могу строить с тобой или просто поболтать о жизни. Жду тебя! 💕",
                "audio_chat_price": 450.0,
                "video_chat_price": 1400.0,
                "private_price": None,
                "channel_link": "@mayagame",
                "games": ["Minecraft", "Terraria"],
                "photo_ids": ["test_photo_7", "test_photo_8", "test_photo_9"]
            },
            {
                "name": "Sofia",
                "age": 19,
                "description": "Привет! Я София, фанатка League of Legends. Готова сыграть с тобой в ранкед или просто пообщаться в дискорде! 🎮",
                "audio_chat_price": 550.0,
                "video_chat_price": 1700.0,
                "private_price": 1100.0,
                "channel_link": "@sofialol",
                "games": ["League of Legends"],
                "photo_ids": ["test_photo_10", "test_photo_11", "test_photo_12"]
            },
            {
                "name": "Anna",
                "age": 21,
                "description": "Хай! Я Анна, люблю Apex Legends и Warframe. Могу составить компанию в игре или просто пообщаться о гейминге! 🔥",
                "audio_chat_price": 650.0,
                "video_chat_price": 1900.0,
                "private_price": 1300.0,
                "channel_link": "@annagaming",
                "games": ["Apex Legends", "Warframe"],
                "photo_ids": ["test_photo_13", "test_photo_14", "test_photo_15"]
            },
        ]
        
        print("\n👤 Добавление анкет...")
        for profile_data in profiles_data:
            try:
                # Извлекаем игры
                games = profile_data.pop("games")
                
                # Создаем анкету
                profile = await ProfileRepository.create(session, profile_data)
                print(f"  ✅ {profile.name} ({profile.age} лет)")
                
                # Добавляем игры к анкете
                for game_name in games:
                    if game_name in created_games:
                        game = created_games[game_name]
                        game_id = game.id if hasattr(game, 'id') else game["id"]
                        await ProfileRepository.add_game(session, profile.id, game_id)
                        print(f"    🎮 Добавлена игра: {game_name}")
                
            except Exception as e:
                print(f"  ❌ Ошибка при создании анкеты {profile_data.get('name', 'Unknown')}: {e}")
        
        await session.commit()
        print("\n✅ Тестовые данные успешно добавлены!")
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(fill_test_data())

