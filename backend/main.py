from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .database import Base, engine, get_db
from .models import User, Machine, Solve

Base.metadata.create_all(bind=engine)
app = FastAPI(title="RootBox")
pwd = CryptContext(schemes=["bcrypt"])

def get_rank(points: int):
    if points < 100:
        return "Noob"
    if points < 500:
        return "Script Kiddie"
    if points < 1500:
        return "Hacker"
    return "Pro Hacker"

@app.on_event("startup")
def seed():
    from .database import SessionLocal
    db = SessionLocal()
    if not db.query(Machine).first():
        db.add_all([
            Machine(name="Meow", difficulty="Easy", os="Linux", flag_user="FLAG{meow_user_pwned}", flag_root="FLAG{meow_root_pwned}"),
            Machine(name="Fawn", difficulty="Easy", os="Linux", flag_user="FLAG{fawn_user_pwned}", flag_root="FLAG{fawn_root_pwned}"),
            Machine(name="Dancing", difficulty="Medium", os="Windows", flag_user="FLAG{dancing_user_pwned}", flag_root="FLAG{dancing_root_pwned}"),
        ])
        db.commit()
    db.close()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <body style="background:#0a0a0a;color:#00ff41;font-family:monospace;padding:20px">
    <h1>ROOTBOX</h1>
    <p>Hack the box. Own the root.</p>
    <a href="/docs" style="color:#00ff41">-> Vai alle API /docs</a><br><br>
    <a href="/api/machines" style="color:#00ff41">-> Lista macchine</a><br>
    <a href="/api/leaderboard" style="color:#00ff41">-> Classifica</a>
    </body>
    """

@app.post("/api/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "Utente esiste già")
    u = User(username=username, password_hash=pwd.hash(password))
    db.add(u); db.commit()
    return {"ok": True, "user": username, "rank": "Noob"}

@app.post("/api/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == username).first()
    if not u or not pwd.verify(password, u.password_hash):
        raise HTTPException(401, "Login sbagliato")
    return {"ok": True, "username": u.username, "points": u.points, "rank": get_rank(u.points)}

@app.get("/api/machines")
def list_machines(db: Session = Depends(get_db)):
    ms = db.query(Machine).all()
    return [{"id": m.id, "name": m.name, "difficulty": m.difficulty, "os": m.os} for m in ms]

@app.post("/api/submit-flag")
def submit_flag(username: str, machine_name: str, flag: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == username).first()
    m = db.query(Machine).filter(Machine.name == machine_name).first()
    if not u or not m:
        raise HTTPException(404, "Utente o macchina non trovata")

    # Controlla se è user o root
    tipo = None
    punti = 0
    if flag == m.flag_user:
        tipo = "user"; punti = 10
    elif flag == m.flag_root:
        tipo = "root"; punti = 20
    else:
        return {"ok": False, "msg": "Flag sbagliata, riprova"}

    # Evita punti doppi
    gia = db.query(Solve).filter(Solve.user_id==u.id, Solve.machine_id==m.id, Solve.type==tipo).first()
    if gia:
        return {"ok": True, "msg": f"Già risolta! Non prendi altri punti", "points": u.points, "rank": get_rank(u.points)}

    u.points += punti
    db.add(Solve(user_id=u.id, machine_id=m.id, type=tipo))
    db.commit()
    return {"ok": True, "msg": f"BRAVO! +{punti} punti per {tipo} flag!", "points": u.points, "rank": get_rank(u.points)}

@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.points.desc()).limit(20).all()
    return [{"pos": i+1, "username": u.username, "points": u.points, "rank": get_rank(u.points)} for i, u in enumerate(users)]

@app.get("/api/profile/{username}")
def profile(username: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == username).first()
    if not u:
        raise HTTPException(404, "Utente non trovato")
    solves = db.query(Solve).filter(Solve.user_id==u.id).all()
    return {"username": u.username, "points": u.points, "rank": get_rank(u.points), "solves": len(solves)}
