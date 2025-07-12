from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import pymongo
import os
from typing import Optional, List
import uuid
from bson import ObjectId
import shutil
import mimetypes

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'vb_solucoes')
SECRET_KEY = "vb_solucoes_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app
app = FastAPI(title="VB Soluções - Livro de Ocorrência Online")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]
users_collection = db.users
incidents_collection = db.incidents

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class IncidentCreate(BaseModel):
    title: str
    description: str
    type: str
    location: str  # apartamento
    people_involved: str  # bloco
    severity: str  # baixa, media, alta

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    people_involved: Optional[str] = None
    severity: Optional[str] = None

class IncidentStatusUpdate(BaseModel):
    status: str  # nova, em_andamento, resolvida, cancelada

class Incident(BaseModel):
    id: str
    title: str
    description: str
    type: str
    location: str  # apartamento
    people_involved: str  # bloco
    severity: str
    status: str
    created_by: str
    created_by_username: str
    created_at: datetime
    updated_at: datetime

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    return User(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"]
    )

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def init_admin_user():
    """Initialize default admin user"""
    existing_admin = users_collection.find_one({"username": "admin"})
    if not existing_admin:
        admin_id = str(uuid.uuid4())
        users_collection.insert_one({
            "id": admin_id,
            "username": "admin",
            "email": "admin@vbsolucoes.com",
            "password": get_password_hash("admin123"),
            "role": "admin",
            "created_at": datetime.utcnow()
        })
        print("Default admin user created: admin/admin123")

# API Routes
@app.on_event("startup")
async def startup_event():
    init_admin_user()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "VB Soluções API"}

@app.post("/api/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = users_collection.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": "user",  # Default role
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    user_response = User(
        id=user_id,
        username=user.username,
        email=user.email,
        role="user"
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@app.post("/api/login", response_model=Token)
async def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    user_response = User(
        id=db_user["id"],
        username=db_user["username"],
        email=db_user["email"],
        role=db_user["role"]
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@app.get("/api/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/incidents", response_model=Incident)
async def create_incident(incident: IncidentCreate, current_user: User = Depends(get_current_user)):
    incident_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_incident = {
        "id": incident_id,
        "title": incident.title,
        "description": incident.description,
        "type": incident.type,
        "location": incident.location,
        "people_involved": incident.people_involved,
        "severity": incident.severity,
        "status": "nova",  # Default status
        "created_by": current_user.id,
        "created_by_username": current_user.username,
        "created_at": now,
        "updated_at": now
    }
    
    incidents_collection.insert_one(new_incident)
    
    return Incident(**new_incident)

@app.get("/api/incidents", response_model=List[Incident])
async def get_incidents(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role != "admin":
        # Regular users can only see their own incidents
        query["created_by"] = current_user.id
    
    incidents = list(incidents_collection.find(query).sort("created_at", -1))
    
    return [Incident(**incident) for incident in incidents]

@app.get("/api/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str, current_user: User = Depends(get_current_user)):
    incident = incidents_collection.find_one({"id": incident_id})
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and incident["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return Incident(**incident)

@app.put("/api/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str, 
    status_update: IncidentStatusUpdate, 
    current_user: User = Depends(get_admin_user)
):
    """Only admins can update incident status"""
    result = incidents_collection.update_one(
        {"id": incident_id},
        {
            "$set": {
                "status": status_update.status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    return {"message": "Status updated successfully"}

@app.put("/api/incidents/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: str, 
    incident_update: IncidentUpdate, 
    current_user: User = Depends(get_current_user)
):
    incident = incidents_collection.find_one({"id": incident_id})
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Check permissions (only creator or admin can update)
    if current_user.role != "admin" and incident["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    for field, value in incident_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    incidents_collection.update_one(
        {"id": incident_id},
        {"$set": update_data}
    )
    
    updated_incident = incidents_collection.find_one({"id": incident_id})
    return Incident(**updated_incident)

@app.delete("/api/incidents/{incident_id}")
async def delete_incident(incident_id: str, current_user: User = Depends(get_admin_user)):
    """Only admins can delete incidents"""
    result = incidents_collection.delete_one({"id": incident_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    return {"message": "Incident deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)