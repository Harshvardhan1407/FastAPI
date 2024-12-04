from fastapi import FastAPI, HTTPException, Depends, APIRouter,Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import uvicorn
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Annotated
import os
from dotenv import load_dotenv
load_dotenv()
sql_username = os.getenv("sql_username")
sql_password = os.getenv("sql_password")
api_host = os.getenv("api_host")
api_port = int(os.getenv("api_port"))
# print(api_host,type(api_host))
# print(api_port,type(api_port))
app = FastAPI()

# Database setup
DATABASE_URL = f"mysql+mysqlconnector://{sql_username}:{sql_password}@localhost/users"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create a router
router = APIRouter(prefix="/api/v1")
# Add the router to the FastAPI app
app.include_router(router)

@app.post("/")
def read_root():
    return {"message": "Hi Harsh!!! API working fine.....!"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Module and FastAPI instance
        host=api_host,  # Host configuration
        port=api_port,       # Port configuration
        reload=True      # Auto-reload during development
    )


# Secret key for signing JWTs
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# Database model
class User(Base):
    __tablename__ = "users_login"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    login_count = Column(Integer, default=0)

# Create tables
Base.metadata.create_all(bind=engine)


# Dependency: Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# # In-memory user storage for simplicity (use a database in production)
# fake_users_db = {
#     "harsh": {
#         "username": "harsh_id",
#         "hashed_password": "$2b$12$5Nk9yqjzvfp0R.2O.uVbWumAA/m5pSKV2ShnZ4s.jBxtg7g120lgK",
#     }
# }

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Helper: Hash password
def get_password_hash(password):
    return pwd_context.hash(password)


# Helper: Verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Helper: Authenticate user
def authenticate_user(db,username: str, password: str):
    # user = fake_users_db.get(username)
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


# Helper: Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Token endpoint
@app.post("/login_token")
# def login(form_data: OAuth2PasswordRequestForm = Depends()):
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):

    # user = authenticate_user(form_data.username, form_data.password)
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# # Protected route
# @app.post("/user_login")
# def read_users_me(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
# # def read_users_me(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication token")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid authentication token")
    
#     return {"username": username}


@app.post("/user_login")
def read_users_me(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return {"username": user.username, "login_count": user.login_count}


@app.post("/create_user")
def create_user(username: str, password: str, db=Depends(get_db)):
    hashed_password = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully", "username": user.username}


@app.put("/update_password")
def update_password(username: str, new_password: str, db=Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@app.delete("/delete_user")
def delete_user(username: str, db=Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@app.post("/weather_data")
# def weather_ingestion_api(project:str,from_date:datetime,to_date: datetime):
    # return {f"weather_api{project},{from_date},{to_date}"}
def weather_ingestion_api():
    return {"weather_api"}
# def weather_ingestion_api(
    # project: Annotated[str, Query(..., description="Project name for the weather data")],
    # from_date: Annotated[datetime, Query(..., description="Start date in YYYY-MM-DD format")],
    # to_date: Annotated[datetime, Query(..., description="End date in YYYY-MM-DD format")],
# ):
    # Add your logic here
    # return {
    #     "message": f"Weather data for project: {project}"
    #     #, from {from_date}, to {to_date}"
    # }