import sys
import time
import hashlib
import requests
import threading
from flask import Flask, jsonify, request, render_template_string
import webview
from cripto_db import CriptoDB
from cripto_wallet import CriptoWallet
from cripto_p2p_network import CriptoP2P

if len(sys.argv) < 2:
    print("Uso correto: python bruno_blockchain_real.py <PORTA>")
    sys.exit(1)

PORT = int(sys.argv[1])
db = CriptoDB(PORT)
mempool = []
network_nodes = set()

app = Flask(__name__)
RECOMPENSA_MINERACAO = 50.0

WALLET_FILE = f"wallet_{PORT}.json"
minha_carteira = CriptoWallet.load_wallet(WALLET_FILE)
if not minha_carteira:
    minha_carteira = CriptoWallet.generate_keypair(f"semente_secreta_segura_{PORT}")
    CriptoWallet.save_wallet(WALLET_FILE, minha_carteira)

if len(db.get_blockchain()) == 0:
    db.save_block(0, "0"*64, "0"*64, time.time(), 0, "0"*64)

TEMPLATE_DASHBOARD = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Moeda Bruno (BRN) - Painel de Controle</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #121214; color: #e1e1e6; margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #29292e; padding-bottom: 20px; margin-bottom: 20px; }
        h1 { color: #04d361; margin: 0; font-size: 24px; }
        .badge { background-color: #29292e; padding: 8px 15px; border-radius: 6px; font-size: 13px; border: 1px solid #41414c; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background-color: #202024; border: 1px solid #29292e; border-radius: 8px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { font-size: 18px; margin-top: 0; color: #a8a8b3; border-bottom: 1px solid #29292e; padding-bottom: 10px; }
        .balance-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #121214; }
        .btn { background-color: #04d361; color: #000; border: none; padding: 10px 20px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%; font-size: 14px; margin-top: 10px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-size: 12px; margin-bottom: 5px; color: #a8a8b3; }
        input { width: 100%; padding: 10px; background-color: #121214; border: 1px solid #29292e; border-radius: 4px; color: #fff; box-sizing: border-box; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { background: #121214; padding: 10px; border-radius: 4px; margin-bottom: 8px; border-left: 4px solid #04d361; font-size: 13px; word-break: break-all; }
        .wallet-info { background-color: #1a1a1e; border: 1px dashed #41414c; padding: 10px; font-family: monospace; font-size: 11px; margin-bottom: 15px; border-radius: 4px; color: #ff9000; }
        .rollup-li { border-left-color: #9871f5; }
    </style>
    <script>
        function atualizarDados() { window.location.reload(); }
        async function enviarTransacao(e) {
            e.preventDefault();
            const receiver = document.getElementById('receiver').value;
            const amount = document.getElementById('amount').value;
            const res = await fetch('/send_transaction_p2p', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({receiver, amount})
            });
            const data = await res.json();
            if(res.ok) { alert('Moedas transmitidas para a Mempool!'); atualizarDados(); }
            else { alert('Rejeitado pelo Consenso: ' + data.message); }
        }
        async function minerarMoedas() {
            const res = await fetch('/mine_empty');
            const data = await res.json();
            if(res.ok) { alert('Sucesso! Bloco minerado por PoW. Recompensa de +50 BRN recebida!'); atualizarDados(); }
        }
    </script>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🛡️ Moeda Bruno (BRN) - Painel do Nó</h1>
                <p style="margin: 5px 0 0 0; color: #8d8d99; font-size: 14px;">Emissão por Proof-of-Work | Sem Pré-mineração | Camada 2 Ativa</p>
            </div>
            <div class="badge">🌐 IP: <strong>{{ data.ip }}</strong> | Porta: <strong>{{ data.port }}</strong></div>
        </header>

        <div class="grid">
            <div>
                <div class="card" style="margin-bottom: 20px;">
                    <h2>🔑 Endereço da Sua Carteira</h2>
                    <div class="wallet-info"><strong>CHAVE PÚBLICA BRN:</strong><br>{{ data.minha_chave_publica }}</div>
                    <h2>💰 Livro de Saldos Gerais Minerados</h2>
                    <div style="max-height: 150px; overflow-y: auto;">
                        {% for user, bal in data.balances.items() %}
                        <div class="balance-item">
                            <span>👤 {{ user[:18] }}...</span>
                            <strong style="color: #04d361;">{{ bal }} BRN</strong>
                        </div>
                        {% else %}
                        <p style="color:#8d8d99; font-size:13px;">Nenhuma moeda em circulação na rede.</p>
                        {% endfor %}
                    </div>
                </div>

                <div class="card">
                    <h2>💸 Transferir Moedas Mineradas</h2>
                    <form onsubmit="enviarTransacao(event)">
                        <div class="form-group">
                            <label>Endereço de Destino (Chave Pública BRN)</label>
                            <input type="text" id="receiver" required placeholder="Ex: BRN_f34a...">
                        </div>
                        <div class="form-group">
                            <label>Quantidade a Transferir</label>
                            <input type="number" id="amount" step="0.01" required placeholder="0.00">
                        </div>
                        <button type="submit" class="btn">Assinar & Transmitir</button>
                    </form>
                </div>
            </div>

            <div>
                <div class="card" style="margin-bottom: 20px;">
                    <h2>⛏️ Painel do Minerador (Proof-of-Work)</h2>
                    <button class="btn" onclick="minerarMoedas()" style="background-color: #ff9000; color: #000;">⛏️ Resolver Desafio e Minerar Novas Moedas (+50 BRN)</button>
                    <h2 style="margin-top: 20px;">⏳ Mempool Ativa</h2>
                    <ul style="max-height: 120px; overflow-y: auto;">
                        {% for tx in data.mempool %}
                        <li><strong>De:</strong> {{ tx.sender[:12] }}... ➔ <strong>Para:</strong> {{ tx.receiver[:12] }}... | <strong>Valor:</strong> {{ tx.amount }} BRN</li>
                        {% else %}
                        <p style="color:#8d8d99; font-size:13px;">Aguardando transações na rede...</p>
                        {% endfor %}
                    </ul>
                </div>

                <div class="card">
                    <h2>⛓️ Lotes Rollup Ancorados no Bitcoin (L1)</h2>
                    <ul style="max-height: 120px; overflow-y: auto;">
                        {% for batch in data.rollup_batches %}
                        <li class="rollup-li">
                            <strong>Lote ID:</strong> {{ batch.batch_id }} ({{ batch.tx_count }} txs)<br>
                            <strong>Bitcoin TXID:</strong> <span style="font-size:11px; color:#04d361;">{{ batch.bitcoin_txid[:30] }}...</span>
                        </li>
                        {% else %}
                        <p style="color:#8d8d99; font-size:13px;">Nenhum lote Rollup processado pela Camada 2 ainda.</p>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    ctx_data = {
        "ip": CriptoP2P.get_local_ip(),
        "port": PORT,
        "minha_chave_publica": minha_carteira["public_key"],
        "balances": db.get_all_balances(),
        "mempool": mempool,
        "rollup_batches": db.get_rollup_batches()
    }
    return render_template_string(TEMPLATE_DASHBOARD, data=ctx_data)

@app.route('/send_transaction_p2p', methods=['POST'])
def send_transaction_p2p():
    data = request.get_json()
    sender = minha_carteira["public_key"]
    receiver = data.get("receiver")
    amount = float(data.get("amount"))
    
    saldos = db.get_all_balances()
    saldo_remetente = saldos.get(sender, 0.0)
    saldo_retido_mempool = sum(t["amount"] for t in mempool if t["sender"] == sender)
    saldo_disponivel = saldo_remetente - saldo_retido_mempool
    
    if saldo_disponivel < amount:
        return jsonify({"status": "error", "message": f"Saldo de mineração insuficiente! Livre: {saldo_disponivel} BRN."}), 400

    signature = CriptoWallet.sign_transaction(minha_carteira["private_key"], sender, receiver, amount)
    
    tx = {
        "tx_id": f"tx_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}",
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "signature": signature,
        "timestamp": time.time()
    }
    
    mempool.append(tx)
    return jsonify({"status": "success", "transaction": tx}), 200

@app.route('/mine_empty', methods=['GET'])
def mine_empty():
    blockchain = db.get_blockchain()
    last_block = blockchain[-1] if blockchain else {"index": -1, "hash": "0"*64}
    new_index = last_block["index"] + 1
    prev_hash = last_block["hash"]
    
    reward_tx_id = f"tx_reward_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
    merkle_root = hashlib.sha256(reward_tx_id.encode()).hexdigest()
