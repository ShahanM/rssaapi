from rssa_api.data.repositories.dependencies import (
    StudyParticipantRepositoryDep,
    ParticipantRatingRepositoryDep,
    ParticipantStudyInteractionResponseRepositoryDep,
    ParticipantRecommendationContextRepositoryDep,
)
from rssa_api.data.repositories.content_dependencies import MovieRepositoryDep
from .recommender_service import RecommenderService
from fastapi import Depends
from typing import Annotated

def get_recommender_service(
    participant_repo: StudyParticipantRepositoryDep,
    rating_repo: ParticipantRatingRepositoryDep,
    movie_repo: MovieRepositoryDep,
    interaction_repo: ParticipantStudyInteractionResponseRepositoryDep,
    rec_ctx_repo: ParticipantRecommendationContextRepositoryDep,
) -> RecommenderService:
    """Get RecommenderService dependency."""
    return RecommenderService(
        participant_repo,
        rating_repo,
        movie_repo,
        interaction_repo,
        rec_ctx_repo,
    )


RecommenderServiceDep = Annotated[RecommenderService, Depends(get_recommender_service)]
