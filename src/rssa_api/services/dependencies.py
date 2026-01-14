from typing import Annotated

from fastapi import Depends
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantRecommendationContextRepository,
    StudyParticipantRepository,
)

from rssa_api.data.moviedb import get_repository as movie_repo_factory
from rssa_api.data.rssadb import get_repository as rssa_repo_factory

from .recommender_service import RecommenderService


def get_recommender_service(
    participant_repo: Annotated[
        StudyParticipantRepository,
        Depends(rssa_repo_factory(StudyParticipantRepository)),
    ],
    rating_repo: Annotated[
        ParticipantRatingRepository,
        Depends(rssa_repo_factory(ParticipantRatingRepository)),
    ],
    interaction_repo: Annotated[
        ParticipantStudyInteractionResponseRepository,
        Depends(rssa_repo_factory(ParticipantStudyInteractionResponseRepository)),
    ],
    rec_ctx_repo: Annotated[
        ParticipantRecommendationContextRepository,
        Depends(rssa_repo_factory(ParticipantRecommendationContextRepository)),
    ],
    movie_repo: Annotated[
        MovieRepository,
        Depends(movie_repo_factory(MovieRepository)),
    ],
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
