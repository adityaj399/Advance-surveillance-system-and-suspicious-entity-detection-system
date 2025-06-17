from firebase import firebase
import time

def readFirebase():
    firebase1 = firebase.FirebaseApplication('https://augmentedreality-af310-default-rtdb.firebaseio.com/', None)
    level = firebase1.get('/250/level', None)
    return level


def writeFirebase(alert):

    firebase1 = firebase.FirebaseApplication('https://augmentedreality-af310-default-rtdb.firebaseio.com/', None)
    result = firebase1.put('AE250/','alert',alert)

    print(result)

