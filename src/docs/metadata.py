from enum import Enum

class TagsMetadataEnum(Enum):
	movie = 'movie'
	ers = 'ers movie'
	cybered = 'cybered movie'
	user = 'user'
	study = 'study'
	condition = 'study condition'
	step = 'step'
	page = 'page'
	question = 'survey question'
	admin = 'admin'
	pref_comm = 'preference community'
	pref_viz = 'preference visualization'



tags_metadata = [
	{
		'name': TagsMetadataEnum.movie.value,
		'description': 'This is the movie dataset adapated from the MovieLens dataset of IMDB movies.',
		'externalDocs': {
			'description': 'Movielens Dataset can be found at the MovieLens website.',
			'url': 'https://grouplens.org/datasets/movielens/',
		}
	},
	{
		'name': TagsMetadataEnum.ers.value,
		'description': 'This is the movie dataset with emotional valence ratings from the ERS dataset.'
	},
	{
		'name': TagsMetadataEnum.cybered.value,
		'description': 'This is a truncated version of the Movie dataset with only movies that contain a TV parential rating of PG-13 or lower.' \
			+ 'This dataset was created for the CyberED project.'
	},
	{
		'name': TagsMetadataEnum.user.value,
		'description': 'The user API is used to record study participant responses.'
	},
	{
		'name': TagsMetadataEnum.study.value,
		'description': 'The study API is a study meta API that is used to create and manage the study.' \
			+ 'As such, it is only available to admin users.'
	},
	{
		'name': TagsMetadataEnum.condition.value,
		'description': 'The condition API is used to create and manage the study conditions.'
	},
	{
		'name': TagsMetadataEnum.step.value,
		'description': 'The step API is used to create and manage the study steps (e.g. - consent forms, presurveys, preference elicitations).' \
			+ 'It is part of the study API and is only available to admin users.'
	},
	{
		'name': TagsMetadataEnum.page.value,
		'description': 'The pages API is used to create multiple pages for a step, for example, the several pages of a survey.' \
			+ 'It is part of the study API and is only available to admin users.'
	},
	{
		'name': TagsMetadataEnum.question.value,
		'description': 'The question API is used to create and manage the survey questions.' \
			+ 'It is part of the study API and is only available to admin users.'
	},
	{
		'name': TagsMetadataEnum.admin.value,
		'description': 'These are common admin APIs that are used to manage the databases, study metadeta, and contains all the update and delete APIs.'
	},
	{
		'name': TagsMetadataEnum.pref_comm.value,
		'description': 'These are the APIs used to create and manage the preference communities.'
	},
	{
		'name': TagsMetadataEnum.pref_viz.value,
		'description': 'These are the APIs used to create and manage the preference visualizations.'
	}
]