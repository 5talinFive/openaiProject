from flask import Flask, request, render_template, session
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia esto a una clave secreta segura

# Configura la clave de API para autenticar las solicitudes a OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurar las credenciales de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Abrir la hoja de cálculo y seleccionar la hoja
sheet = client.open("DB_OPENAI").sheet1

@app.route('/')
def index():
    if 'messages' not in session:
        session['messages'] = [{"role": "system", "content": "You are a helpful assistant."}]
    return render_template('index.html', messages=session['messages'][1:])  # Excluir el mensaje del sistema

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['user_input']
    
    # Añadir el mensaje del usuario al historial
    session['messages'].append({"role": "user", "content": user_input})
    
    # Verificar si la entrada del usuario contiene "colegio rafael galeth"
    if "colegio rafael galeth" in user_input.lower():
        # Leer datos de la Google Sheet
        data = sheet.get_all_records()
        
        # Convertir los datos a una cadena JSON
        external_data = json.dumps(data)
        
        # Crear el mensaje para OpenAI incluyendo los datos externos
        messages = session['messages'] + [{"role": "user", "content": f"External Data: {external_data}"}]
    else:
        # Crear el mensaje para OpenAI sin los datos externos
        messages = session['messages']
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    response_text = response.choices[0].message['content'].strip()
    
    # Añadir la respuesta del asistente al historial
    session['messages'].append({"role": "assistant", "content": response_text})
    
    return render_template('index.html', messages=session['messages'][1:])  # Excluir el mensaje del sistema

if __name__ == '__main__':
    app.run(debug=True)