import hashlib
import hmac
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from config.settings import Settings


class PasswordSecurity:
    """
    Servicio criptográfico de contraseñas basado en Argon2id (Type.ID)
    combinado con pre-hashing HMAC-SHA256 usando un PEPPER_SECRET del entorno.
    """

    def __init__(self):
        self._ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,  # 64 MB
            parallelism=4,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    @staticmethod
    def _apply_pepper(plain_password: str) -> str:
        pepper_bytes = Settings.get_pepper_bytes()
        password_bytes = plain_password.encode("utf-8")
        return hmac.new(pepper_bytes, password_bytes, hashlib.sha256).hexdigest()

    def hash_password(self, plain_password: str) -> str:
        if not plain_password or len(plain_password.strip()) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        peppered = self._apply_pepper(plain_password)
        return self._ph.hash(peppered)

    def verify_password(self, stored_hash: str, plain_password: str) -> bool:
        if not stored_hash or not plain_password:
            return False
        peppered = self._apply_pepper(plain_password)
        try:
            return self._ph.verify(stored_hash, peppered)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, stored_hash: str) -> bool:
        try:
            return self._ph.check_needs_rehash(stored_hash)
        except Exception:
            return False
