"""Сервис для расчета стоимости заказов"""
from typing import Dict


def calculate_order_price(
    price_per_hour: float,
    duration_hours: float,
    participants_count: int
) -> Dict[str, float]:
    """
    Расчет стоимости заказа
    
    Формула:
    - Базовая цена = цена_за_час × продолжительность
    - Доплата за участников = базовая_цена × 50% × (количество_участников - 1)
    - Итого = базовая_цена + доплата
    
    Args:
        price_per_hour: Цена за час (аудио или видео)
        duration_hours: Продолжительность в часах
        participants_count: Количество участников
    
    Returns:
        Словарь с расчетом:
        {
            'base_price': базовая цена,
            'additional_participants_price': доплата за участников,
            'total_price': итоговая цена
        }
    """
    base_price = price_per_hour * duration_hours
    
    # Доплата за дополнительных участников (50% за каждого, кроме первого)
    additional_participants = participants_count - 1
    if additional_participants > 0:
        additional_participants_price = base_price * 0.5 * additional_participants
    else:
        additional_participants_price = 0.0
    
    total_price = base_price + additional_participants_price
    
    return {
        'base_price': round(base_price, 2),
        'additional_participants_price': round(additional_participants_price, 2),
        'total_price': round(total_price, 2)
    }


def format_price_calculation(
    price_per_hour: float,
    duration_hours: float,
    participants_count: int,
    calculation: Dict[str, float]
) -> str:
    """
    Форматирование расчета стоимости для отображения пользователю
    
    Returns:
        Отформатированная строка с расчетом
    """
    lines = [
        f"💰 Расчет стоимости:",
        f"• Базовая цена: {price_per_hour:.0f}₽/час × {duration_hours:.0f} ч. = {calculation['base_price']:.0f}₽"
    ]
    
    if calculation['additional_participants_price'] > 0:
        additional = participants_count - 1
        lines.append(
            f"• Доплата за {additional} доп. участников: "
            f"{calculation['base_price']:.0f}₽ × 50% × {additional} = "
            f"{calculation['additional_participants_price']:.0f}₽"
        )
    
    lines.append(f"• Итого: {calculation['total_price']:.0f}₽")
    
    return "\n".join(lines)

