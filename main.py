from markdown2html import markdown2html
from cohere.classify import Example
from cors import crossdomain
from replit import db
from flask import *
import requests
import cohere
import json
import uuid
import copy
import os

app = Flask(__name__, template_folder="", static_folder="")
co = cohere.Client("2H7QHvLLgO1HK4kzz6w7EBLpoEHVJnYOTH0UbGF5")
dataset = [Example(x.split("\t")[1], x.split("\t")[0]) for x in open("preds.txt", "r").read().split("\n")]

def uploadToDeso(cover):
  return requests.post("https://node.deso.org/api/v0/upload-image", headers={"Content-Type": "multipart/form-data"}, data={"UserPublicKeyBase58Check": os.environ["UserPublicKeyBase58Check"], "JWT": os.environ["JWT"]}, files=[("file",(cover.filename,cover.stream,cover.mimetype))]).text

@crossdomain(origin="*")
@app.route("/blogs/all", methods=["GET", "POST"])
def all_blogs():
  return jsonify(json.loads(db.get_raw("blogs")))

# @crossdomain(origin="*")
# @app.route("/blogs/add", methods=["GET", "POST"])
# def add_blog():
#   data = request.form.to_dict()
#   tempuuid = str(uuid.uuid4())
#   data["rating"] = 0
#   data["bid"] = tempuuid
#   data["comments"] = []
#   print(request.form.keys())
#   data["cover"] = uploadToDeso(request.files["cover"])
#   data["content"] = markdown2html(data["content"])
#   db["blogs"].append(data)
#   return ""
  
@crossdomain(origin="*")
@app.route("/blogs/add", methods=["GET", "POST"])
def add_blog():
  data = request.json
  tempuuid = str(uuid.uuid4())
  data["rating"] = 0
  data["bid"] = tempuuid
  data["comments"] = []
  data["cover"] = json.loads(data["cover"])["ImageURL"]
  data["content"] = markdown2html(data["content"])
  db["blogs"].append(data)
  return ""

@crossdomain(origin="*")
@app.route("/blogs/get/<bid>", methods=["GET", "POST"])
def get_blog(bid):
  for ind, blog in enumerate(json.loads(db.get_raw("blogs"))):
    if blog["bid"] == bid:
      return jsonify(json.loads(db.get_raw("blogs"))[ind])

@crossdomain(origin="*")
@app.route("/blogs/comments/<bid>", methods=["GET", "POST"])
def add_comment(bid):
  classifications = co.classify(model="medium", taskDescription="This data set blocks negativity site wide in our travel blog application", outputIndicator="this is:", inputs=[request.json["content"]], examples=dataset).classifications
  for x in classifications:
    if x.prediction == "positive":
      for ind, blog in enumerate(json.loads(db.get_raw("blogs"))):
        if blog["bid"] == bid:
          db["blogs"][ind]["comments"].append(request.json)
    else:
      return jsonify({"nlp": "Our NLP processor recognized this as a negative comment. It said your comment was " + str(round(x.confidence[0].confidence*100, 2)) + "% negative. Please rephrase your comment."})
    return ""

@crossdomain(origin="*")
@app.route("/blogs/rate/<bid>", methods=["GET", "POST"])
def add_rate(bid):
  for ind, blog in enumerate(json.loads(db.get_raw("blogs"))):
    if blog["bid"] == bid:
      db["blogs"][ind]["rating"] += 1
  return ""

@crossdomain(origin="*")
@app.route("/users/log", methods=["GET", "POST"])
def log_activity():
  log_activity.done = False
  data = request.json
  data["distance"] = int(data["distance"]) / 1.609
  for ind, user in enumerate(json.loads(db.get_raw("users"))):
    if user["uid"] == data["uid"]:
      db["users"][ind]["runs"].append({"start_loc": data["start_loc"], "end_loc": data["end_loc"], "distance": data["distance"]})
      db["users"][ind]["distance"] += data["distance"]
      log_activity.done = True
  if not log_activity.done:
    db["users"].append({"uid": data["uid"], "distance": data["distance"], "runs": [{"start_loc": data["start_loc"], "end_loc": data["end_loc"], "distance": data["distance"]}]})
  return ""

@crossdomain(origin="*")
@app.route("/users/get/<uid>", methods=["GET", "POST"])
def get_user(uid):
  for ind, user in enumerate(json.loads(db.get_raw("users"))):
    if user["uid"] == uid:
      return jsonify(user)
  return ""

@crossdomain(origin="*")
@app.route("/leaderboard", methods=["GET", "POST"])
def get_leaderboard():
  return jsonify(sorted(json.loads(db.get_raw("users")), key=lambda k: k["distance"], reverse=True))

app.run(host="0.0.0.0")
