import sqlite3, psycopg2, os

# DB = os.environ['DB']
# DB_NAME = os.environ['DB_NAME']
# DB_USER = os.environ['DB_USER']
# DB_PASS = os.environ['DB_PASS']
# DB_DOMAIN = os.environ['DB_DOMAIN']
# DB_PORT = os.environ['DB_PORT']


DB = '/Project/video_counts/stills_counts.db'
DB_NAME = 'uo-vision-1'
DB_USER = 'uo'
DB_PASS = 'vision'
DB_DOMAIN = 'database.urbanobservatory.ac.uk'
DB_PORT = 5234

conn_lite = sqlite3.connect(DB)
conn_post = psycopg2.connect(host=DB_DOMAIN, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
cursor_lite = conn_lite.cursor()
cursor_post = conn_post.cursor()

cursor_lite.execute("SELECT location, url, datetime, counts FROM stills_counts")
data = cursor_lite.fetchall()

cursor_post.executemany("INSERT INTO stills_counts VALUES(%s, %s, %s, %s)", data)
conn_post.commit()

cursor_lite.close()
cursor_post.close()

conn_lite.close()
conn_post.close()
