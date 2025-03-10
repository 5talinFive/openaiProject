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

# Configurar las credenciales de Google Sheets usando variables de entorno
credentials_dict = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL")
}

credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict)
client = gspread.authorize(credentials)

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
    
    # Inicializar la variable messages
    messages = session['messages'].copy()
    
    # Verificar si la entrada del usuario contiene "colegio rafael galeth"
    if "colegio rafael galeth" in user_input.lower():
        # Leer datos de la Google Sheet
        data = sheet.get_all_records()
        
        # Convertir los datos a una cadena JSON
        external_data = json.dumps(data)
        
        # Crear el mensaje para OpenAI incluyendo los datos externos como contexto
        messages.append({"role": "system", "content": f"External Data: {external_data}"})
    
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