import json
import pymongo
from bson.objectid import ObjectId
import os
import random
import string
import sys
import numpy as np
from util import base64_to_pil
from flask import Flask, redirect, url_for, request, render_template, Response, jsonify, session
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.utils import get_file


app = Flask(__name__)

app.secret_key = 'MySecret'

# ========== SETUP MONGODB ==========
try:
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=1000
    )
    db = mongo.Fruit
    mongo.server_info()
except:
    print("ERROR Connect To Database")

# ===================================


# ========== PREDICT ==========
model = load_model('models/model_buah.h5')


def model_predict(img, model):
    img = img.resize((224, 224))
    x = image.img_to_array(img)
    x = x.reshape(-1, 224, 224, 3)
    x = x.astype('float32')
    x = x / 255.0
    preds = model.predict(x)
    return preds


@app.route('/predict/API/v1', methods=['POST'])
def predict():
    try:
        # Request gambar
        img = base64_to_pil(request.json)
        # Simpan Gambar
        img.save("uploads/fruits.png")
        # Membuat Prediksi
        preds = model_predict(img, model)

        target_names = [
            'Apel', 'Belimbing', 'Buah_Naga', 'Jambu', 'Jeruk', 'Kiwi', 'Mangga', 'Pir', 'Pisang', 'Tomat'
        ]

        hasil_label = target_names[np.argmax(preds)]
        data = list(db.fruits.find())

        for i, plant in enumerate(target_names):
            if hasil_label == plant:
                jenis_tanaman = data[i]["jenis"]
                deskripsi_tanaman = data[i]["deskripsi"]
                nutrisi_tanaman = data[i]["nutrisi"]
                manfaat_tanaman = data[i]["manfaat"]

        hasil_prob = "{:.2f}".format(100 * np.max(preds))

        return jsonify(
            result=hasil_label,
            probability=hasil_prob + str('%'),
            jenis=jenis_tanaman,
            deskripsi=deskripsi_tanaman,
            nutrisi=nutrisi_tanaman,
            manfaat=manfaat_tanaman
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Predict!"}),
            status=500,
            mimetype="application/json"
        )
# =======================================


# ========== CREATE USER ==========
@app.route("/users/create/", methods=["POST"])
def create_user():
    try:
        user = {
            "username": request.json["username"],
            "password": request.json["password"],
            "token": request.json["token"]
        }
        dbResponse = db.users.insert_one(user)
        session['username'] = request.json["username"]
        return Response(
            response=json.dumps({
                "message": "User Created",
                "id": f"{dbResponse.inserted_id}"
            }),
            status=200,
            mimetype="application/json"
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Create User!"}),
            status=500,
            mimetype="application/json"
        )

# ==================================


# ========== LOGIN USER ==========
@app.route("/users/login", methods=["POST"])
def login_user():
    try:
        login_user = db.users.find_one({'username': request.form["username"]})
        if login_user:
            if request.form["password"] == login_user["password"]:
                db.users.update_one(
                    {"_id": login_user["_id"]},
                    {"$set": {
                        "token": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    }}
                )
                session["username"] = login_user["username"]
                return Response(
                    response=json.dumps({
                        "message": "Login berhasil!"
                    }),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({"message": "Password Salah!"}),
                    status=500,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({"message": "Username Salah!"}),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Login Gagal!"}),
            status=500,
            mimetype="application/json"
        )

# ======================================


# ========== CREATE FRUIT ==========
@app.route("/fruits/create", methods=["POST"])
def create_plant():
    try:
        if not session.get("username"):
            
            return redirect("/login")
        
        plant = {
            "nama": request.form["nama"],
            "jenis": request.form["jenis"],
            "deskripsi": request.form["deskripsi"],
            "nutrisi": request.form["nutrisi"],
            "manfaat": request.form["manfaat"]
        }
        dbResponse = db.fruits.insert_one(plant)
        return Response(
            response=json.dumps({
                "message": "Fruit Created",
                "id": f"{dbResponse.inserted_id}"
            }),
            status=200,
            mimetype="application/json"
        )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
        except Exception as ex:
            print(ex)
            return Response(
                response=json.dumps({"message": "Cannot Create Fruit!"}),
                status=500,
                mimetype="application/json"
            )

# =======================================


# ========== READ ==========
@app.route("/fruits", methods=["GET"])
def get_fruits():
    try:
        if not session.get("username"):
            # if not there in the session then redirect to the login page
            return redirect("/login")
        # token = db.users.find_one({"token": request.json["token"]})
        # if token:
        data = list(db.fruits.find())
        # Convert to string
        for plant in data:
            plant["_id"] = str(plant["_id"])
        return Response(
            response=json.dumps(data),
            status=200,
            mimetype="application/json"
        )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
        except Exception as ex:
            print(ex)
            return Response(
                response=json.dumps({
                    "message": "Cannot Get fruits!"
                }),
                status=500,
                mimetype="application/json"
            )

# ============================================


# ========== UPDATE ==========
@ app.route("/fruits/update/<id>", methods=["PUT"])
def update_plant(id):
    try:
        token = db.users.find_one({"token": request.json["token"]})
        if token:
            dbResponse = db.fruits.update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "nama": request.json["nama"],
                    "jenis": request.json["jenis"],
                    "deskripsi": request.json["deskripsi"],
                    "nutrisi": request.json["nutrisi"],
                    "manfaat": request.json["manfaat"]
                }}
            )
            if dbResponse.modified_count == 1:
                return Response(
                    response=json.dumps({"message": "Fruit Updated"}),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({"message": "Nothing To Update"}),
                    status=200,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Update!"}),
            status=500,
            mimetype="application/json"
        )

# ====================================================


# ========== DELETE ==========
@ app.route("/fruits/delete/<id>", methods=["DELETE"])
def delete_plant(id):
    try:
        token = db.users.find_one({"token": request.json["token"]})
        if token:
            dbResponse = db.fruits.delete_one({"_id": ObjectId(id)})
            if dbResponse.deleted_count == 1:
                return Response(
                    response=json.dumps({
                        "message": "Plant Deleted",
                        "id": f"{id}"
                    }),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({
                        "message": "Plant Not Found",
                        "id": f"{id}"
                    }),
                    status=200,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Sorry Cannot Delete!"}),
            status=500,
            mimetype="application/json"
        )

# ===============================================


if __name__ == "__main__":
    app.run(port=5000, debug=True)
