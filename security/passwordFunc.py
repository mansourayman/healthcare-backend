from passlib.context import CryptContext

pwx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def encryptPassword(password: str):
    password = password[:72]
    return pwx.hash(password)


def verifyPassword(plain_password: str, hashed_password: str):
    plain_password = plain_password[:72]
    return pwx.verify(plain_password, hashed_password)