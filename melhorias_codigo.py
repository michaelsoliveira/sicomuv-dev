import os
import sys
import logging
import subprocess
import ast
import astor
import shutil

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminho do projeto
PROJECT_PATH = r"C:\Users\willi\Documents\FACULDADE\10º SEMESTRE\PROJETO FINAL 2\VALIDAÇÃO MANUAL - WILLIAM - CODIGO TESTE\SICOMUV_Clone"

def install_package(package):
    """Instala um pacote Python usando pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def setup_environment():
    """Configura o ambiente e verifica as dependências necessárias."""
    logging.info("Configurando o ambiente...")
    
    if not os.path.exists(PROJECT_PATH):
        logging.error(f"O diretório do projeto não existe: {PROJECT_PATH}")
        sys.exit(1)
    
    required_packages = [
        'opencv-python', 'numpy', 'pytesseract', 'Pillow', 
        'googletrans==3.1.0a0', 'gTTS', 'pygame', 'astor'
    ]
    
    for package in required_packages:
        try:
            __import__(package.split('==')[0])
        except ImportError:
            logging.info(f"Instalando {package}...")
            install_package(package)
    
    logging.info("Ambiente configurado com sucesso.")

def analyze_project_structure():
    """Analisa a estrutura atual do projeto."""
    logging.info("Analisando estrutura do projeto...")
    structure = {}
    for root, dirs, files in os.walk(PROJECT_PATH):
        structure[root] = {
            "directories": dirs,
            "files": [f for f in files if f.endswith('.py')]
        }
    return structure

def analyze_python_file(file_path):
    """Analisa um arquivo Python e retorna informações sobre seu conteúdo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        
        return {
            "imports": analyzer.imports,
            "functions": analyzer.functions,
            "classes": analyzer.classes,
            "global_vars": analyzer.global_vars
        }
    except Exception as e:
        logging.error(f"Erro ao analisar {file_path}: {str(e)}")
        return {"imports": [], "functions": [], "classes": [], "global_vars": []}

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.functions = []
        self.classes = []
        self.global_vars = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append(f"{node.module}.{alias.name}")

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)

    def visit_ClassDef(self, node):
        self.classes.append(node.name)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.global_vars.append(target.id)

def improve_python_file(file_path):
    """Melhora o código de um arquivo Python."""
    logging.info(f"Melhorando o arquivo: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        transformer = CodeImprover()
        improved_tree = transformer.visit(tree)
        
        improved_code = astor.to_source(improved_tree)
        
        # Faz backup do arquivo original
        backup_path = file_path + '.bak'
        shutil.copy2(file_path, backup_path)
        
        # Escreve o código melhorado
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(improved_code)
        
        logging.info(f"Arquivo melhorado. Backup criado em {backup_path}")
    except Exception as e:
        logging.error(f"Erro ao melhorar {file_path}: {str(e)}")

class CodeImprover(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        # Adiciona docstrings às funções que não as têm
        if not ast.get_docstring(node):
            docstring = ast.Str(s=f"Função {node.name}")
            node.body.insert(0, ast.Expr(value=docstring))
        
        # Adiciona anotações de tipo para argumentos e retorno
        for arg in node.args.args:
            if arg.annotation is None:
                arg.annotation = ast.Name(id='Any', ctx=ast.Load())
        if node.returns is None:
            node.returns = ast.Name(id='Any', ctx=ast.Load())
        
        return node

    def visit_ClassDef(self, node):
        # Adiciona docstrings às classes que não as têm
        if not ast.get_docstring(node):
            docstring = ast.Str(s=f"Classe {node.name}")
            node.body.insert(0, ast.Expr(value=docstring))
        return node
def optimize_imports(file_path):
    """Otimiza e organiza as importações em um arquivo Python."""
    logging.info(f"Otimizando importações em: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(astor.to_source(node).strip())
        
        # Remove duplicatas e ordena
        imports = sorted(set(imports))
        
        # Reescreve o arquivo com importações organizadas
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write("from typing import Any, List, Dict\n")
            file.write("\n".join(imports) + "\n\n")
            in_imports = False
            for line in lines:
                if line.startswith(("import ", "from ")):
                    in_imports = True
                elif in_imports and not line.strip():
                    continue
                else:
                    in_imports = False
                    file.write(line)
        
        logging.info(f"Importações otimizadas em: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao otimizar importações em {file_path}: {str(e)}")

def add_unit_tests(file_path):
    """Adiciona testes unitários ao arquivo."""
    logging.info(f"Adicionando testes unitários em: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        
        # Adiciona imports necessários para testes
        imports = ast.parse("import unittest\nimport doctest").body
        tree.body = imports + tree.body
        
        # Adiciona classe de teste
        test_class = ast.parse("""
class TestSICOMUV(unittest.TestCase):
    def test_process_image(self):
        # Adicione testes para process_image aqui
        pass

    def test_perform_ocr(self):
        # Adicione testes para perform_ocr aqui
        pass

    def test_translate_text(self):
        # Adicione testes para translate_text aqui
        pass

    def test_text_to_speech(self):
        # Adicione testes para text_to_speech aqui
        pass

if __name__ == '__main__':
    unittest.main()
    doctest.testmod()
    """).body
        
        tree.body.extend(test_class)
        
        improved_code = astor.to_source(tree)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(improved_code)
        
        logging.info(f"Testes unitários adicionados em: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao adicionar testes unitários em {file_path}: {str(e)}")

def optimize_performance(file_path):
    """Realiza otimizações de performance no arquivo."""
    logging.info(f"Otimizando performance em: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        transformer = PerformanceOptimizer()
        optimized_tree = transformer.visit(tree)
        
        optimized_code = astor.to_source(optimized_tree)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(optimized_code)
        
        logging.info(f"Performance otimizada em: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao otimizar performance em {file_path}: {str(e)}")

class PerformanceOptimizer(ast.NodeTransformer):
    def visit_For(self, node):
        # Converte loops for em list comprehensions quando possível
        if isinstance(node.body[0], ast.Assign) and len(node.body) == 1:
            target = node.body[0].targets[0]
            value = node.body[0].value
            return ast.Assign(
                targets=[node.body[0].targets[0]],
                value=ast.ListComp(
                    elt=value,
                    generators=[ast.comprehension(
                        target=node.target,
                        iter=node.iter,
                        ifs=[],
                        is_async=0
                    )]
                )
            )
        return node

def create_requirements_file():
    """Cria um arquivo requirements.txt com as dependências do projeto."""
    logging.info("Criando arquivo requirements.txt")
    
    requirements = [
        'opencv-python',
        'numpy',
        'pytesseract',
        'Pillow',
        'googletrans==3.1.0a0',
        'gTTS',
        'pygame',
        'astor'
    ]
    
    try:
        with open(os.path.join(PROJECT_PATH, 'requirements.txt'), 'w') as f:
            for req in requirements:
                f.write(f"{req}\n")
        
        logging.info("Arquivo requirements.txt criado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao criar arquivo requirements.txt: {str(e)}")

def create_readme():
    """Cria ou atualiza o arquivo README.md do projeto."""
    logging.info("Criando/atualizando arquivo README.md")
    
    readme_content = """
# SICOMUV - Sistema de Comunicação Universal por Voz

## Descrição
SICOMUV é uma aplicação inovadora que utiliza processamento de imagem, OCR, tradução e síntese de voz para facilitar a comunicação entre diferentes idiomas.

## Funcionalidades Principais
- Captura de texto através de imagens
- Reconhecimento óptico de caracteres (OCR)
- Tradução de texto para múltiplos idiomas
- Conversão de texto para fala

## Instalação
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure o Tesseract OCR

## Uso
Execute `python main.py` e siga as instruções na interface gráfica.

## Desenvolvimento
- Use o ambiente virtual
- Execute os testes: `python -m unittest discover tests`

## Contribuição
Consulte CONTRIBUTING.md para detalhes sobre como contribuir para o projeto.

## Licença
Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.
"""
    
    try:
        with open(os.path.join(PROJECT_PATH, 'README.md'), 'w') as f:
            f.write(readme_content)
        
        logging.info("Arquivo README.md criado/atualizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao criar/atualizar README.md: {str(e)}")
def create_gitignore():
    """Cria um arquivo .gitignore para o projeto."""
    logging.info("Criando arquivo .gitignore")
    
    gitignore_content = """
# Arquivos e diretórios Python
__pycache__/
*.py[cod]
*$py.class

# Ambiente virtual
venv/
env/

# Arquivos de IDE
.vscode/
.idea/

# Arquivos de log
*.log

# Arquivos temporários
temp_audio.mp3

# Arquivos de configuração local
config.ini

# Arquivos de saída
output/
"""
    
    try:
        with open(os.path.join(PROJECT_PATH, '.gitignore'), 'w') as f:
            f.write(gitignore_content)
        
        logging.info("Arquivo .gitignore criado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao criar arquivo .gitignore: {str(e)}")

def final_project_setup():
    """Realiza configurações finais do projeto."""
    create_readme()
    create_gitignore()
    
    # Cria diretório para testes se não existir
    tests_dir = os.path.join(PROJECT_PATH, 'tests')
    if not os.path.exists(tests_dir):
        try:
            os.makedirs(tests_dir)
            logging.info(f"Diretório de testes criado: {tests_dir}")
        except Exception as e:
            logging.error(f"Erro ao criar diretório de testes: {str(e)}")
    
    # Cria um arquivo __init__.py vazio no diretório de testes
    try:
        with open(os.path.join(tests_dir, '__init__.py'), 'w') as f:
            pass
        logging.info("Arquivo __init__.py criado no diretório de testes.")
    except Exception as e:
        logging.error(f"Erro ao criar arquivo __init__.py: {str(e)}")
    
    logging.info("Configuração final do projeto concluída.")

def optimize_sicomuv_specific(file_path):
    """Aplica otimizações específicas para o SICOMUV_Clone."""
    logging.info(f"Aplicando otimizações específicas do SICOMUV em: {file_path}")
    
    try:
        improve_python_file(file_path)
        optimize_imports(file_path)
        add_unit_tests(file_path)
        optimize_performance(file_path)
        
        logging.info(f"Otimizações específicas do SICOMUV concluídas em: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao aplicar otimizações em {file_path}: {str(e)}")

def improve_project():
    """Melhora todos os arquivos Python no projeto."""
    for root, dirs, files in os.walk(PROJECT_PATH):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                optimize_sicomuv_specific(file_path)

def main():
    try:
        setup_environment()
        project_structure = analyze_project_structure()
        
        logging.info("Análise da estrutura do projeto concluída.")
        for path, content in project_structure.items():
            logging.info(f"Diretório: {path}")
            logging.info(f"  Subdiretórios: {', '.join(content['directories'])}")
            logging.info(f"  Arquivos Python: {', '.join(content['files'])}")
            
            for py_file in content['files']:
                file_path = os.path.join(path, py_file)
                file_analysis = analyze_python_file(file_path)
                logging.info(f"  Análise de {py_file}:")
                logging.info(f"    Imports: {', '.join(file_analysis['imports'])}")
                logging.info(f"    Funções: {', '.join(file_analysis['functions'])}")
                logging.info(f"    Classes: {', '.join(file_analysis['classes'])}")
                logging.info(f"    Variáveis globais: {', '.join(file_analysis['global_vars'])}")
        
        logging.info("Iniciando melhorias no projeto...")
        improve_project()
        create_requirements_file()
        final_project_setup()
        logging.info("Melhorias e configurações do projeto SICOMUV concluídas.")
    except Exception as e:
        logging.error(f"Erro durante a execução do script: {str(e)}")

if __name__ == "__main__":
    main()