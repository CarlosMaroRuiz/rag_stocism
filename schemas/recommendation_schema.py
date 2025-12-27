from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ===== ENUMS ESPECÍFICOS DE ESTOICISMO =====

class AgeRange(str, Enum):
    """Rangos de edad"""
    TEEN = "13-17"
    YOUNG_ADULT = "18-25"
    ADULT = "26-35"
    MIDDLE_AGE = "36-50"
    SENIOR = "51+"


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


class PracticeFrequency(str, Enum):
    """Frecuencia de práctica espiritual"""
    NEVER = "nunca"
    OCCASIONALLY = "ocasionalmente"
    WEEKLY = "semanalmente"
    DAILY = "diariamente"
    MULTIPLE_TIMES_DAILY = "varias_veces_al_dia"


class StoicPath(str, Enum):
    """Caminos/pilares del estoicismo (coinciden con valores de BD)"""
    INNER_PEACE = "Paz Interior"
    SELF_CONTROL = "Autocontrol"
    WISDOM = "Sabiduría"
    RESILIENCE = "Resiliencia"
    GRATITUDE = "Gratitud"
    JUSTICE = "Justicia"
    COURAGE = "Coraje"
    TEMPERANCE = "Templanza"


class DailyChallenge(str, Enum):
    """Desafíos y prácticas diarias (coinciden con valores de BD)"""
    # Prácticas estoicas
    MORNING_MEDITATION = "meditacion_matutina"
    EVENING_REFLECTION = "reflexion_nocturna"
    STOIC_JOURNAL = "diario_estoico"
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


# ===== REQUESTS =====

class GenerateRecommendationRequest(BaseModel):
    """Request simple para generar recomendaciones (solo necesita user_id)"""
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
    num_recommendations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Número de recomendaciones a generar"
    )


# ===== RESPONSES =====

class Recommendation(BaseModel):
    """Una recomendación/enseñanza estoica"""
    title: str = Field(..., description="Título de la enseñanza estoica")
    content: str = Field(..., description="Explicación detallada y ejercicio práctico")
    source_reference: Optional[str] = Field(
        None,
        description="Cita del texto estoico (Marco Aurelio, Epicteto, Séneca)"
    )
    difficulty: str = Field(
        ...,
        description="Nivel de dificultad: fácil, intermedio, difícil"
    )
    stoic_virtue: Optional[StoicPath] = Field(
        None,
        description="Virtud/camino estoico relacionado"
    )


class GenerateRecommendationsResponse(BaseModel):
    """Respuesta con recomendaciones estoicas personalizadas"""
    user_profile_summary: str = Field(
        ...,
        description="Resumen del perfil del usuario"
    )
    topic: str = Field(
        default="estoicismo",
        description="Tema (siempre estoicismo en este sistema)"
    )
    recommendations: List[Recommendation] = Field(
        ...,
        description="Lista de enseñanzas estoicas personalizadas"
    )


# ===== LEGACY (Mantener por compatibilidad si es necesario) =====

class KnowledgeLevel(str, Enum):
    """DEPRECATED: Usar StoicLevel en su lugar"""
    BEGINNER = "principiante"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"
