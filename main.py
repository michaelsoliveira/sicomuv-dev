import cv2
import pytesseract
import os
import numpy as np
import keras.models
import speech_recognition as sr
import threading
import pyttsx3
from concurrent.futures import ThreadPoolExecutor
import warnings
from dotenv import load_dotenv
import matplotlib.pyplot as plt 
from deep_translator import GoogleTranslator

load_dotenv()

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSPATH')
os.environ['TESSDATA_PREFIX'] = f"{os.getenv('TESSDIR')}\\tessdata"
tessdata_dir_config = f'--tessdata-dir "{os.getenv("TESSDIR")}\\tessdata"'

idiomas = {
    'Afrikaans': 'af', 'Árabe': 'ar', 'Bengali': 'bn', 'Cantonês': 'yue', 'Catalão': 'ca',
    'Chinês': 'zh-tw', 'Croata': 'hr', 'Checo': 'cs', 'Dinamarquês': 'da', 'Holandês': 'nl',
    'Inglês': 'en', 'Filipino': 'fil', 'Finlandês': 'fi', 'Francês': 'fr', 'Alemão': 'de',
    'Grego': 'el', 'Gujarati': 'gu', 'Hebraico': 'he', 'Hindi': 'hi', 'Húngaro': 'hu',
    'Indonésio': 'id', 'Italiano': 'it', 'Japonês': 'ja', 'Javanês': 'jw', 'Coreano': 'ko',
    'Letão': 'lv', 'Lituano': 'lt', 'Malaio': 'ms', 'Marata': 'mr', 'Norueguês': 'no',
    'Polonês': 'pl', 'Português Brasil': 'pt', 'Portugues Portugal': 'pt-pt',
    'Romeno': 'ro', 'Russo': 'ru', 'Sérvio': 'sr', 'Eslovaco': 'sk', 'Esloveno': 'sl',
    'Espanhol': 'es', 'Suaíli': 'sw', 'Sueco': 'sv', 'Tâmil': 'ta', 'Telugu': 'te',
    'Tailandês': 'th', 'Turco': 'tr', 'Ucraniano': 'uk', 'Vietnamita': 'vi', 'Galês': 'cy'
}

engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('voice', 'brazil')
engine.setProperty('volume', 1.0)

def falar(texto):
    print(f"Assistente: {texto}")
    engine.say(texto)
    engine.runAndWait()

def reconhecer_comando(timeout=5):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("Ouvindo...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            comando = recognizer.recognize_google(audio, language='pt-BR')
            print(f"Comando reconhecido: {comando}")
            return comando.lower()
        except sr.WaitTimeoutError:
            print("Tempo de espera excedido.")
        except sr.UnknownValueError:
            print("Não foi possível entender o áudio.")
        except sr.RequestError as e:
            print(f"Erro na requisição ao serviço de reconhecimento de fala; {e}")
    return None

def selecionar_idioma_por_voz():
    falar("Por favor, me diga para qual idioma você gostaria de traduzir.")
    while True:
        comando = reconhecer_comando()
        if comando:
            for nome, codigo in idiomas.items():
                if nome.lower() in comando:
                    falar(f"Entendi que você quer traduzir para {nome}. Isso está correto?")
                    confirmacao = reconhecer_comando()
                    if confirmacao and ('sim' in confirmacao or 'correto' in confirmacao):
                        return codigo
        falar("Desculpe, não consegui identificar o idioma. Vamos tentar novamente?")

def load_trained_model(model_path):
    try:
        return keras.models.load_model(model_path)
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        return None

def preprocess_image(image):
    return cv2.resize(image, (128, 128)) / 255.0

def convert_prediction_to_text(image):
    return pytesseract.image_to_string(image, config=tessdata_dir_config)

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
                falar("Certo, vou capturar esta imagem.")
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
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        processed_image = preprocess_image(gray)
        input_image = np.expand_dims(processed_image, axis=0)
        prediction = model.predict(input_image)
        print(f"Prediction: {prediction}")
        if prediction is not None:
            text = convert_prediction_to_text(gray)
            print("Texto detectado:", text)

            if text.strip():
                falar("Estou traduzindo o texto agora. Só um momento, por favor.")
                tradutor = GoogleTranslator(source="auto", target=idioma_selecionado)
                translated_text = tradutor.translate(text)
                print(f"Tradução: {translated_text}")
                if translated_text:
                    falar(f"Aqui está a tradução: {translated_text}")
            else:
                falar("Não detectei nenhum texto na imagem.")

        cv2.imshow('Imagem Capturada', frame)
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        falar("Ocorreu um erro ao processar a imagem.")

def main():
    falar("Olá! Bem-vindo ao SICOMUV, seu assistente de comunicação e tradução. Como posso te ajudar hoje?")
    
    try:
        idioma_selecionado = None
        while not idioma_selecionado:
            idioma_selecionado = selecionar_idioma_por_voz()
        falar("Ótimo! Agora que escolhemos o idioma, você pode me pedir para capturar uma imagem ou encerrar o programa. O que você prefere?")
        print(f"Idioma selecionado: {idioma_selecionado}")

        model_path = os.path.join(os.getcwd(), "dataset", "train.h5")
        model = load_trained_model(model_path)
        if model is None:
            falar("Não foi possível carregar o modelo. O programa será encerrado.")
            return

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
    except Exception as e:
        print(f"Erro inesperado: {e}")
        falar("Ocorreu um erro inesperado. O programa será encerrado.")
    finally:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()