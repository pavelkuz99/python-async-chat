from passlib.context import CryptContext


class Encryption(CryptContext):
    def __init__(self):
        super().__init__(schemes=["pbkdf2_sha256"],
                         default="pbkdf2_sha256",
                         bkdf2_sha256__default_rounds=30000)

    def encrypt_password(self, password):
        return self.encrypt(password)

    def check_encrypt_password(self, password, hashed):
        return self.verify(password, hashed)