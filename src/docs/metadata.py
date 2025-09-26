from enum import Enum
from typing import Any, Dict, List


class ResourceTagsEnum(Enum):
	movie = 'Resource: Movie'
	study = 'Resource: Study'
	survey = 'Resource: Survey'
	response = 'Resource: Response'
	participant = 'Resouce: Participant'
	feedback = 'Resource: Feedback'


class TagsEnum(Enum):
	movie = 'Admin: Movie'
	study = 'Admin: Study'
	study_step = 'Admin: Study Step'
	survey = 'Admin: Survey'
	construct = 'Admin: Survey Construct'
	response = 'Admin: Response'
	participant = 'Admin: Participant'
	feedback = 'Admin: Feedback'


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
]
