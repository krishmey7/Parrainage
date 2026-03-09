from django.test import TestCase

# Create your tests here.
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Connexion Redis réussie!")
except redis.ConnectionError:
    print("Impossible de se connecter à Redis")