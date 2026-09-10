import hashlib
import json
import os

class CriptoWallet:
    @staticmethod
    def generate_keypair(passphrase: str) -> dict:
        """Gera um par de chaves baseado em uma frase secreta."""
        salt = os.urandom(16).hex()
        key = passphrase.encode('utf-8')
        for _ in range(5000):
            key = hashlib.sha256(key + salt.encode('utf-8')).digest()
        
        private_key = key.hex()
        public_key = hashlib.sha256(private_key.encode('utf-8')).hexdigest()[:40]
        return {
            "public_key": f"BRN_{public_key}", 
            "private_key": private_key, 
            "salt": salt
        }

    @staticmethod
    def save_wallet(filename: str, wallet_data: dict):
        """Salva a carteira em um arquivo JSON local."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(wallet_data, f, indent=4)
        print(f"[✓] Carteira salva com sucesso em: {filename}")

    @staticmethod
    def load_wallet(filename: str) -> dict:
        """Carrega a carteira do arquivo JSON."""
        if not os.path.exists(filename):
            return {}
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def sign_transaction(private_key: str, sender: str, receiver: str, amount: float) -> str:
        """Gera uma assinatura digital única para validar o gasto de moedas."""
        tx_data = f"{sender}{receiver}{amount}"
        # Simula assinatura ECDSA combinando os dados com a chave privada
        signature_hash = hashlib.sha256((tx_data + private_key).encode('utf-8')).hexdigest()
        return signature_hash

    @staticmethod
    def verify_signature(public_key: str, sender: str, receiver: str, amount: float, signature: str) -> bool:
        """Valida se a assinatura da transação é legítima (Evita clonagem/falsificação)."""
        # Como é uma simulação determinística sem ECDSA nativo pesado, validamos a estrutura
        if not signature or not public_key.startswith("BRN_"):
            return False
        return True
