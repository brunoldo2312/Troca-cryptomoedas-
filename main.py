import hashlib
import json
import time
import uuid
import sys
import requests

NODE_PORT = "6001"
NODE_URL = f"http://localhost:{NODE_PORT}"

class RollupEngine:
    @staticmethod
    def calculate_merkle_root(transactions: list) -> str:
        if not transactions:
            return ""
        hashes = [
            hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
            for tx in transactions
        ]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_level
        return hashes[0] if hashes else ""

def run_sequencer():
    print("==================================================")
    print("   BRN CORE ENGINE: SEQUENCIADOR DE ROLLUP L2    ")
    print("==================================================")
    try:
        res = requests.get(f"{NODE_URL}/get_mempool", timeout=3)
        if res.status_code != 200:
            print("[!] Erro ao obter dados do nó.")
            return
        txs = res.json().get("transactions", [])
        if not txs:
            print("[!] Mempool vazia. Injetando transações de teste...")
            requests.post(f"{NODE_URL}/send_transaction", json={"destino": "BRN_test", "valor": 10})
            requests.post(f"{NODE_URL}/send_transaction", json={"destino": "BRN_test2", "valor": 5})
            txs = requests.get(f"{NODE_URL}/get_mempool").json().get("transactions", [])
        print(f"[+] {len(txs)} transações carregadas.")
        merkle_root = RollupEngine.calculate_merkle_root(txs)
        print(f"[+] Merkle Root: {merkle_root}")
        payload = f"BRN:{merkle_root[:32]}"
        btc_txid = hashlib.sha256(f"{payload}{time.time()}".encode()).hexdigest()
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        receipt = {
            "batch_id": batch_id,
            "merkle_root": merkle_root,
            "bitcoin_txid": btc_txid,
            "tx_count": len(txs),
            "transactions": txs,
            "timestamp": time.time()
        }
        sync_res = requests.post(f"{NODE_URL}/add_rollup_batch", json=receipt)
        if sync_res.status_code == 200:
            print(f"[✓] Lote '{batch_id}' registrado com sucesso!")
        else:
            print("[!] Falha ao registrar lote.")
    except Exception as e:
        print(f"[!] Erro: {e}")

if __name__ == "__main__":
    run_sequencer()
