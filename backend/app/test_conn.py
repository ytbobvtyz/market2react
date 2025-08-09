from sqlalchemy import create_engine
engine = create_engine("postgresql+psycopg2://market_user:ваш_пароль@localhost/market2react")
conn = engine.connect()
print(conn.scalar("SELECT 1"))  # Должно вернуть 1
conn.close()