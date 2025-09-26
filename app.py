from flask import Flask, render_template
from dotenv import load_dotenv

# ルートのインポート
from routes.reservation_routes import reservation_bp

load_dotenv()
import models

app = Flask(__name__)

# Blueprintを登録
app.register_blueprint(reservation_bp)

user_name = "guest"

@app.route('/')
def index():
    """メインページ"""
    models.init_db()
    rooms = models.get_all_rooms()
    return render_template('index.html', rooms=rooms, user_name=user_name)


if __name__ == '__main__':
    app.run(debug=True)