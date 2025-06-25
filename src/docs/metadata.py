from enum import Enum
from typing import Any, Dict, List


class ResourceTagsEnum(Enum):
	movie = 'Resource: Movie'
	study = 'Resource: Study'
	survey = 'Resource: Survey'
	response = 'Resource: Response'
	participant = 'Resouce: Participant'
	feedback = 'Resource: Feedback'


class AdminTagsEnum(Enum):
	movie = 'Admin: Movie'
	study = 'Admin: Study'
	survey = 'Survey'
	response = 'Response'
	participant = 'Participant'
	feedback = 'feedback'


class RSTagsEnum(Enum):
	rssa = 'Recommender System for Self Actualization'


tags_metadata: List[Dict[str, Any]] = [
	{
		'name': ResourceTagsEnum.movie.value,
		'description': 'This is the movie dataset adapated from the MovieLens dataset of IMDB movies.',
		'externalDocs': {
			'description': 'Movielens Dataset can be found at the MovieLens website.',
			'url': 'https://grouplens.org/datasets/movielens/',
		},
	},
	{
		'name': ResourceTagsEnum.study.value,
		'description': 'The study API is a study meta API that is used to create and manage the study.'
		+ 'As such, it is only available to admin users.',
	},
	{
		'name': ResourceTagsEnum.participant.value,
		'description': 'The user API is used to record study participant responses.',
	},
	{
		'name': AdminTagsEnum.study.value,
		'description': '',
	},
]


class AppMetadata:
	title = 'RSSA Project API'
	summary = 'API for all the RSSA projects, experiments, and alternate movie databases.'
	description = """
		This API is a FastAPI based API that is used to manage the RSSA project. 
		The API is used to manage the study, the participants, the movies, 
		the preference communities, and the preference visualizations. 
		The API is also used to manage the metadata for the study.
	"""
