from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings
from pydantic import EmailStr

# Para hashing de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Para JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_password_reset_token(email: EmailStr) -> str:
    
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {
        "exp": expire,
        "nbf": datetime.utcnow(),
        "sub": email,
        "scope": "password_reset"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt