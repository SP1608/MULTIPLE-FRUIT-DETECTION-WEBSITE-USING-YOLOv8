from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
from ultralytics import YOLO
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import sys
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from flask import Request
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


app = Flask(__name__)

prediction_done = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/manual')
def manual():
    return render_template('manual.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/recipe')
def recipe():
    return render_template('recipe.html')

@app.route('/predict', methods=['GET','POST'])
def predict():
    global prediction_done
    
    # Check if it's a POST request and contains the file part
    if request.method == 'POST' and 'file' in request.files:
        # Get the file from the request
        uploaded_file = request.files['file']

        # If the user does not select a file, the browser may submit an empty file without a filename
        if uploaded_file.filename == '':
            return 'No selected file'

        # Save the uploaded file to a secure location
        filename = secure_filename(uploaded_file.filename)
        file_path = f"uploads/{filename}"
        uploaded_file.save(file_path)

        # Set prediction_done flag to True
        prediction_done = True

        # Perform prediction
        model = YOLO("best.pt")
        results = model.predict(source=file_path, show=True, save=True, save_txt=True, save_conf=False, line_width=2)

        return display(uploaded_file.filename)
    else:
        # If it's not a POST request or doesn't contain the file part, return an error message
        return "No file part or wrong request method"

# @app.route('/display/<path:filename>')
# def display(filename):
#     folder_path = 'runs/detect'
#     subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
#     latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
#     directory = os.path.join(folder_path, latest_subfolder)

#     files = os.listdir(directory)
#     latest_file = files[0]

#     filename = os.path.join(directory, latest_file)

#     file_extension = filename.rsplit('.', 1)[1].lower()

#     if file_extension in {'jpg', 'jpeg', 'png'}:
#         return send_from_directory(directory, latest_file, environ=request.environ)
#     else:
#         return "Invalid file format"

import pathlib
from flask import send_from_directory, request

@app.route('/display/<path:filename>')
def display(filename):
    folder_path = 'runs/detect'
    directory = pathlib.Path(folder_path)
    subfolders = [f for f in directory.iterdir() if f.is_dir()]
    latest_subfolder = max(subfolders, key=lambda x: x.stat().st_ctime)
    files = list(latest_subfolder.iterdir())
    latest_file = max(files, key=lambda x: x.stat().st_ctime)

    filename = str(latest_file)

    file_extension = filename.rsplit('.', 1)[1].lower()

    if file_extension in {'jpg', 'jpeg', 'png'}:
        return send_from_directory(str(latest_subfolder), latest_file.name, environ=request.environ)
    else:
        return "Invalid file format"


@app.route('/result')
def result():
    global prediction_done
    global unique_fruits 
    
    # Check if prediction is done
    if not prediction_done:
        # Render the result page with a message indicating to select an image and predict first
        return render_template('result.html', message="Select an image and predict first")

    folder_path = 'runs/detect'
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
    directory = os.path.join(folder_path, latest_subfolder)

    labels_path = os.path.join(directory, 'labels')  # Assuming labels are stored in a folder named 'labels'

    label_files = [f for f in os.listdir(labels_path) if f.endswith('.txt')]
    latest_label_file = max(label_files, key=lambda x: os.path.getctime(os.path.join(labels_path, x)))

    label_filename = os.path.join(labels_path, latest_label_file)

    # Create a dictionary to map index numbers to fruit names
    fruit_dict = {0: "Orange", 1: "Apple", 2: "Banana", 3: "Grape"}

    # Create a set to store unique fruits
    unique_fruits = set()

    # Iterate through each line in the file
    with open(label_filename, 'r') as file:
        for index, line in enumerate(file):
            # Extract the first character of the line
            first_char = line[0]

            # Check if the first character is a key in the fruit dictionary
            fruit_name = fruit_dict.get(int(first_char))

            # Check if the fruit is not already in the set
            if fruit_name:
                unique_fruits.add(fruit_name)

    return render_template('result.html', fruits=unique_fruits)


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'GET':
        return render_template('recommend.html')

    global unique_fruits

    recipes_df = pd.read_csv('recipes_data_updated.csv')

    # Preprocess the data
    recipes_df['features'] = recipes_df['taste'] + ' ' + recipes_df['meal_type'] + ' ' + recipes_df['dietary_constraints']+ ' ' + recipes_df['recipe']

    # Train a Recommendation Model
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(recipes_df['features'])

    # Get form data
    r_type = request.form['type']
    r_taste = request.form['taste']
    r_allergy = request.form['dietary_constraints']

    def recommend_recipes_ml(fruit, r_type, r_taste, r_allergy):
        input_features = f"{r_taste} {r_type} {r_allergy}"
        input_vector = tfidf_vectorizer.transform([input_features])

        cosine_similarities = linear_kernel(input_vector, tfidf_matrix).flatten()
        similar_indices = cosine_similarities.argsort()[::-1]

        recommended_recipes = []
        recommended_recipes_detail=[]
        for idx in similar_indices:
            recipe = recipes_df.iloc[idx]
            if (fruit.strip().lower() in recipe['name'].lower() and
                recipe['meal_type'].lower() == r_type and
                recipe['taste'].lower() == r_taste and
                (r_allergy == "nothing" or all(allergy.strip() == "nothing" or allergy.strip() in recipe['dietary_constraints'].lower().split(',')) 
                 for allergy in r_allergy.split()) and
                recipe['name'] not in recommended_recipes):
                recommended_recipes_detail.append(recipe['name'])
                recommended_recipes_detail.append(recipe['recipe'])
            if len(recommended_recipes_detail) >= 5:
                break

        return recommended_recipes_detail

    recommended_recipes_dict = {}
    for fruit in unique_fruits:
        fruit_recommendations = recommend_recipes_ml(fruit, r_type, r_taste, r_allergy)
        if fruit_recommendations:
            recommended_recipes_dict[fruit] = fruit_recommendations
        else:
            recommended_recipes_dict[fruit] = {"NO RECIPE"}
    return render_template('recipe.html', recommended_recipes=recommended_recipes_dict)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/Database")
db = client["Database"]
collection = db["feedback"]

@app.route('/feedback', methods=['GET','POST'])
def feedback_post():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        feedback = request.form.get('enter_your_opinions_here')

        # Save the feedback to MongoDB
        collection.insert_one({"name": name, "email": email, "feedback": feedback})

        return redirect(url_for('feedback_success'))
    
    return render_template('feedback.html')

@app.route('/feedback_success')
def feedback_success():
    return render_template('feedback_success.html')

if __name__ == '__main__':
    app.run(debug=True)