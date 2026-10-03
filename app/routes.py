from flask import request, jsonify
from app import app
from app.model import SimpleSVCModel
from app.data_layer import DataLayer
import numpy as np



model = SimpleSVCModel()
data_layer = DataLayer()

# Entrenar modelo al iniciar la app
model.train()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()    
    features_list = [   
            data['Pregnancies'],
            data['Glucose'],
            data['BloodPressure'],
            data['SkinThickness'],
            data['Insulin'],
            data['BMI'],
            data['DiabetesPedigreeFunction'],
            data['Age']
        ]

    features = np.array(features_list).reshape(1, -1)
    
    try:
        accuracy, prediction = model.predict_fun(features)
        data.update({"Outcome": prediction[0]})
        data_layer.insertValue(data)
        return jsonify({'prediction': prediction, 'confidence': accuracy})
    except Exception as e:
        print("estoy aca")
        print(str(e))
        return jsonify({'error': str(e)}), 500
    
@app.route('/train', methods=['GET'])
def is_trained():    
    if (model.trained()):
       message = 'The model is trained' 
    else: 
        message ='The model is not trained'

    return jsonify({'message': message}), 400


@app.route('/hello', methods=['GET'])
def hello():
    with open('index.html', 'r') as file:
        index = file.read()
    return index

