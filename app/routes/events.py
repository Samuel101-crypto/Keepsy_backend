from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, Form, File
from sqlmodel import select
import os
import tempfile
import time
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .. import database, models, oauth
import requests
from ..config import settings
# Configuration for the TUS upload
from tusclient import client
import io
import numpy as np
import cv2
from sklearn.cluster import KMeans


router = APIRouter(tags=['Events'], prefix="/events")

async def validate_file(file_type):
    accepted_types = ["image/jpeg", "image/png", "image/gif"]
    return file_type in accepted_types

async def upload_file(filebytes, file_type):
    publisher_url = settings.publisher_url
    print(file_type)
    headers = {"Content-Type": f"{file_type}",
               "Authorization": f"api-Key {settings.api_key}"}
    print(settings.api_key)
    print(type(settings.api_key))
    
    response = requests.post(publisher_url, data=filebytes, headers=headers)

    if response.status_code == 200:
        # blob_id = response.json().get("blob_id")
        # print(f"media uploaded successfully")
        # return blob_id
        print(response)
    
    else:
        print("Failed to upload media")
        print(f"Error: {response.status_code}")
        return None


# @router.post("/")
# async def create_event(file: Optional[UploadFile] = Form(...),event: str = Form(None), session: AsyncSession = Depends(database.get_session)):
#     if not file: 
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artwork is required!")
    
#     if not validate_file(file.content_type):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artwork type is not jpeg, png or gif!")
#     event = json.loads(event)
#     print(event)
#     print(type(event))

#     try:
#         event = models.EventCreate(**event)
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")
    
#     file_content = await file.read()

#     blob_id = await upload_file(file_content, file.content_type)
#     # if blob_id == None:
#     #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to upload media")



#     return {"file": file.filename}





# --- TUS Upload Configuration ---
publisher_url = settings.publisher_url
API_KEY = settings.api_key
VAULT_ID = settings.vault_id

async def store_file_id(upload_id:str , organizer:str, location:str, max_tokens:str, event_name: str, artwork_attributes:dict, session: AsyncSession):
    new_event= models.Events(organizer=organizer, location=location, max_tokens=max_tokens, upload_id=upload_id, event_name=event_name, artwork_attributes=artwork_attributes)
    session.add(new_event)
    await session.commit()
    print("Success!")

async def analyze_artwork(file_obj):
    try:
        file_bytes = file_obj.read()
        file_array = np.asarray(bytearray(file_bytes), dtype=np.uint8)
        image = cv2.imdecode(file_array, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode image, Ensure the image is valid!")
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channels = image.shape

        pixels = image.reshape((-1, 3))
        num_clusters = 3
        kmeans =    KMeans(n_clusters=num_clusters, random_state=42)
        kmeans.fit(pixels)
        dominant_colors = kmeans.cluster_centers_.astype(int)

        label, counts = np.unique(kmeans.labels_, return_counts=True)
        proportions = counts / counts.sum()

        colors_info = []
        for i, center in enumerate(dominant_colors):
            colors_info.append({
                "red":int(center[0]),
                "blue":int(center[1]),
                "green":int(center[2]),
                "proportion":float(proportions[i]),
            })
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        avg_brightness = float(np.mean(gray))

        attributes = {
            "dimensions": {"width": width, "height": height},
            "dominant_colors": colors_info,
            "average_brightness": avg_brightness
        }

        return attributes
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error analyzing artwork: {e}")

def process_upload(file_path: str, file_name: str, file_type: str) -> str | None:
    """
    Synchronous upload process using tuspy.
    Returns the upload_id if successful, None if failed.
    """
    file_size = os.stat(file_path).st_size
    headers = {"Api-Key": API_KEY}
    tus_client = client.TusClient(publisher_url, headers=headers)

    metadata = {
        "filename": file_name,
        "filetype": file_type,
        "vaultId": VAULT_ID
    }

    chunk_size = 1024 * 1024  # 1 MB
    uploader = tus_client.uploader(file_path=file_path, metadata=metadata, chunk_size=chunk_size)

    try:
        while uploader.offset < file_size:
            uploader.upload_chunk()
            percentage = (uploader.offset / file_size) * 100
            print(f"Progress: {percentage:.2f}% ({uploader.offset}/{file_size} bytes)")
            time.sleep(0.1)  # Pause between chunks
        print("Upload completed successfully!")
        # Extract the file ID from the uploader URL
        file_id = uploader.url.split("/")[-1]
        print("File uploaded with id:", file_id)
        return file_id  # Return the upload_id
    except Exception as e:
        print(f"Upload failed: {e}")
        return None
    finally:
        # Close uploader file handle if open
        try:
            if hasattr(uploader, "_file") and uploader._file:
                uploader._file.close()
        except Exception as close_exc:
            print("Error closing uploader file:", close_exc)
        # Allow time for OS to release file handles, then attempt to remove the temp file
        time.sleep(0.5)
        for attempt in range(5):
            try:
                os.remove(file_path)
                print("Temporary file removed.")
                break
            except PermissionError as remove_exc:
                print(f"Attempt {attempt+1}: Error removing temporary file: {remove_exc}")
                time.sleep(0.5)
        else:
            print("Failed to remove temporary file after multiple attempts.")

@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), organizer: str = Form(...), location: str = Form(...),max_tokens: int = Form(...), event_name: str = Form(...), session: AsyncSession = Depends(database.get_session), current_user = Depends(oauth.get_current_user)):

    file_bytes = await file.read()
    result= await session.execute(select(models.Users).where(models.Users.email == organizer))
    user_record = result.scalar_one_or_none()
    if user_record is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizer email doesn't exist")
    
    file_type = await validate_file(file.content_type)
    if file_type is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Image is not valid!")

    # Save the incoming file to a temporary file on disk.
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_file_path = tmp.name
        tmp.write(file_bytes)

    file_name = os.path.basename(file.filename)
    file_type = file.content_type

    upload_id = await asyncio.to_thread(process_upload, temp_file_path, file_name, file_type)

    

    file_like = io.BytesIO(file_bytes)

    artwork_attributes = await analyze_artwork(file_like)

    # If upload succeeded, store the data in the database
    if upload_id:
        await store_file_id(upload_id, organizer, location, max_tokens, event_name, artwork_attributes ,session=session)
        return {"message": f"File '{file_name}' uploaded successfully with ID: {upload_id}"}
    else:
        return {"message": "Upload failed", "error": "Could not process the file"}