import json
import hashlib
from typing import Dict, Any

def generate_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Gera um hash SHA-256 estável para um dicionário (payload da API).
    """
    payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    hash_object = hashlib.sha256(payload_str.encode('utf-8'))
    return hash_object.hexdigest()