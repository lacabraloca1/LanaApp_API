from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    nombre: str
    correo: EmailStr
    telefono: str
    contraseña: str
    
class UserLogin(BaseModel):
    correo: EmailStr
    contraseña: str