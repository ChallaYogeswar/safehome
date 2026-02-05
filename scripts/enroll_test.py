import requests
from PIL import Image, ImageDraw
import os

BASE = 'http://127.0.0.1:5000'
TMPDIR = 'tests/tmp'
if not os.path.exists(TMPDIR):
    os.makedirs(TMPDIR)

# Create two simple images
for i in range(2):
    img = Image.new('RGB', (200,200), color=(73,109,137))
    d = ImageDraw.Draw(img)
    d.ellipse((60,50,140,130), fill=(255,224,189))
    d.ellipse((80,80,95,95), fill=(0,0,0))
    d.ellipse((105,80,120,95), fill=(0,0,0))
    d.arc((80,110,120,140), 0, 180, fill=(0,0,0), width=3)
    path = os.path.join(TMPDIR, f'image{i+1}.jpg')
    img.save(path)

session = requests.Session()

# Register (may redirect)
reg = session.post(BASE + '/auth/register', data={
    'username': 'testuser',
    'email': 'testuser@example.com',
    'password': 'Test@1234',
    'confirm_password': 'Test@1234'
})
print('register', reg.status_code)

# Login
login = session.post(BASE + '/auth/login', data={'email': 'testuser@example.com', 'password': 'Test@1234'})
print('login', login.status_code)

# Enroll person
files = [
    ('images', open(os.path.join(TMPDIR, 'image1.jpg'), 'rb')),
    ('images', open(os.path.join(TMPDIR, 'image2.jpg'), 'rb')),
]

enroll = session.post(BASE + '/face/enroll', data={'person_name': 'Test Person', 'relation': 'family', 'is_resident': 'true'}, files=files)
print('enroll status', enroll.status_code)
print(enroll.text)
