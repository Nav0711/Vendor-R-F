import json
import os
import threading

TOKEN_FILE = "token_state.json"
INITIAL_TOKENS = 50000

class TokenManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._load_state()
        
    def _load_state(self):
        if not os.path.exists(TOKEN_FILE):
            self.available_tokens = INITIAL_TOKENS
            self._save_state()
        else:
            try:
                with open(TOKEN_FILE, "r") as f:
                    data = json.load(f)
                    self.available_tokens = data.get("available_tokens", INITIAL_TOKENS)
            except Exception:
                self.available_tokens = INITIAL_TOKENS
                self._save_state()
                
    def _save_state(self):
        with open(TOKEN_FILE, "w") as f:
            json.dump({"available_tokens": self.available_tokens}, f)
            
    def get_balance(self) -> int:
        with self._lock:
            return self.available_tokens
            
    def deduct(self, amount: int) -> bool:
        """Deducts tokens if sufficient balance exists. Returns True if successful."""
        with self._lock:
            if self.available_tokens >= amount:
                self.available_tokens -= amount
                self._save_state()
                return True
            return False

# Global instance
token_manager = TokenManager()
