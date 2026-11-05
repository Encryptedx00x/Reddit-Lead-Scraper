#!/usr/bin/env python3
"""
OpenClaw GEO-Reddit Wrapper
- Orquestra scripts Python via OpenClaw tools/exec
- Envia rascunhos para fila de aprovação
- Expõe endpoint HTTP para aprovação remota (opcional)
"""
import os, sys, json, subprocess, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

WORKSPACE = Path("/root/.openclaw/workspace/geo-reddit")
APPROVAL_QUEUE = WORKSPACE / "approval_queue.json"
APPROVED_QUEUE = WORKSPACE / "approved_posts.json"

def run_script(script_name, args=None):
    """Executa script Python e captura output"""
    cmd = ["python3", str(WORKSPACE / script_name)]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORKSPACE))
    if result.returncode != 0:
        return {"status": "error", "stderr": result.stderr}
    return {"status": "success", "stdout": result.stdout}

def queue_for_approval(lead, draft):
    """Adiciona rascunho à fila de aprovação"""
    queue = []
    if APPROVAL_QUEUE.exists():
        queue = json.loads(APPROVAL_QUEUE.read_text())
    queue.append({"lead": lead, "draft": draft, "status": "pending", "timestamp": time.time()})
    APPROVAL_QUEUE.write_text(json.dumps(queue, indent=2))
    return f"✅ Rascunho enfileirado para aprovação. Total na fila: {len(queue)}"

def approve_item(index):
    """Aprova item da fila e move para approved_posts.json"""
    if not APPROVAL_QUEUE.exists():
        return "❌ Fila vazia."
    queue = json.loads(APPROVAL_QUEUE.read_text())
    if index < 0 or index >= len(queue):
        return "❌ Índice inválido."
    item = queue.pop(index)
    item["status"] = "approved"
    APPROVAL_QUEUE.write_text(json.dumps(queue, indent=2))
    
    approved = []
    if APPROVED_QUEUE.exists():
        approved = json.loads(APPROVED_QUEUE.read_text())
    approved.append(item)
    APPROVED_QUEUE.write_text(json.dumps(approved, indent=2))
    return f"✅ Item {index} aprovado e movido para fila de envio."

def reject_item(index):
    """Rejeita item da fila"""
    if not APPROVAL_QUEUE.exists():
        return "❌ Fila vazia."
    queue = json.loads(APPROVAL_QUEUE.read_text())
    if index < 0 or index >= len(queue):
        return "❌ Índice inválido."
    queue.pop(index)
    APPROVAL_QUEUE.write_text(json.dumps(queue, indent=2))
    return f"❌ Item {index} rejeitado e removido."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 openclaw_wrapper.py <comando> [args]")
        print("Comandos: scrape, draft, approve <index>, reject <index>, status")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "scrape":
        print(run_script("reddit_lead_scraper.py"))
    elif cmd == "draft":
        print(run_script("outreach_engine.py"))
    elif cmd == "approve" and len(sys.argv) > 2:
        print(approve_item(int(sys.argv[2])))
    elif cmd == "reject" and len(sys.argv) > 2:
        print(reject_item(int(sys.argv[2])))
    elif cmd == "status":
        queue = json.loads(APPROVAL_QUEUE.read_text()) if APPROVAL_QUEUE.exists() else []
        print(f"📥 Fila de aprovação: {len(queue)} itens")
        for i, item in enumerate(queue):
            print(f"  [{i}] r/{item['lead']['subreddit']} | u/{item['lead']['author']} | {item['lead']['title'][:50]}...")
    else:
        print("❌ Comando inválido.")
