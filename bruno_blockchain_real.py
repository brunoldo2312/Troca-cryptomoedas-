import sys
import time
import hashlib
import requests
from flask import Flask, jsonify, request, render_template_string
import webview
from cripto_db import CriptoDB
from cripto_wallet import CriptoWallet
from cripto_p2p_network import CriptoP2P

if len(sys.argv) < 2:
    print("Uso correto: python bruno_blockchain_real.py <PORTA>")
    sys.exit(1)

# CORREÇÃO CRÍTICA AQUI: capturando a posição correta do argumento da lista
PORT = int(sys.argv[1])
db = CriptoDB(PORT)
mempool = []
network_nodes = set()

app = Flask(__name__)

WALLET_FILE = f"wallet_{PORT}.json"
minha_carteira = CriptoWallet.load_wallet(WALLET_FILE)
if not minha_carteira:
    minha_carteira = CriptoWallet.generate_keypair(f"senha_secreta_do_no_{PORT}")
    CriptoWallet.save_wallet(WALLET_FILE, minha_carteira)

if len(db.get_blockchain()) == 0:
    db.save_block(0, "0"*64, "0"*64, time.time(), 0, "0"*64)
    db.save_transaction("tx_genesis", "GENESIS", minha_carteira["public_key"], 1000000.0, time.time(), 0)

TEMPLATE_DASHBOARD = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Moeda Bruno (BRN) - Rede P2P</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121214; color: #e1e1e6; margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #29292e; padding-bottom: 20px; margin-bottom: 20px; }
        h1 { color: #04d361; margin: 0; font-size: 24px; }
        .badge { background-color: #29292e; padding: 8px 15px; border-radius: 6px; font-size: 13px; border: 1px solid #41414c; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background-color: #202024; border: 1px solid #29292e; border-radius: 8px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { font-size: 18px; margin-top: 0; color: #a8a8b3; border-bottom: 1px solid #29292e; padding-bottom: 10px; }
        .balance-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #121214; }
        .btn { background-color: #04d361; color: #000; border: none; padding: 10px 20px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%; font-size: 14px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-size: 12px; margin-bottom: 5px; color: #a8a8b3; }
        input { width: 100%; padding: 10px; background-color: #121214; border: 1px solid #29292e; border-radius: 4px; color: #fff; box-sizing: border-box; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { background: #121214; padding: 10px; border-radius: 4px; margin-bottom: 8px; border-left: 4px solid #04d361; font-size: 13px; word-break: break-all; }
        .wallet-info { background-color: #1a1a1e; border: 1px dashed #41414c; padding: 10px; font-family: monospace; font-size: 11px; margin-bottom: 15px; border-radius: 4px; color: #ff9000; }
    </style>
    <script>
        function atualizarDados() { window.location.reload(); }
        async function enviarTransacaoP2P(e) {
            e.preventDefault();
            const receiver = document.getElementById('receiver').value;
            const amount = document.getElementById('amount').value;
            
            const res = await fetch('/send_transaction_p2p', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({receiver, amount})
            });
            if(res.ok) { alert('Moedas enviadas e propagadas na rede BRN!'); atualizarDados(); }
        }
        async function conectarNo(e) {
            e.preventDefault();
            const target_port = document.getElementById('target_port').value;
            const res = await fetch('/connect_node', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({port: target_port})
            });
            if(res.ok) { alert('Conectado à rede do nó ' + target_port); atualizarDados(); }
        }
    </script>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>💼 Moeda Bruno (BRN) - Rede P2P</h1>
                <p style="margin: 5px 0 0 0; color: #8d8d99; font-size: 14px;">Envio Assinado entre Carteiras e Sincronização de Nós</p>
            </div>
            <div class="badge">🌐 IP: <strong>{{ data.ip }}</strong> | Porta Ativa: <strong>{{ data.port }}</strong></div>
        </header>

        <div class="grid">
            <div>
                <div class="card" style="margin-bottom: 20px;">
                    <h2>🔑 Sua Carteira Digital (Salva Automaticamente)</h2>
                    <div class="wallet-info">
                        <strong>SUA CHAVE PÚBLICA (Endereço BRN):</strong><br>
                        {{ data.minha_chave_publica }}
                    </div>
                    <h2>💰 Livro de Saldos Gerais</h2>
                    <div style="max-height: 120px; overflow-y: auto;">
                        {% for user, bal in data.balances.items() %}
                        <div class="balance-item">
                            <span>👤 {{ user[:15] }}...</span>
                            <strong style="color: #04d361;">{{ bal }} BRN</strong>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card">
                    <h2>💸 Transferir Moedas para a Rede BRN</h2>
                    <form onsubmit="enviarTransacaoP2P(event)">
                        <div class="form-group">
                            <label>Endereço de Destino (Chave Pública BRN)</label>
                            <input type="text" id="receiver" required placeholder="Ex: BRN_f34a...">
                        </div>
                        <div class="form-group">
                            <label>Quantidade de Moedas (BRN)</label>
                            <input type="number" id="amount" step="0.01" required placeholder="0.00">
                        </div>
                        <button type="submit" class="btn">Assinar & Enviar via P2P</button>
                    </form>
                </div>
            </div>

            <div>
                <div class="card" style="margin-bottom: 20px;">
                    <h2>🕸️ Conectar a outro Nó na Rede BRN</h2>
                    <form onsubmit="conectarNo(event)" style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <input type="number" id="target_port" required placeholder="Ex da Porta: 6002" style="flex: 2;">
                        <button type="submit" class="btn" style="flex: 1; background-color: #9871f5; color: #fff;">Conectar</button>
                    </form>
                    <strong>Nós Conectados na sua Rede:</strong>
                    <ul style="margin-top: 10px;">
                        {% for node in data.nodes %}
                        <li style="border-left-color: #9871f5; background:#121214;">🔗 {{ node }}</li>
                        {% else %}
                        <p style="color:#8d8d99; font-size:12px; margin:0;">Nenhum outro nó conectado.</p>
                        {% endfor %}
                    </ul>
                </div>

                <div class="card">
                    <h2>⏳ Mempool Global Sincronizada</h2>
                    <ul style="max-height: 180px; overflow-y: auto;">
                        {% for tx in data.mempool %}
                        <li>
                            <strong>De (Sender):</strong> {{ tx.sender[:20] }}...<br>
                            <strong>Para (Receiver):</strong> {{ tx.receiver[:20] }}...<br>
                            <strong>Quantidade:</strong> {{ tx.amount }} BRN
                        </li>
                        {% else %}
                        <p style="color:#8d8d99; font-size:13px;">Aguardando transações da rede...</p>
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
        "nodes": list(network_nodes)
    }
    return render_template_string(TEMPLATE_DASHBOARD, data=ctx_data)

@app.route('/connect_node', methods=['POST'])
def connect_node():
    data = request.get_json()
    target_node = f"http://localhost:{data.get('port')}"
    network_nodes.add(target_node)
    return jsonify({"status": "connected"}), 200

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    tx = request.get_json()
    if tx["tx_id"] not in [t["tx_id"] for t in mempool]:
        if CriptoWallet.verify_signature(tx["sender"], tx["sender"], tx["receiver"], tx["amount"], tx["signature"]):
            mempool.append(tx)
            for node in network_nodes:
                try: requests.post(f"{node}/receive_transaction", json=tx, timeout=1)
                except Exception: pass
            return jsonify({"status": "accepted"}), 200
    return jsonify({"status": "ignored"}), 400

@app.route('/send_transaction_p2p', methods=['POST'])
def send_transaction_p2p():
    data = request.get_json()
    sender = minha_carteira["public_key"]
    receiver = data.get("receiver")
    amount = float(data.get("amount"))
    
    signature = CriptoWallet.sign_transaction(minha_carteira["private_key"], sender, receiver, amount)
    
    tx = {
        "tx_id": f"tx_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}",
        "sender": sender,
