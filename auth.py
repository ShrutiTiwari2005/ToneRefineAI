import hashlib, json, os

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "users.json")

def _load():
    if not os.path.exists(DB): return {}
    try:
        with open(DB, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def _save(obj):
    with open(DB, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2)

def _safe(u: str) -> str:
    return "".join(c for c in (u or "") if c.isalnum())

def _hash(pw: str, salt: str) -> str:
    return hashlib.sha256((salt + pw).encode("utf-8")).hexdigest()

def user_exists(username: str) -> bool:
    return _safe(username) in _load()

def create_user(username: str, password: str) -> bool:
    u = _safe(username)
    if not u or user_exists(u): return False
    salt = hashlib.sha256(u.encode()).hexdigest()[:16]
    db = _load()
    db[u] = {"salt": salt, "hash": _hash(password, salt)}
    _save(db); return True

def authenticate(username: str, password: str) -> bool:
    u = _safe(username); db = _load()
    if u not in db: return False
    return db[u]["hash"] == _hash(password, db[u]["salt"])
