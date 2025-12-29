from core.db import repository

def get_user_subscription(user_id: str):
    """
    Obtiene la información de suscripción del usuario desde MySQL.
    
    Args:
        user_id: UUID del usuario
        
    Returns:
        Dict con información de suscripción o None si no existe
    """
    if not user_id:
        raise ValueError("user_id es requerido")

    # Query basada en la estructura real de la tabla subscriptions
    query = """
        SELECT 
            id,
            user_id,
            plan_name,
            status,
            current_period_start,
            current_period_end,
            trial_start,
            trial_end,
            cancelled_at,
            ends_at,
            CASE 
                WHEN status = 'active' 
                    AND (current_period_end IS NULL OR current_period_end > NOW())
                    AND (cancelled_at IS NULL OR ends_at IS NULL OR ends_at > NOW())
                THEN 1 
                ELSE 0 
            END as has_active_subscription
        FROM subscriptions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """

    subscription = repository.fetch_one(query, (user_id,))
    
    if subscription:
        subscription["has_active_subscription"] = bool(subscription["has_active_subscription"])
    
    return subscription

