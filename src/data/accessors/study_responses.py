from typing import List, Union, Dict
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from ..models.schema.participanschema import *
from ..models.study_v2 import *
from ..models.survey_constructs import *
from ..models.participants import *

from .studies import get_study_by_id, get_study_conditions

from data.rssadb import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, and_, or_, select
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import HTTPException

import random


def get_responses(db: Session, participant: Participant,\
	construct_id: uuid.UUID, item_ids: List[uuid.UUID]) -> Dict[uuid.UUID, ParticipantResponse]:

	if not item_ids: return {}

	reponses = db.query(ParticipantResponse).\
		where(and_(ParticipantResponse.participant_id == participant.id,\
			ParticipantResponse.construct_id == construct_id,\
			ParticipantResponse.item_id.in_(item_ids))).all()
	
	if not reponses: return {}

	return {res.item_id: res for res in reponses}



def create_survey_response(db: Session, participant_id: uuid.UUID,\
	response: SurveyResponse) -> bool:
	
	participant = db.query(Participant).where(Participant.id == participant_id).first()
	if not participant:
		raise HTTPException(status_code=404, detail='Participant not found')
	
	pcontent = db.query(PageContent).where(PageContent.page_id == response.page_id).first()
	res = get_responses(db, participant, pcontent.content_id, [resItem.item_id for resItem in response.responses])

	if res:
		for resItem in response.responses:
			if resItem.item_id in res:
				if res[resItem.item_id].response != resItem.response:
					res[resItem.item_id].response = resItem.response
					res[resItem.item_id].date_modified = datetime.now(timezone.utc)
					db.add(res[resItem.item_id])
		db.commit()
		return True
	
	presponses = []
	for resItem in response.responses:
		
		presponse = ParticipantResponse(participant_id=participant.id,\
				construct_id=pcontent.content_id,\
				response=resItem.response,\
				item_id=resItem.item_id)
		
		presponses.append(presponse)
	
	db.add_all(presponses)
	db.flush()
	db.commit()
	
	if all([True for res in presponses if res.id]): return True

	return False
