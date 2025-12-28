from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ===== ENUMS ESPECÍFICOS DE ESTOICISMO =====

class AgeRange(str, Enum):
    """Rangos de edad"""
    TEEN = "13-17"
    YOUNG_ADULT = "18-25"
    YOUNG_ADULT_ALT = "18-24"  # Variante Laravel
    ADULT = "26-35"
    ADULT_ALT = "25-34"  # Variante Laravel
    MIDDLE_AGE = "36-50"
    MIDDLE_AGE_ALT = "35-44"  # Variante Laravel
    SENIOR = "51+"
    SENIOR_ALT = "45+"  # Variante Laravel


class Gender(str, Enum):
    """Género"""
    MALE = "masculino"
    FEMALE = "femenino"
    NON_BINARY = "no_binario"
    PREFER_NOT_SAY = "prefiero_no_decir"


class StoicLevel(str, Enum):
    """Nivel de conocimiento en estoicismo"""
    BEGINNER = "principiante"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"
    MASTER = "maestro"


class SpiritualPracticeLevel(str, Enum):
    """Nivel de práctica espiritual general (coincide con BD)"""
    NONE = "ninguna"
    OCCASIONAL = "ocasional"
    BEGINNER = "principiante"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"
    MODERATE = "moderada"


class PracticeFrequency(str, Enum):
    """Frecuencia de práctica espiritual"""
    NEVER = "nunca"
    OCCASIONALLY = "ocasionalmente"
    WEEKLY = "semanalmente"
    DAILY = "diariamente"
    DAILY_ALT = "diaria"  # Variante Laravel
    MULTIPLE_TIMES_DAILY = "varias_veces_al_dia"


class StoicPath(str, Enum):
    """Caminos/pilares del estoicismo (coinciden con valores de BD)"""
    INNER_PEACE = "Paz Interior"
    INNER_PEACE_ALT = "paz interior"  # Variante Laravel lowercase
    INNER_PEACE_UNDERSCORE = "paz_interior" # Variante BD con underscore
    SELF_CONTROL = "Autocontrol"
    SELF_CONTROL_ALT = "autocontrol"  # Variante Laravel lowercase
    WISDOM = "Sabiduría"
    WISDOM_ALT = "sabiduría"  # Variante Laravel lowercase
    WISDOM_NO_ACCENT = "sabiduria"  # Sin acento
    RESILIENCE = "Resiliencia"
    RESILIENCE_ALT = "resiliencia"  # Variante Laravel lowercase
    GRATITUDE = "Gratitud"
    GRATITUDE_ALT = "gratitud"  # Variante Laravel lowercase
    JUSTICE = "Justicia"
    JUSTICE_ALT = "justicia"  # Variante Laravel lowercase
    COURAGE = "Coraje"
    COURAGE_ALT = "coraje"  # Variante Laravel lowercase
    TEMPERANCE = "Templanza"
    TEMPERANCE_ALT = "templanza"  # Variante Laravel lowercase
    VIRTUE = "virtud"  # Variante Laravel - concepto general


class DailyChallenge(str, Enum):
    """Desafíos y prácticas diarias (coinciden con valores de BD)"""
    # Prácticas estoicas
    MORNING_MEDITATION = "meditacion_matutina"
    MEDITATION = "meditación"  # Variante Laravel
    MEDITATION_ALT = "meditacion"  # Sin acento
    EVENING_REFLECTION = "reflexion_nocturna"
    REFLECTION = "reflexión"  # Variante Laravel
    REFLECTION_ALT = "reflexion"  # Sin acento
    STOIC_JOURNAL = "diario_estoico"
    JOURNAL = "diario"  # Variante Laravel
    NEGATIVE_VISUALIZATION = "visualizacion_negativa"

    # Desafíos emocionales
    STRESS = "estres"
    ANXIETY = "ansiedad"
    ANGER = "ira"
    FRUSTRATION = "frustracion"
    SADNESS = "tristeza"
    FEAR = "miedo"

    # Desafíos conductuales
    PROCRASTINATION = "procrastinacion"
    LACK_FOCUS = "falta_de_enfoque"
    RELATIONSHIPS = "relaciones"
    WORK_PRESSURE = "presion_laboral"

    # Práct icas adicionales
    PHYSICAL_EXERCISE = "ejercicio_fisico"  # Variante Laravel

    # Valores adicionales de Laravel
    GRATITUDE_PRACTICE = "gratitud"  # Variante Laravel


# ===== REQUESTS =====

class GenerateExerciseRequest(BaseModel):
    """Request simple para generar ejercicios (solo necesita user_id)"""
    user_id: Optional[str] = Field(
        None,
        description="ID del usuario (temporal hasta implementar JWT)"
    )


class StoicQuizRequest(BaseModel):
    """Request del cuestionario estoico (reemplaza UserProfileRequest genérico)"""

    # Demográficos
    age_range: AgeRange = Field(..., description="Rango de edad del usuario")
    gender: Optional[Gender] = Field(None, description="Género del usuario")
    country: Optional[str] = Field(None, description="País de residencia")

    # Contexto espiritual
    religious_belief: Optional[str] = Field(
        None,
        description="Creencia religiosa o filosófica actual"
    )
    spiritual_practice_level: SpiritualPracticeLevel = Field(
        ...,
        description="Nivel general de práctica espiritual"
    )
    spiritual_practice_frequency: PracticeFrequency = Field(
        ...,
        description="Frecuencia de práctica espiritual"
    )

    # Estoicismo específico
    stoic_level: StoicLevel = Field(
        default=StoicLevel.BEGINNER,
        description="Nivel de conocimiento en filosofía estoica"
    )
    stoic_paths: List[StoicPath] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Caminos/virtudes estoicas de interés (1-4)"
    )

    # Situación personal
    daily_challenges: List[DailyChallenge] = Field(
        ...,
        min_length=1,
        description="Desafíos diarios que enfrenta"
    )

    # Configuración opcional
    num_exercises: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Número de ejercicios a generar"
    )


# ===== RESPONSES =====

class Exercise(BaseModel):
    """Un ejercicio práctico estoico personalizado"""
    name: str = Field(..., description="Nombre del ejercicio")
    level: str = Field(..., description="Nivel estoico: principiante, intermedio, avanzado, maestro")
    objective: str = Field(..., description="Objetivo del ejercicio")
    instructions: str = Field(..., description="Instrucciones claras y prácticas paso a paso")
    duration: str = Field(..., description="Duración del ejercicio (ej: 1 día, 3 días, 1 semana)")
    reflection: str = Field(..., description="Pregunta de reflexión o autoevaluación final")
    source: Optional[str] = Field(
        None,
        description="Fuente del libro estoico de donde se obtuvo el ejercicio"
    )


class GenerateExercisesResponse(BaseModel):
    """Respuesta con ejercicios estoicos personalizados"""
    user_profile_summary: str = Field(
        ...,
        description="Resumen del perfil del usuario"
    )
    topic: str = Field(
        default="estoicismo",
        description="Tema (siempre estoicismo en este sistema)"
    )
    exercises: List[Exercise] = Field(
        ...,
        description="Lista de ejercicios estoicos personalizados"
    )


# ===== LEGACY (Mantener por compatibilidad si es necesario) =====

class KnowledgeLevel(str, Enum):
    """DEPRECATED: Usar StoicLevel en su lugar"""
    BEGINNER = "principiante"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"
