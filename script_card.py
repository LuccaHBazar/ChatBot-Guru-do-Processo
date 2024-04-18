import json
import os
import requests
from dotenv import load_dotenv
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters

logger = Logger()

load_dotenv()

# Constantes para pipe e phase names - pipefy
PIPE_NAME = 'Coleta de Documentação / Contato Advogado'
PHASE_NAME = 'Informações do Lead'

# cabecalho da requisicao HTTP
def get_headers():
  
    # busca parametro environment no arquivo .env
    if os.getenv('ENVIRONMENT') == 'development':
        #cria variavel
        secret_token = os.getenv('PIPEFY_TOKEN')
    else:
        # Busca o secret token na AWS Secrets Manager
        secret = json.loads(parameters.get_secret("secret_tokens"))
        secret_token = secret['pipefy_token']

    # retorna um cabecalho com token (chave/valor) - igual no insomnia
    return {
        'Authorization': f'Bearer {secret_token}',
        'Content-Type': 'application/json'
    }

# verifica se houve algum tipo de erro na resposta
def check_for_errors(response):
    if 'errors' in response:
        raise Exception(f"GraphQL Error: {response['errors']}")
    elif 'error' in response:
        raise Exception(f"Error: {response['error']}")

def obter_informacoes_card(card_id):

    # Query GraphQL para obter informações do card
    query = """
    query {
      card(id: %s) {
        fields {
          field {
            id
            label
          }
          value
        }
      }
    }
    """ % card_id

    # requisicao para o Graphql - (url, corpo da requisicao - query, cabecalho - autenticao no pipefy com tolken)
    response = requests.post('https://api.pipefy.com/graphql', json={'query': query}, headers=get_headers())

    if response.status_code == 200:
        # transforma a resposta em formato json
        card_data = response.json() 
        # print("passou por aqui")
        # print(card_data)
        return card_data
    else:
        print("Erro ao obter informações do card:", response.status_code)
        return None

# criacao do card no pipefy
def create_card(pipe_id, phase_id, nome, cpf, telefone, email):
    telefone_com_prefixo = "+55" + telefone

    # objeto graphql para criar card
    mutation = """
    mutation {
      createCard(input: {
        pipe_id: %s,
        phase_id: %s
        fields_attributes: [
          {field_id: "nome_do_lead", field_value: "%s"},
          {field_id: "cpf", field_value: "%s"},
          {field_id: "telefone", field_value: "%s"},
          {field_id: "e_mail_do_lead", field_value: "%s"}
        ]
      }) {
        card {
          id
          title
        }
      }
    }
    """ % (pipe_id, phase_id, nome, cpf, telefone_com_prefixo, email)

    # requisicao para o Graphql - (url, corpo da requisicao - mutation, cabecalho - autenticao no pipefy com tolken)
    response = requests.post('https://api.pipefy.com/graphql', json={'query': mutation}, headers=get_headers())
   
    # transforma a resposta em formato json
    response_json = response.json()

    # verifica se houve algum tipo de erro na resposta
    check_for_errors(response_json)

    return response_json
