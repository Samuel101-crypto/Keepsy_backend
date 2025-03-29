from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, Form, File, Response
from sqlmodel import select
import os
import tempfile
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .. import database, models, oauth, utils
import requests
from ..config import settings
from datetime import datetime
import io



router = APIRouter(tags=['Events'], prefix="/events")

@router.get("/", response_model=list[models.EventsPublic])
async def get_events(current_user = Depends(oauth.get_current_user), session :  AsyncSession = Depends(database.get_session)):
    events = await session.execute(select(models.Events).where(models.Events.organizer == current_user.email))
    return events.scalars().all()

@router.delete("/{id}")
async def delete_event(id: int = id , current_user = Depends(oauth.get_current_user), session: AsyncSession = Depends(database.get_session)):
    db_record = (await session.execute(select(models.Events).where(models.Events.id == id))).scalar_one_or_none()

    if db_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There is no such event!")
    
    url = settings.tusky_files_url + db_record.upload_id
    headers = {"Api-Key": settings.api_key,
               "Content-Type": "application/json"}
    
    payload = {
        "parentId": "aaa41f98-f6c4-4f49-9fea-83d95fd80004",
        "status": "deleted",
        "name": ""
    }

    response = requests.patch(url,json=payload, headers=headers)
    if response.status_code == 200:
        print("success")
    await session.delete(db_record)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), organizer: str = Form(...), date_time: str =Form(...), location: str = Form(...),max_tokens: int = Form(...), nft_type: int = Form(...) , nft_description: str = Form(...),event_name: str = Form(...), session: AsyncSession = Depends(database.get_session), current_user = Depends(oauth.get_current_user)):

    try:
        dt = datetime.strptime(date_time, "%d-%m-%Y %H-%M-%S")
        date_time = dt
    except ValueError as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, detail="The date and time was entered in the wrong format!")

    file_bytes = await file.read()
    result= await session.execute(select(models.Users).where(models.Users.email == organizer))
    user_record = result.scalar_one_or_none()
    if user_record is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizer email doesn't exist")
    
    file_type = await utils.validate_file(file.content_type)
    if file_type is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Image is not valid!")

    # Save the incoming file to a temporary file on disk.
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_file_path = tmp.name
        tmp.write(file_bytes)

    file_name = os.path.basename(file.filename)
    file_type = file.content_type

    upload_id = await asyncio.to_thread(utils.process_upload, temp_file_path, file_name, file_type)

    

    file_like = io.BytesIO(file_bytes)

    artwork_attributes = await utils.analyze_artwork(file_like)

    # If upload succeeded, store the data in the database
    if upload_id:
        await utils.store_file_id(upload_id=upload_id, organizer=organizer,location= location,max_tokens= max_tokens,event_name= event_name, artwork_attributes=artwork_attributes,nft_description=nft_description ,date_time=date_time, nft_type=nft_type ,session=session)
        return {"message": f"File '{file_name}' uploaded successfully with ID: {upload_id}"}
    else:
        return {"message": "Upload failed", "error": "Could not process the file"}
    
    