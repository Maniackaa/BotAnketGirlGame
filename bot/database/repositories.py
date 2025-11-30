"""Репозитории для работы с базой данных"""
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from bot.database.models import (
    User, Profile, Game, ProfileGame, Order, ReminderTask
)


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    @staticmethod
    async def get_or_create(session: AsyncSession, telegram_id: int, 
                           username: Optional[str] = None, 
                           first_name: Optional[str] = None) -> User:
        """Получить или создать пользователя"""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user
    
    @staticmethod
    async def accept_rules(session: AsyncSession, user_id: int):
        """Принять правила пользователем"""
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one()
        user.rules_accepted = True
        user.rules_accepted_at = datetime.utcnow()
        await session.commit()


class ProfileRepository:
    """Репозиторий для работы с анкетами"""
    
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Profile]:
        """Получить все анкеты"""
        result = await session.execute(
            select(Profile).options(selectinload(Profile.games).selectinload(ProfileGame.game))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_id(session: AsyncSession, profile_id: int) -> Optional[Profile]:
        """Получить анкету по ID"""
        result = await session.execute(
            select(Profile)
            .where(Profile.id == profile_id)
            .options(selectinload(Profile.games).selectinload(ProfileGame.game))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_game(session: AsyncSession, game_id: int) -> List[Profile]:
        """Получить анкеты по игре"""
        result = await session.execute(
            select(Profile)
            .join(ProfileGame)
            .where(ProfileGame.game_id == game_id)
            .options(selectinload(Profile.games).selectinload(ProfileGame.game))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(session: AsyncSession, profile_data: dict) -> Profile:
        """Создать анкету"""
        profile = Profile(**profile_data)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile
    
    @staticmethod
    async def update(session: AsyncSession, profile_id: int, profile_data: dict) -> Optional[Profile]:
        """Обновить анкету"""
        result = await session.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return None
        
        for key, value in profile_data.items():
            setattr(profile, key, value)
        
        profile.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(profile)
        return profile
    
    @staticmethod
    async def delete(session: AsyncSession, profile_id: int) -> bool:
        """Удалить анкету"""
        result = await session.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            await session.delete(profile)
            await session.commit()
            return True
        return False
    
    @staticmethod
    async def add_game(session: AsyncSession, profile_id: int, game_id: int) -> bool:
        """Добавить игру к анкете"""
        # Проверяем, не добавлена ли уже игра
        result = await session.execute(
            select(ProfileGame)
            .where(ProfileGame.profile_id == profile_id)
            .where(ProfileGame.game_id == game_id)
        )
        if result.scalar_one_or_none():
            return False  # Игра уже добавлена
        
        profile_game = ProfileGame(profile_id=profile_id, game_id=game_id)
        session.add(profile_game)
        await session.commit()
        return True
    
    @staticmethod
    async def remove_game(session: AsyncSession, profile_id: int, game_id: int) -> bool:
        """Удалить игру из анкеты"""
        result = await session.execute(
            select(ProfileGame)
            .where(ProfileGame.profile_id == profile_id)
            .where(ProfileGame.game_id == game_id)
        )
        profile_game = result.scalar_one_or_none()
        if profile_game:
            await session.delete(profile_game)
            await session.commit()
            return True
        return False


class GameRepository:
    """Репозиторий для работы с играми"""
    
    @staticmethod
    async def get_all(session: AsyncSession, limit: int = 10, offset: int = 0) -> List[Game]:
        """Получить игры с пагинацией"""
        result = await session.execute(
            select(Game).order_by(Game.name).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def search(session: AsyncSession, query: str) -> List[Game]:
        """Поиск игр по названию"""
        result = await session.execute(
            select(Game).where(Game.name.ilike(f"%{query}%")).order_by(Game.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_id(session: AsyncSession, game_id: int) -> Optional[Game]:
        """Получить игру по ID"""
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(session: AsyncSession, name: str) -> Game:
        """Создать игру"""
        game = Game(name=name)
        session.add(game)
        await session.commit()
        await session.refresh(game)
        return game
    
    @staticmethod
    async def update(session: AsyncSession, game_id: int, name: str) -> Optional[Game]:
        """Обновить название игры"""
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return None
        
        game.name = name
        await session.commit()
        await session.refresh(game)
        return game
    
    @staticmethod
    async def delete(session: AsyncSession, game_id: int) -> bool:
        """Удалить игру"""
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        game = result.scalar_one_or_none()
        if game:
            await session.delete(game)
            await session.commit()
            return True
        return False


class OrderRepository:
    """Репозиторий для работы с заказами"""
    
    @staticmethod
    async def create(session: AsyncSession, order_data: dict) -> Order:
        """Создать заказ"""
        # Генерация номера заказа
        count_result = await session.execute(
            select(func.count(Order.id))
        )
        order_count = count_result.scalar() or 0
        order_number = f"#{order_count + 1}"
        
        order = Order(
            order_number=order_number,
            **order_data
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order
    
    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int) -> List[Order]:
        """Получить заказы пользователя"""
        result = await session.execute(
            select(Order)
            .join(User)
            .where(User.telegram_id == user_id)
            .options(
                selectinload(Order.profile),
                selectinload(Order.game)
            )
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.user),
                selectinload(Order.profile),
                selectinload(Order.game)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Order]:
        """Получить все заказы"""
        result = await session.execute(
            select(Order)
            .options(
                selectinload(Order.user),
                selectinload(Order.profile),
                selectinload(Order.game)
            )
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())


class ReminderTaskRepository:
    """Репозиторий для работы с задачами напоминаний"""
    
    @staticmethod
    async def get_pending_tasks(session: AsyncSession) -> List[ReminderTask]:
        """Получить все невыполненные задачи"""
        result = await session.execute(
            select(ReminderTask)
            .where(ReminderTask.executed == False)
            .where(ReminderTask.scheduled_time > datetime.utcnow())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def mark_as_executed(
        session: AsyncSession,
        task_id: int
    ) -> bool:
        """Отметить задачу как выполненную"""
        result = await session.execute(
            select(ReminderTask).where(ReminderTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.executed = True
            task.executed_at = datetime.utcnow()
            await session.commit()
            return True
        return False
