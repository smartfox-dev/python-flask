from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from threading import Thread
from flask_socketio import SocketIO
import time 
import random
from googletrans import Translator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
cors = CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')

timeCount = 1
output_value = 0
defects_value = 0
percentage = 0
socketConnections = []
# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

############################## Model ################################
# Define the model
class Setting(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(200), nullable=False)
  output = db.Column(db.String(200), nullable=False)
  defects = db.Column(db.String(200), nullable=False)
  header = db.Column(db.String(200), nullable=False)
  limit = db.Column(db.String(200), nullable=False)

  def __repr__(self):
    return f"<Setting {self.name}>"

class Output(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  count = db.Column(db.String(200), nullable=False)

  def __repr__(self):
    return f"<Output {self.name}>"
  
class Defects(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  count = db.Column(db.String(200), nullable=False)

  def __repr__(self):
    return f"<Defects {self.name}>"   

####################### Create the database #########################
with app.app_context():
  if not os.path.exists('database.db'):
    db.create_all()
  else:
    # with db.session.begin(subtransactions=True):
      db.session.query(Output).delete()
      db.session.query(Defects).delete()
      db.session.execute("DELETE FROM sqlite_sequence WHERE name='Output'")
      db.session.execute("DELETE FROM sqlite_sequence WHERE name='Defects'")
      db.session.commit()

############################# Routes ################################
@app.route('/api/setting/save', methods=['POST'])
def save_setting():
  data = request.get_json()
  new_item = Setting(name=data['name'], output=data['output'], defects=data['defects'], header=data['header'], limit=data['limit'])
  db.session.add(new_item)
  db.session.commit()
  saved_item = Setting.query.filter_by(id=new_item.id).first()
  if saved_item:
    return jsonify({
      'status': 0, 
      'data':{
        'id': saved_item.id, 
        'name': saved_item.name, 
        'output': saved_item.output, 
        'defects': saved_item.defects, 
        'header': saved_item.header,      
        'limit': saved_item.limit,
      }
    }), 201
  else: 
    return jsonify({'status': 1, "message": "Failed to fetch saved item"}), 201

@app.route('/api/setting/get', methods=['POST'])
def get_setting():
  last_item = Setting.query.order_by(Setting.id.desc()).first()
  if last_item:
    return jsonify({
      'status': 0, 
      'data':{
        'id': last_item.id, 
        'name': last_item.name, 
        'output': last_item.output, 
        'defects': last_item.defects, 
        'header': last_item.header,      
        'limit': last_item.limit,
      }
    }), 201
  else:
    return jsonify({'status': 1, 'message': 'No items found'}), 404

@app.route('/api/setting/translate', methods=['POST'])
def get_translate():
    data = request.get_json()
    word_array = data['array']
    translator = Translator()
    translated_array = []
    
    for word in word_array:
        try:
            translated = translator.translate(word, data['language'])
            translated_array.append(translated.text)
        except Exception as e:
            print(f"Error translating '{word}': {e}")
            translated_array.append(word)  # Fallback to original word in case of error
    return jsonify({'status': 0, 'data': translated_array})

############################# Thread #############################
def generate_dumy_data():
  global output_value, defects_value, timeCount
  while True:
    with app.app_context():
      # Increment output value randomly
      output_value += random.randint(1, 10)
     
      if timeCount % 5 == 0:
        timeCount = 0
        defects_value += random.randint(5, 10)
        #Insert data into the database
        new_output = Output(count=output_value)
        db.session.add(new_output)
        db.session.commit()
        new_defects = Defects(count=defects_value)
        db.session.add(new_defects)
        db.session.commit()

      # Increment defects value randomly every 5 seconds
      # print('--------Time Increment------:', timeCount)
      timeCount += 1
      time.sleep(1) # Sleep for 1 second

############################# Socket ################################
@socketio.on('connect')
def handle_connect():
  print('----------------Client connected----------------')

@socketio.on('disconnect')
def handle_disconnect():
  print('----------------Client disconnected-------------')

@socketio.on('dumy_data')
def handle_data():
  #Calculate percentage
  percentage = round((defects_value / output_value) * 100, 2) if output_value !=0 else 0
  #Emit data to the frontend
  data = {'output': output_value, 'defects': defects_value, 'percentage': percentage}
  socketio.emit('dumy_data', data)


######################## Main route for testing ######################
@app.route('/')
def index():
  return "Hello World!"

if __name__ == '__main__':
  Thread(target=generate_dumy_data).start()
  socketio.run(app)