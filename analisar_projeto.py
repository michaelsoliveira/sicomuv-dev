import os
import re
from collections import Counter

def analyze_file_content(file_path):
    """Analisa o conteúdo de um arquivo e extrai informações relevantes."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Extrai comentários e docstrings
        comments = re.findall(r'#.*$|"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', content, re.MULTILINE)
        
        # Identifica imports
        imports = re.findall(r'^import .*|^from .* import .*', content, re.MULTILINE)
        
        # Identifica definições de funções e classes
        functions = re.findall(r'def \w+$$.*$$:', content)
        classes = re.findall(r'class \w+.*:', content)
        
        return {
            'comments': comments[:5],  # Limita a 5 comentários
            'imports': imports,
            'functions': functions,
            'classes': classes
        }
    except Exception as e:
        return f"Erro ao ler {file_path}: {str(e)}"

def analyze_project(project_path):
    """Analisa o projeto e gera um resumo."""
    summary = f"Análise do Projeto: {project_path}\n\n"
    file_types = Counter()
    important_files = []
    
    for root, dirs, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_type = os.path.splitext(file)[1]
            file_types[file_type] += 1
            
            if file_type in ['.py', '.js', '.html', '.css']:
                important_files.append(file_path)
    
    summary += "Estrutura do Projeto:\n"
    summary += f"Total de arquivos: {sum(file_types.values())}\n"
    summary += "Tipos de arquivos:\n"
    for file_type, count in file_types.most_common():
        summary += f"  {file_type}: {count}\n"
    
    summary += "\nArquivos Importantes:\n"
    for file_path in important_files[:10]:  # Limita a 10 arquivos importantes
        summary += f"\n{file_path}:\n"
        analysis = analyze_file_content(file_path)
        if isinstance(analysis, str):
            summary += f"  {analysis}\n"
        else:
            summary += f"  Imports: {', '.join(analysis['imports'][:5])}\n"
            summary += f"  Funções: {', '.join(func.split('(')[0] for func in analysis['functions'][:5])}\n"
            summary += f"  Classes: {', '.join(cls.split('(')[0] for cls in analysis['classes'][:5])}\n"
            if analysis['comments']:
                summary += f"  Comentário relevante: {analysis['comments'][0][:100]}...\n"
    
    return summary

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.join(script_dir, "SICOMUV_Clone")

    if not os.path.exists(project_path):
        print(f"O diretório do projeto {project_path} não existe.")
        exit(1)

    print("Iniciando análise do projeto...")
    summary = analyze_project(project_path)
    summary_file = os.path.join(script_dir, "projeto_resumo.txt")

    print(f"Salvando o resumo em {summary_file}...")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"Análise concluída. O resumo foi salvo em {summary_file}")