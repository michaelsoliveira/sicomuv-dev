import os
import subprocess
import sys

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    output, error = process.communicate()
    return process.returncode, output, error

def create_file(filename, content=""):
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Criado arquivo: {filename}")

def confirm(question):
    return input(f"{question} (s/n): ").lower().strip() == 's'

def main():
    # Criar arquivos mínimos
    create_file('README.md', "# SICOMUV\n\nSistema de Comunicação Universal por Voz")
    create_file('SICOMUV.code-workspace', '{"folders": [{"path": "."}]}')
    create_file('main.py', "# Código principal do SICOMUV\n\nprint('Hello, SICOMUV!')")
    os.makedirs('tests', exist_ok=True)
    create_file('tests/__init__.py')

    # Adicionar new_venv ao .gitignore
    with open('.gitignore', 'a') as f:
        f.write('\nnew_venv/')
    print("Adicionado new_venv/ ao .gitignore")

    # Inicializar repositório Git se não existir
    if not os.path.exists('.git'):
        run_command('git init')
        print("Repositório Git inicializado")

    # Adicionar todos os arquivos
    run_command('git add .')
    print("Todos os arquivos adicionados ao stage")

    # Verificar o status do repositório
    code, output, error = run_command('git status')
    print("Status do Git:")
    print(output)

    # Commit das alterações
    if confirm("Deseja fazer o commit das alterações?"):
        code, output, error = run_command('git commit -m "Inicialização do projeto SICOMUV"')
        if code == 0:
            print("Commit realizado com sucesso")
        else:
            print(f"Erro ao realizar commit: {error}")
            return
    else:
        print("Commit cancelado")
        return

    # Criar e mudar para a branch 'teste'
    if confirm("Deseja criar e mudar para a branch 'teste'?"):
        code, output, error = run_command('git checkout -b teste')
        if code == 0:
            print("Branch 'teste' criada e ativada")
        else:
            print(f"Erro ao criar branch 'teste': {error}")
            return
    else:
        print("Operação cancelada")
        return

    # Configurar o remote (se necessário)
    code, output, error = run_command('git remote -v')
    if 'origin' not in output:
        remote_url = "https://github.com/michaelsoliveira/sicomuv-dev.git"
        if confirm(f"Deseja adicionar o remote 'origin' com a URL {remote_url}?"):
            run_command(f'git remote add origin {remote_url}')
            print(f"Remote 'origin' adicionado: {remote_url}")
        else:
            print("Adição do remote cancelada")
            return

    # Push para o GitHub
    if confirm("Deseja fazer push para o GitHub?"):
        code, output, error = run_command('git push -u origin teste')
        if code == 0:
            print("Push realizado com sucesso")
        else:
            print(f"Erro ao realizar push: {error}")
            if confirm("Deseja tentar um push forçado?"):
                code, output, error = run_command('git push -u origin teste --force')
                if code == 0:
                    print("Push forçado realizado com sucesso")
                else:
                    print(f"Erro ao realizar push forçado: {error}")
                    print("Verifique suas configurações do Git e do GitHub e tente novamente.")
            else:
                print("Push cancelado")
    else:
        print("Push cancelado")

if __name__ == "__main__":
    main()