from flask import Flask, render_template, request, jsonify,redirect, url_for
from gtts import gTTS
import google.generativeai as genai
import base64
import io
import os
import PIL.Image
import requests

app = Flask(__name__)

# OpenWeatherMap API Key
API_KEY = "73b48ecfece17f28d57b8f06a4dd9306"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

# Air Quality API Endpoint
AIR_QUALITY_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

genai.configure(api_key="AIzaSyDqYe2MmvwxHZR8WBeefRx1eagXF-dydyA")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/air')
def air():
        return render_template('air.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/map')
def map():
    return render_template('map.html')

API_KEY = "2bfaac82a56640299f7c2353da4a50ec"
BASE_URL = "https://newsapi.org/v2/everything"

# Fetch news articles from NewsAPI
def get_news():
    params = {
        'q': 'environment OR climate OR sustainability',  # Query for environmental news
        'language': 'en',
        'apiKey': API_KEY,
        'pageSize': 10,
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        return []

@app.route('/api/news')
def news_api():
    articles = get_news()
    return jsonify(articles)

@app.route('/news')
def news():
    return render_template('news.html')
@app.route('/video')
def video():
    return render_template('videos.html')

# Route for Quiz page
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

# Route for Sell page
@app.route('/sell')
def sell():
    return render_template('sell.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    data = request.json
    user_message = data['message']
    model = genai.GenerativeModel('gemini-1.5-flash')
    rply = model.generate_content(f"{user_message}  answer to this environmental sustainability related question , give human like response informative and casual tone in one or 2 lines without any */ symbols")

    return jsonify({'response': rply.text})   

@app.route('/scan')
def scan():
    return render_template('scan.html')


@app.route('/uploads', methods=['GET','POST'])
def uploads():
    if request.method == 'POST':
        # Get the image data from the request
        data = request.json
        image_data = data.get('image')

        # Decode the base64 image data
        image_data = image_data.split(',')[1]
        image_binary = base64.b64decode(image_data)

        # Save the image to a file on your local PC
        img_path = 'captured_image.png'
        with open(img_path, 'wb') as img_file:
            img_file.write(image_binary)

        # Load the image
        img = PIL.Image.open(io.BytesIO(image_binary))

        # Use Generative AI model to generate text from the image
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(["analyze this image and give recommendations on how to recycle or upcycle the product shown in the image. in short less than 7 lines point by point ", img], stream=True)
        response.resolve()
        rply=response.text
        rply=rply.replace("**", "")

        with open('static/describe.txt', 'w') as f:
            f.write(rply)

        # Generate speech from the extracted text
        tts = gTTS(text=rply, lang='en')

        # Save the speech to a file
        audio_path = 'static/output.mp3'
        tts.save(audio_path)
        audio_url = f"/{audio_path}"
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    audio_url = "output.mp3"
    with open('static/describe.txt', 'r') as f:
        describe = f.read()
    return render_template('result.html',recipe=describe, audio=audio_url)

@app.route('/gpt', methods=['GET', 'POST'])
def gpt():
    response_text = ""
    encoded_string = ""
    
    if request.method == 'POST':
        # Get transcribed text from the form
        transcribed_text = request.form.get('transcribed_text')
        
        # Generate response using the transcribed text
        if transcribed_text:
            # Generate response using Generative AI model
            model = genai.GenerativeModel('gemini-1.5-flash')
            rply = model.generate_content("Respond to user queries related to environmental sustainability in one or two lines give human like response informative and casual tone " + transcribed_text)
            response_text = rply.text
            response_text=response_text.replace("**", "")
            print(response_text)
            
            # Convert response text to speech
            tts = gTTS(text=response_text, lang='en')
            tts.save('response.mp3')
            
            # Encode the audio file as base64
            with open("response.mp3", "rb") as audio_file:
                encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
        
        else:
            response_text = "No input provided."
        
        # Return the response to the client
        return render_template('gpt.html', response=response_text, audio=encoded_string)
    
    # If it's a GET request, render the form
    return render_template('gpt.html')


    
@app.route('/get_weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', 'New York')
    weather_url = f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric"
    
    # Get weather data
    weather_response = requests.get(weather_url).json()
    
    if weather_response.get('cod') != 200:
        return jsonify({'error': 'City not found or invalid API key'}), 400

    weather_data = {
        'city': city,
        'temperature': weather_response['main']['temp'],
        'humidity': weather_response['main']['humidity'],
        'wind_speed': weather_response['wind']['speed'],
        'weather': weather_response['weather'][0]['description'],
        'high': weather_response['main']['temp_max'],
        'low': weather_response['main']['temp_min'],
        'sunrise': weather_response['sys']['sunrise'],
        'sunset': weather_response['sys']['sunset'],
        'date': weather_response['dt'],
    }

    # Get air quality data
    lat = weather_response['coord']['lat']
    lon = weather_response['coord']['lon']
    air_quality_url = f"{AIR_QUALITY_URL}?lat={lat}&lon={lon}&appid={API_KEY}"
    air_quality_response = requests.get(air_quality_url).json()

    air_quality_data = {
        'aqi': air_quality_response['list'][0]['main']['aqi'],
        'pm10': air_quality_response['list'][0]['components']['pm10'],
        'pm2_5': air_quality_response['list'][0]['components']['pm2_5'],
        'co': air_quality_response['list'][0]['components']['co'],
        'no': air_quality_response['list'][0]['components']['no'],
        'so2': air_quality_response['list'][0]['components']['so2'],
    }

    return jsonify({
        'weather_data': weather_data,
        'air_quality_data': air_quality_data
    })

if __name__ == '__main__':
    app.run(debug=True)
