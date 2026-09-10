import sqlite3
import os

class CriptoDB:
    def __init__(self, port: int):
        self.db_name = f"blockchain_node_{port}.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    block_index INTEGER PRIMARY KEY,
                    prev_hash TEXT,
                    merkle_root TEXT,
                    timestamp REAL,
                    nonce INTEGER,
                    block_hash TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    tx_id TEXT PRIMARY KEY,
                    sender TEXT,
                    receiver TEXT,
                    amount REAL,
                    timestamp REAL,
                    block_index INTEGER,
                    FOREIGN KEY(block_index) REFERENCES blocks(block_index)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rollup_batches (
                    batch_id TEXT PRIMARY KEY,
                    merkle_root TEXT,
                    bitcoin_txid TEXT,
                    tx_count INTEGER,
                    timestamp REAL
                )
            ''')
            conn.commit()

    def save_block(self, index: int, prev_hash: str, merkle_root: str, timestamp: float, nonce: int, block_hash: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO blocks VALUES (?, ?, ?, ?, ?, ?)", 
                           (index, prev_hash, merkle_root, timestamp, nonce, block_hash))
            conn.commit()

    def save_transaction(self, tx_id: str, sender: str, receiver: str, amount: float, timestamp: float, block_index: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO transactions VALUES (?, ?, ?, ?, ?, ?)", 
                           (tx_id, sender, receiver, amount, timestamp, block_index))
            conn.commit()

    def save_rollup_batch(self, batch_id: str, merkle_root: str, bitcoin_txid: str, tx_count: int, timestamp: float):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO rollup_batches VALUES (?, ?, ?, ?, ?)", 
                           (batch_id, merkle_root, bitcoin_txid, tx_count, timestamp))
            conn.commit()

    def get_all_balances(self) -> dict:
        balances = {}
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sender, receiver, amount FROM transactions")
            for sender, receiver, amount in cursor.fetchall():
                if sender != "GENESIS" and sender != "MINING_REWARD":
                    balances[sender] = balances.get(sender, 0.0) - amount
                balances[receiver] = balances.get(receiver, 0.0) + amount
        return balances

    def get_blockchain(self) -> list:
        blockchain = []
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blocks ORDER BY block_index ASC")
            blocks = cursor.fetchall()
            for b in blocks:
                cursor.execute("SELECT tx_id, sender, receiver, amount, timestamp FROM transactions WHERE block_index = ?", (b[0],))
                txs = cursor.fetchall()
                tx_list = [{"tx_id": t[0], "sender": t[1], "receiver": t[2], "amount": t[3], "timestamp": t[4]} for t in txs]
                blockchain.append({
                    "index": b[0], "prev_hash": b[1], "merkle_root": b[2],
                    "timestamp": b[3], "nonce": b[4], "hash": b[5], "transactions": tx_list
                })
        return blockchain

    def get_rollup_batches(self) -> list:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT batch_id, merkle_root, bitcoin_txid, tx_count, timestamp FROM rollup_batches ORDER BY timestamp DESC")
            return [{"batch_id": r[0], "merkle_root": r[1], "bitcoin_txid": r[2], "tx_count": r[3], "timestamp": r[4]} for r in cursor.fetchall()]
