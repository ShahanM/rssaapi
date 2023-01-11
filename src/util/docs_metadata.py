from enum import Enum

class TagsMetadataEnum(Enum):
	movie = 'movie'
	ers = 'ers movie'
	cybered = 'cybered movie'
	user = 'user'
	study = 'study'
	step = 'step'
	page = 'page'
	question = 'survey question'
	admin = 'admin'

tags_metadata = [
    {
        'name': TagsMetadataEnum.movie.value,
        'description': ''
    },
    {
        'name': TagsMetadataEnum.ers.value,
        'description': ''
    },
    {
        'name': TagsMetadataEnum.cybered.value,
        'description': '',
        'externalDocs': {
            'description': 'Items external docs',
            'url': 'https://fastapi.tiangolo.com/',
        }
    },
    {
        'name': TagsMetadataEnum.user.value,
        'description': ''
    },
    {
        'name': TagsMetadataEnum.study.value,
        'description': ''
    },
    {
        'name': TagsMetadataEnum.step.value,
        'description': ''
    },
	{
		'name': TagsMetadataEnum.page.value,
		'description': ''
	},
	{
		'name': TagsMetadataEnum.question.value,
		'description': ''
	},
    {
        'name': TagsMetadataEnum.admin.value,
        'description': ''
    }
]