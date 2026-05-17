from passlib.context import CryptContext;
pwx=CryptContext(schemes=["bcrypt"], deprecated="auto");
def encryptPassword(password:str)->str:
    return pwx.hash(password);
def checkPassword(password:str,hashedPassword:str)->bool:
    return pwx.verify(password,hashedPassword);
