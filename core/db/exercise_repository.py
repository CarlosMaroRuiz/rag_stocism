from typing import List, Dict, Optional
from core.db import Database
from core.db.repository import BaseRepository
import uuid


class ExerciseRepository(BaseRepository):
    def __init__(self):
        super().__init__(Database())
    
    def create_exercise(self, user_id: str, exercise_data: Dict) -> str:
        """Crea un nuevo ejercicio para el usuario"""
        exercise_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO user_exercises 
            (id, user_id, exercise_name, exercise_level, objective, instructions, 
             duration, reflection, source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """
        
        params = (
            exercise_id,
            user_id,
            exercise_data.get('name'),
            exercise_data.get('level'),
            exercise_data.get('objective'),
            exercise_data.get('instructions'),
            exercise_data.get('duration'),
            exercise_data.get('reflection'),
            exercise_data.get('source')
        )
        
        self.execute(query, params)
        return exercise_id
    
    def create_exercises_batch(self, user_id: str, exercises: List[Dict]) -> List[str]:
        """Crea múltiples ejercicios en un lote"""
        exercise_ids = []
        for exercise in exercises:
            exercise_id = self.create_exercise(user_id, exercise)
            exercise_ids.append(exercise_id)
        return exercise_ids
    
    def get_pending_exercises_count(self, user_id: str) -> int:
        """Cuenta cuántos ejercicios pendientes tiene el usuario"""
        query = """
            SELECT COUNT(*) as count 
            FROM user_exercises 
            WHERE user_id = %s AND status IN ('pending', 'in_progress')
        """
        result = self.fetch_one(query, (user_id,))
        return result['count'] if result else 0
    
    def get_user_exercises(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Obtiene los ejercicios del usuario, opcionalmente filtrados por estado"""
        if status:
            query = """
                SELECT * FROM user_exercises 
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
            """
            params = (user_id, status)
        else:
            query = """
                SELECT * FROM user_exercises 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            params = (user_id,)
        
        return self.fetch_all(query, params)
    
    def mark_exercise_completed(self, exercise_id: str, user_id: str) -> bool:
        """Marca un ejercicio como completado"""
        query = """
            UPDATE user_exercises 
            SET status = 'completed', completed_at = NOW()
            WHERE id = %s AND user_id = %s
        """
        rows_affected = self.execute(query, (exercise_id, user_id))
        return rows_affected > 0
    
    def get_exercise_by_id(self, exercise_id: str, user_id: str) -> Optional[Dict]:
        """Obtiene un ejercicio específico del usuario"""
        query = """
            SELECT * FROM user_exercises 
            WHERE id = %s AND user_id = %s
        """
        return self.fetch_one(query, (exercise_id, user_id))
    
    def should_generate_new_exercises(self, user_id: str, required_count: int = 5) -> bool:
        """Verifica si se deben generar nuevos ejercicios"""
        pending_count = self.get_pending_exercises_count(user_id)
        return pending_count < required_count
    
    def get_completed_exercises_count(self, user_id: str) -> int:
        """Cuenta cuántos ejercicios completados tiene el usuario"""
        query = """
            SELECT COUNT(*) as count 
            FROM user_exercises 
            WHERE user_id = %s AND status = 'completed'
        """
        result = self.fetch_one(query, (user_id,))
        return result['count'] if result else 0

