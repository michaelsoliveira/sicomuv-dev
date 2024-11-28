import cv2
import pytesseract
import os
import numpy as np
import keras.models
import speech_recognition as sr
import pyttsx3
from concurrent.futures import ThreadPoolExecutor
import warnings
from dotenv import load_dotenv
import logging
import sys
import importlib

# Verificação de dependências
dependencies = ['cv2', 'pytesseract', 'numpy', 'keras', 'speech_recognition', 'pyttsx3', 'dotenv', 'matplotlib', 'deep_translator']
for module in dependencies:
    if importlib.util.find_spec(module) is None:
        print(f"Erro: A biblioteca {module} não está instalada. Por favor, instale-a usando 'pip install {module}'")
        sys.exit(1)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carregar variáveis de ambiente
load_dotenv()

# Suprimir avisos
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

tesseract_path=os.getenv('TESSPATH')
tessdata_dir=os.getenv('TESSDIR')

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSPATH')
os.environ['TESSDATA_PREFIX'] = f"{os.getenv('TESSDIR')}\\tessdata\\"
tessdata_dir_config = f'--tessdata-dir {os.getenv("TESSDIR")}\\tessdata\\'
pytesseract.pytesseract.tesseract_cmd = f"{os.getenv('TESSPATH')}"



if not tesseract_path or not tessdata_dir:
    logging.error("As variáveis de ambiente TESSPATH e TESSDIR devem ser definidas no arquivo .env")
    print("Por favor, configure as variáveis de ambiente TESSPATH e TESSDIR no arquivo .env")
    sys.exit(1)

if not os.path.exists(tesseract_path):
    logging.error(f"O caminho do Tesseract não existe: {tesseract_path}")
    print(f"O caminho do Tesseract especificado não existe. Por favor, verifique o caminho: {tesseract_path}")
    sys.exit(1)

pytesseract.pytesseract.tesseract_cmd = tesseract_path
os.environ['TESSDATA_PREFIX'] = os.path.join(tessdata_dir, "tessdata")
tessdata_dir_config = f'--tessdata-dir "{tessdata_dir}\\tessdata"'

# Dicionário de idiomas suportados
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

# Inicializar o motor de fala pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 195)
engine.setProperty('voice', 'brazil')
engine.setProperty('volume', 2.0)

def falar(texto):
    logging.info(f"Assistente: {texto}")
    engine.say(texto)
    engine.runAndWait()

def reconhecer_comando(timeout=5, max_tentativas=3):
    recognizer = sr.Recognizer()
    for tentativa in range(max_tentativas):
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            logging.info(f"Ouvindo... (Tentativa {tentativa + 1})")
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
                comando = recognizer.recognize_google(audio, language='pt-BR')
                logging.info(f"Comando reconhecido: {comando}")
                return comando.lower()
            except sr.WaitTimeoutError:
                logging.warning("Tempo de espera excedido.")
            except sr.UnknownValueError:
                logging.warning("Não foi possível entender o áudio.")
            except sr.RequestError as e:
                logging.error(f"Erro na requisição ao serviço de reconhecimento de fala; {e}")
                falar("Desculpe, estou tendo problemas para me conectar ao serviço de reconhecimento de voz. Por favor, verifique sua conexão com a internet.")
                return None
    
    falar("Desculpe, não consegui entender. Pode repetir, por favor?")
    return None

def selecionar_idioma_por_voz():
    falar("Por favor, me diga para qual idioma você gostaria de traduzir.")
    while True:
        comando = reconhecer_comando()
        if comando:
            for nome, codigo in idiomas.items():
                if nome.lower() in comando:
                    falar(f"Entendi que você quer traduzir para {nome}.")
                    # confirmacao = reconhecer_comando()
                    # if confirmacao and ('sim' in confirmacao or 'correto' in confirmacao):
                    return codigo
        falar("Desculpe, não consegui identificar o idioma. Vamos tentar novamente?")

def load_trained_model(model_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"O arquivo do modelo não existe: {model_path}")
    try:
        return keras.models.load_model(model_path)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar o modelo: {e}")

def preprocess_image(image):
    return cv2.resize(image, (128, 128)) / 255.0

def convert_prediction_to_text(image):
    return pytesseract.image_to_string(image, config=tessdata_dir_config)

def inicializar_camera():
    for i in range(3):  # Tenta as câmeras 0, 1 e 2
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            return cap
    raise RuntimeError("Não foi possível acessar nenhuma câmera.")

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

def traduzir_texto(texto, idioma_destino):
    if not texto.strip():
        return "Nenhum texto detectado para tradução."
    
    try:
        tradutor = GoogleTranslator(source="auto", target=idioma_destino)
        texto_traduzido = tradutor.translate(texto)
        return texto_traduzido
    except Exception as e:
        logging.error(f"Erro na tradução: {e}")
        return f"Erro na tradução. Por favor, verifique sua conexão com a internet."

def processar_imagem(frame, model, idioma_selecionado):
    try:
        if frame is None or frame.size == 0:
            falar("A imagem capturada não é válida. Vamos tentar novamente.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        processed_image = preprocess_image(gray)
        input_image = np.expand_dims(processed_image, axis=0)
        prediction = model.predict(input_image)
        logging.info(f"Prediction: {prediction}")
        print(prediction)
        text = convert_prediction_to_text(gray)
        logging.info(f"Texto detectado: {text}")

        if text.strip():
            falar("Estou traduzindo o texto agora. Só um momento, por favor.")
            translated_text = traduzir_texto(text, idioma_selecionado)
            logging.info(f"Tradução: {translated_text}")
            falar(f"Aqui está a tradução: {translated_text}")
        else:
            falar("Não detectei nenhum texto na imagem.")

        cv2.imshow('Imagem Capturada', frame)
    except Exception as e:
        logging.error(f"Erro ao processar imagem: {e}")
        falar("Ocorreu um erro ao processar a imagem. Vamos tentar novamente.")

def main():
    falar("Olá! Bem-vindo ao SICOMUV, seu assistente de comunicação e tradução. Como posso te ajudar hoje?")
    
    try:
        idioma_selecionado = None
        while not idioma_selecionado:
            idioma_selecionado = selecionar_idioma_por_voz()
        falar("Ótimo! Agora que escolhemos o idioma, você pode me pedir para capturar uma imagem ou encerrar o programa. O que você prefere?")
        logging.info(f"Idioma selecionado: {idioma_selecionado}")

        model_path = os.path.join(os.getcwd(), "dataset", "train.h5")
        try:
            model = load_trained_model(model_path)
        except (FileNotFoundError, RuntimeError) as e:
            falar(f"Erro ao carregar o modelo: {e}")
            return

        try:
            cap = inicializar_camera()
        except RuntimeError as e:
            falar(str(e))
            return

        result = {'comando': None, 'fim': False}
        with ThreadPoolExecutor(max_workers=1) as executor:
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
    except KeyboardInterrupt:
        falar("Programa interrompido pelo usuário.")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        falar("Ocorreu um erro inesperado. O programa será encerrado.")
    finally:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()