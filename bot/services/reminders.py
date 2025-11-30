"""Сервис для управления напоминаниями через APScheduler"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.config import TIMEZONE
from bot.database.models import Order, ReminderTask, User, Profile
from bot.database.repositories import OrderRepository
import pytz


class ReminderService:
    """Сервис для управления напоминаниями"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            timezone=pytz.timezone(TIMEZONE)
        )
        self._initialized = False
    
    async def initialize(self, session: AsyncSession):
        """Инициализация сервиса - восстановление задач из БД"""
        if self._initialized:
            return
        
        # Восстановление задач из БД
        result = await session.execute(
            select(ReminderTask)
            .where(ReminderTask.executed == False)
            .where(ReminderTask.scheduled_time > datetime.utcnow())
        )
        tasks = result.scalars().all()
        
        for task in tasks:
            await self._schedule_task_from_db(session, task)
        
        self.scheduler.start()
        self._initialized = True
    
    async def _schedule_task_from_db(
        self,
        session: AsyncSession,
        task: ReminderTask
    ):
        """Восстановление задачи из БД"""
        from sqlalchemy.orm import selectinload
        
        # Получаем заказ
        order_result = await session.execute(
            select(Order)
            .where(Order.id == task.order_id)
            .options(
                selectinload(Order.user),
                selectinload(Order.profile)
            )
        )
        order = order_result.scalar_one_or_none()
        
        if not order:
            return
        
        # Создаем задачу в планировщике
        job_id = task.job_id or str(uuid.uuid4())
        
        if task.task_type == "reminder_15min":
            self.scheduler.add_job(
                self._send_reminder_15min,
                'date',
                run_date=task.scheduled_time,
                id=job_id,
                args=[task.order_id],
                replace_existing=True
            )
        elif task.task_type == "after_meeting":
            self.scheduler.add_job(
                self._send_after_meeting_message,
                'date',
                run_date=task.scheduled_time,
                id=job_id,
                args=[task.order_id],
                replace_existing=True
            )
        elif task.task_type == "check_payment_processing":
            self.scheduler.add_job(
                self._check_payment_processing,
                'date',
                run_date=task.scheduled_time,
                id=job_id,
                args=[task.order_id],
                replace_existing=True
            )
        elif task.task_type == "check_payment_not_paid":
            self.scheduler.add_job(
                self._check_payment_not_paid,
                'date',
                run_date=task.scheduled_time,
                id=job_id,
                args=[task.order_id],
                replace_existing=True
            )
        
        # Обновляем job_id в БД
        task.job_id = job_id
        await session.commit()
    
    async def schedule_order_reminders(
        self,
        session: AsyncSession,
        order: Order
    ):
        """Создание задач напоминаний для заказа"""
        # Напоминание за 15 минут до встречи
        reminder_time = order.date - timedelta(minutes=15)
        if reminder_time > datetime.utcnow():
            await self._create_reminder_task(
                session=session,
                order_id=order.id,
                task_type="reminder_15min",
                scheduled_time=reminder_time
            )
        
        # Сообщение после окончания встречи
        meeting_end_time = order.date + timedelta(hours=order.duration_hours)
        if meeting_end_time > datetime.utcnow():
            await self._create_reminder_task(
                session=session,
                order_id=order.id,
                task_type="after_meeting",
                scheduled_time=meeting_end_time
            )
        
        # Проверка оплаты для статуса "processing" (через 15 минут)
        if order.payment_status == "processing":
            check_time = datetime.utcnow() + timedelta(minutes=15)
            await self._create_reminder_task(
                session=session,
                order_id=order.id,
                task_type="check_payment_processing",
                scheduled_time=check_time
            )
        
        # Проверка оплаты для статуса "not_paid" (через 30 минут)
        if order.payment_status == "not_paid":
            check_time = datetime.utcnow() + timedelta(minutes=30)
            await self._create_reminder_task(
                session=session,
                order_id=order.id,
                task_type="check_payment_not_paid",
                scheduled_time=check_time
            )
    
    async def _create_reminder_task(
        self,
        session: AsyncSession,
        order_id: int,
        task_type: str,
        scheduled_time: datetime
    ):
        """Создание задачи напоминания в БД и планировщике"""
        job_id = str(uuid.uuid4())
        
        # Создаем запись в БД
        task = ReminderTask(
            order_id=order_id,
            task_type=task_type,
            scheduled_time=scheduled_time,
            job_id=job_id
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        
        # Добавляем в планировщик
        if task_type == "reminder_15min":
            self.scheduler.add_job(
                self._send_reminder_15min,
                'date',
                run_date=scheduled_time,
                id=job_id,
                args=[order_id],
                replace_existing=True
            )
        elif task_type == "after_meeting":
            self.scheduler.add_job(
                self._send_after_meeting_message,
                'date',
                run_date=scheduled_time,
                id=job_id,
                args=[order_id],
                replace_existing=True
            )
        elif task_type == "check_payment_processing":
            self.scheduler.add_job(
                self._check_payment_processing,
                'date',
                run_date=scheduled_time,
                id=job_id,
                args=[order_id],
                replace_existing=True
            )
        elif task_type == "check_payment_not_paid":
            self.scheduler.add_job(
                self._check_payment_not_paid,
                'date',
                run_date=scheduled_time,
                id=job_id,
                args=[order_id],
                replace_existing=True
            )
    
    async def _send_reminder_15min(self, order_id: int):
        """Отправка напоминания за 15 минут до встречи"""
        from bot.database.database import async_session_maker
        from bot.database.repositories import OrderRepository
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(
                    selectinload(Order.user),
                    selectinload(Order.profile)
                )
            )
            order = result.scalar_one_or_none()
            if not order or order.reminder_sent or not order.notification_enabled:
                return
            
            user = order.user
            profile = order.profile
            
            # Сообщение пользователю
            user_text = (
                "⏰ Ваша встреча начнётся через 15 минут.\n\n"
                "Переходите по ссылке заранее, чтобы проверить звук и видео.\n"
                "Желаем хорошей игры!"
            )
            
            if order.conference_link:
                user_text += f"\n\n🔗 Ссылка: {order.conference_link}"
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=user_text
            )
            
            # Сообщение девушке (если есть telegram_id в профиле)
            # TODO: Добавить telegram_id в модель Profile если нужно
            
            # Отмечаем как отправленное
            order.reminder_sent = True
            await session.commit()
            
            # Отмечаем задачу как выполненную
            task_result = await session.execute(
                select(ReminderTask)
                .where(ReminderTask.order_id == order_id)
                .where(ReminderTask.task_type == "reminder_15min")
                .where(ReminderTask.executed == False)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.executed = True
                task.executed_at = datetime.utcnow()
                await session.commit()
    
    async def _send_after_meeting_message(self, order_id: int):
        """Отправка сообщения после окончания встречи"""
        from bot.database.database import async_session_maker
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.user))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return
            
            user = order.user
            
            text = (
                "Спасибо за участие в встрече!\n\n"
                "Будем рады видеть вас снова и если понравилось — "
                "посоветуйте нас друзьям 🤗"
            )
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=text
            )
            
            # Отмечаем задачу как выполненную
            task_result = await session.execute(
                select(ReminderTask)
                .where(ReminderTask.order_id == order_id)
                .where(ReminderTask.task_type == "after_meeting")
                .where(ReminderTask.executed == False)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.executed = True
                task.executed_at = datetime.utcnow()
                await session.commit()
    
    async def _check_payment_processing(self, order_id: int):
        """Проверка оплаты для статуса processing"""
        from bot.database.database import async_session_maker
        from bot.services.notifications import send_payment_check_notification
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.user), selectinload(Order.profile))
            )
            order = result.scalar_one_or_none()
            
            if not order or order.payment_status != "processing":
                return
            
            await send_payment_check_notification(self.bot, order)
            
            # Отмечаем задачу как выполненную
            task_result = await session.execute(
                select(ReminderTask)
                .where(ReminderTask.order_id == order_id)
                .where(ReminderTask.task_type == "check_payment_processing")
                .where(ReminderTask.executed == False)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.executed = True
                task.executed_at = datetime.utcnow()
                await session.commit()
    
    async def _check_payment_not_paid(self, order_id: int):
        """Проверка оплаты для статуса not_paid"""
        from bot.database.database import async_session_maker
        from bot.services.notifications import send_unpaid_order_notification
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.user), selectinload(Order.profile))
            )
            order = result.scalar_one_or_none()
            
            if not order or order.payment_status != "not_paid":
                return
            
            await send_unpaid_order_notification(self.bot, order)
            
            # Отмечаем задачу как выполненную
            task_result = await session.execute(
                select(ReminderTask)
                .where(ReminderTask.order_id == order_id)
                .where(ReminderTask.task_type == "check_payment_not_paid")
                .where(ReminderTask.executed == False)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.executed = True
                task.executed_at = datetime.utcnow()
                await session.commit()
    
    def shutdown(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()

