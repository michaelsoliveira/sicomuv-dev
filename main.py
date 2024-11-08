import cv2
import pytesseract
import os
import numpy as np
import mtranslate
import keras.models
import speech_recognition as sr
import threading
import pyttsx3
from concurrent.futures import ThreadPoolExecutor
import warnings

# Suprimir avisos
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
tessdata_dir_config = '--tessdata-dir "C:\\Program Files\\Tesseract-OCR\\tessdata"'

# Dicionário de idiomas suportados (mantido como está)
idiomas = {
    'Afrikaans': 'af', 'Árabe': 'ar', 'Bengali': 'bn', 'Cantonês': 'yue', 'Catalão': 'ca',
    'Chinês': 'zh-tw', 'Croata': 'hr', 'Checo': 'cs', 'Dinamarquês': 'da', 'Holandês': 'nl',
    'Inglês': 'en', 'Filipino': 'fil', 'Finlandês': 'fi', 'Francês': 'fr', 'Alemão': 'de',
    'Grego': 'el', 'Gujarati': 'gu', 'Hebraico': 'he', 'Hindi': 'hi', 'Húngaro': 'hu',
    'Indonésio': 'id', 'Italiano': 'it', 'Japonês': 'ja', 'Javanês': 'jw', 'Coreano': 'ko',
    'Letão': 'lv', 'Lituano': 'lt', 'Malaio': 'ms', 'Marata': 'mr', 'Norueguês': 'no',
    'Polonês': 'pl', 'Português (Brasil)': 'pt-br', 'Português Portugal': 'pt-pt',
    'Romeno': 'ro', 'Russo': 'ru', 'Sérvio': 'sr', 'Eslovaco': 'sk', 'Esloveno': 'sl',
    'Espanhol': 'es', 'Suaíli': 'sw', 'Sueco': 'sv', 'Tâmil': 'ta', 'Telugu': 'te',
    'Tailandês': 'th', 'Turco': 'tr', 'Ucraniano': 'uk', 'Vietnamita': 'vi', 'Galês': 'cy'
}

# Inicializar o motor de fala pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('voice', 'brazil')
engine.setProperty('volume', 1.0)

def falar(texto):
    engine.say(texto)
    engine.runAndWait()

def reconhecer_comando(timeout=3):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.2)
        print("Ouvindo...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            comando = recognizer.recognize_google(audio, language='pt-BR')
            print(f"Comando reconhecido: {comando}")
            return comando.lower()
        except:
            return None

def selecionar_idioma_por_voz():
    falar("Por favor, me diga para qual idioma você gostaria de traduzir.")
    comando = reconhecer_comando()
    if comando:
        for nome, codigo in idiomas.items():
            if nome.lower() in comando:
                falar(f"Entendi que você quer traduzir para {nome}. Isso está correto?")
                confirmacao = reconhecer_comando()
                if confirmacao and ('sim' in confirmacao or 'correto' in confirmacao):
                    return codigo
    else:
        falar("Desculpe, não consegui identificar o idioma. Vamos tentar novamente?")

def load_trained_model(model_path):
    return keras.models.load_model(model_path)

def preprocess_image(image):
    return cv2.resize(image, (128, 128)) / 255.0

def convert_prediction_to_text(image):
    return pytesseract.image_to_string(image, lang='por', config=tessdata_dir_config)

def select_frame_por_voz(cap, result):
    while True:
        ret, frame = cap.read()
        if not ret:
            falar("Estou com dificuldades para capturar a imagem. Podemos tentar de novo?")
            continue
        cv2.imshow('frame', frame)

        if result['comando']:
            comando = result['comando']
            result['comando'] = None
            if "capturar" in comando or "enter" in comando:
                falar("Certo, vou capturar esta imagem. Tudo bem para você?")
                if reconhecer_comando() in ['sim', 'pode', 'ok', 'tudo bem']:
                    return frame
            elif "sair" in comando or "finalizar" in comando:
                falar("Você quer que eu encerre o programa?")
                if reconhecer_comando() in ['sim', 'pode', 'ok', 'encerre']:
                    result['fim'] = True
                    return None
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    return None

def obter_comandos_de_voz(result):
    while not result['fim']:
        comando = reconhecer_comando()
        if comando:
            result['comando'] = comando

def processar_imagem(frame, model, idioma_selecionado):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    processed_image = preprocess_image(gray)
    input_image = np.expand_dims(processed_image, axis=0)
    prediction = model.predict(input_image)

    if prediction is not None:
        text = convert_prediction_to_text(gray)
        print("Texto detectado:", text)

        falar("Estou traduzindo o texto agora. Só um momento, por favor.")
        translated_text = mtranslate.translate(text, idioma_selecionado, 'en')
        print("Tradução:", translated_text)

        if translated_text:
            falar(f"Aqui está a tradução: {translated_text}")

    cv2.imshow('Imagem Capturada', frame)

def main():
    falar("Olá! Bem-vindo ao SICOMUV, seu assistente de comunicação e tradução. Como posso te ajudar hoje?")

    idioma_selecionado = selecionar_idioma_por_voz()
    falar("Ótimo! Agora que escolhemos o idioma, você pode me pedir para capturar uma imagem ou encerrar o programa. O que você prefere?")

    # Corrigindo o caminho do modelo
    model_path = f"{os.getcwd()}/dataset/train.h5"
    model = load_trained_model(model_path)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            falar("Estou com problemas para acessar a câmera. Pode verificar se ela está conectada corretamente?")
            return

    result = {'comando': None, 'fim': False}
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(obter_comandos_de_voz, result)

        while not result['fim']:
            falar("Estou pronto para capturar uma imagem. Diga 'capturar' quando quiser.")
            selected_frame = select_frame_por_voz(cap, result)
            if result['fim']:
                break
            if selected_frame is not None:
                falar("Imagem capturada! Estou processando, só um instante.")
                processar_imagem(selected_frame, model, idioma_selecionado)

    falar("Estou encerrando o programa. Foi um prazer ajudar você hoje. Obrigado por usar o SICOMUV!")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()