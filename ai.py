# ================================
# 2. RECOMMENDER ALGORITHM (AI MATCH)
# ================================
import random
@app.route("/matchme")
def matchme():
    if session.get('role') != 'guy':
        return "Guys only!"
    with get_db() as db:
        girls = db.execute("SELECT * FROM users WHERE role='girl'").fetchall()
        # AI = distance + rating + new photos
        scored = []
        for g in girls:
            photos = db.execute("SELECT COUNT(*) FROM photos WHERE user_id=? AND approved=1", (g['id'],)).fetchone()[0]
            score = photos * 10 + random.randint(1,20)
            scored.append((score, g))
        scored.sort(reverse=True)
        top3 = scored[:3]
        return render_template("matchme.html", matches=top3)
