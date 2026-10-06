from flask import Flask, jsonify, request
from flask_cors import CORS
import re
import unicodedata

app = Flask(__name__)
CORS(app)

AVISO_ASSISTENTE = (
    "Estas são orientações informativas gerais. O assistente não determina se houve crime "
    "e não substitui orientação jurídica ou policial profissional."
)

CATEGORIAS_ASSISTENTE = [
    {
        "nome": "Ameaça ou coerção",
        "palavras_chave": (
            "ameaca", "ameacou", "ameacando", "coercao", "chantagem",
            "exigiu dinheiro", "exigindo dinheiro", "sob ameaca"
        ),
        "perguntas": (
            "Há risco físico imediato ou a pessoa sabe onde você está?",
            "Estão exigindo dinheiro, imagens, senhas ou alguma ação?"
        ),
        "provas": "Preserve mensagens completas, áudios, e-mails, perfil, número, links, datas e exigências. Guarde os arquivos originais e protocolos.",
        "proximos_passos": "Priorize sua segurança e não confronte a pessoa se isso aumentar o risco. Não envie novos códigos, senhas ou conteúdo sob pressão. Procure a Polícia Civil para orientação; em perigo imediato, ligue 190."
    },
    {
        "nome": "Golpe ou fraude",
        "palavras_chave": (
            "golpe", "fraude", "pix", "transferi dinheiro", "transferencia",
            "pagamento suspeito", "compra falsa", "fui enganado", "fui enganada",
            "cartao clonado", "cobranca falsa"
        ),
        "perguntas": (
            "Você fez algum pagamento ou compartilhou dados?",
            "O contato aconteceu por ligação, mensagem, site ou rede social?"
        ),
        "provas": "Guarde conversas, links, perfil, e-mails, comprovantes, datas e protocolos. Não compartilhe números completos de cartão, senhas ou códigos.",
        "proximos_passos": "Interrompa o contato e não pague novas taxas. Se houve transação, contate imediatamente o banco ou meio de pagamento pelo canal oficial e peça orientação. Considere registrar ocorrência na Polícia Civil."
    },
    {
        "nome": "Invasão de conta",
        "palavras_chave": (
            "conta invadida", "minha conta foi invadida", "invadiram minha conta", "hackearam", "hackeada",
            "hackeado", "acesso nao autorizado", "perdi acesso", "senha alterada",
            "login desconhecido", "invadiram meu email", "invadiram meu e-mail"
        ),
        "perguntas": (
            "Você ainda consegue acessar a conta ou o e-mail de recuperação?",
            "Percebeu mensagens, alterações ou transações que não reconhece?"
        ),
        "provas": "Guarde alertas de login, e-mails de recuperação, registros de atividade, mensagens e protocolos de suporte. Nunca envie senhas ou códigos de autenticação.",
        "proximos_passos": "Use a recuperação oficial da plataforma. Em dispositivo confiável, troque a senha, encerre sessões desconhecidas, revise e-mail/telefone de recuperação e ative autenticação em dois fatores. Contate o banco se houver risco financeiro."
    },
    {
        "nome": "Cyberbullying",
        "palavras_chave": (
            "cyberbullying", "bullying online", "humilhacao online",
            "humilhado na internet", "humilhada na internet", "ataques online",
            "ofensas repetidas"
        ),
        "perguntas": (
            "As ofensas ou publicações aconteceram repetidamente?",
            "Isso ocorre em rede social, jogo, grupo, escola ou trabalho?"
        ),
        "provas": "Registre capturas de tela com contexto, links, nomes de perfil, datas, frequência e protocolos de denúncia. Preserve os arquivos originais.",
        "proximos_passos": "Denuncie o conteúdo à plataforma e ajuste as opções de privacidade. Se envolver escola ou trabalho, procure o canal responsável. Se houver ameaça, exposição de dados ou risco presencial, procure a Polícia Civil; para menores, envolva um adulto de confiança."
    },
    {
        "nome": "Exposição ou divulgação de imagens/dados",
        "palavras_chave": (
            "divulgaram minhas fotos", "divulgaram minhas imagens",
            "imagem intima", "fotos intimas", "vazaram minhas fotos",
            "exposicao de dados", "dados expostos", "dados vazados",
            "vazamento de dados", "publicaram meu endereco",
            "publicaram meus dados", "doxxing", "sem meu consentimento"
        ),
        "perguntas": (
            "O conteúdo está publicado em algum perfil, site ou grupo que você consegue identificar?",
            "O conteúdo envolve uma criança ou adolescente, ou há ameaça para divulgar mais?"
        ),
        "provas": "Anote URLs, perfis, datas, mensagens e protocolos. Preserve capturas de tela sem redistribuir o conteúdo íntimo. Se envolver menores, não baixe nem encaminhe imagens.",
        "proximos_passos": "Denuncie o conteúdo à plataforma e solicite remoção. Proteja suas contas e procure a Polícia Civil para orientação. Se envolver criança/adolescente, procure o Conselho Tutelar ou Disque 100; em perigo imediato, ligue 190."
    },
    {
        "nome": "Perseguição ou assédio digital",
        "palavras_chave": (
            "perseguicao", "perseguindo", "perseguida", "perseguido", "me perseguem", "stalking", "assediando",
            "assedio online", "nao para de me procurar", "contato insistente",
            "me segue online", "perfis diferentes me contatam"
        ),
        "perguntas": (
            "O contato é repetido ou está aumentando?",
            "A pessoa ameaçou aparecer, sabe sua localização ou tentou contato presencial?"
        ),
        "provas": "Registre datas e frequência, mensagens, URLs, perfis, números, tentativas de contato e protocolos. Guarde capturas com contexto antes de bloquear, se for seguro.",
        "proximos_passos": "Avise alguém de confiança, revise privacidade e localização, denuncie à plataforma e bloqueie quando for seguro. Procure a Polícia Civil se houver perseguição contínua ou ameaça; em perigo imediato, ligue 190."
    },
    {
        "nome": "Perfil falso",
        "palavras_chave": (
            "perfil falso", "conta falsa", "se passando por mim",
            "finge ser eu", "usaram minha foto", "impersonacao",
            "roubaram minha identidade", "perfil fingindo ser eu"
        ),
        "perguntas": (
            "O perfil está usando seu nome, foto ou dados?",
            "Alguém recebeu pedidos de dinheiro ou informações feitos em seu nome?"
        ),
        "provas": "Guarde o link e nome do perfil, capturas de tela, mensagens, datas, relatos de contatos e protocolos da plataforma.",
        "proximos_passos": "Denuncie o perfil por falsidade/impersonação na própria plataforma e avise pessoas próximas por outro canal. Se houve fraude ou uso de documentos, procure a Polícia Civil e as instituições afetadas."
    },
    {
        "nome": "Privacidade ou dados pessoais",
        "palavras_chave": (
            "privacidade", "dados pessoais", "usaram meus dados",
            "coletaram meus dados", "compartilharam meus dados",
            "meus dados", "lgpd", "anpd"
        ),
        "perguntas": (
            "Quais tipos de dados parecem estar envolvidos, sem informar os valores ou números completos?",
            "Você sabe qual organização ou serviço pode ter usado ou exposto esses dados?"
        ),
        "provas": "Guarde avisos, mensagens, URLs, datas e protocolos da organização. Não publique documentos, números completos ou outros dados pessoais.",
        "proximos_passos": "Proteja contas relacionadas, troque senhas que possam ter sido expostas e confirme informações diretamente com a organização por canal oficial. Para questões de proteção de dados, consulte os canais oficiais da ANPD; se houver fraude, procure também o banco e a Polícia Civil."
    },
    {
        "nome": "Emergência ou risco imediato",
        "palavras_chave": (),
        "perguntas": (
            "Você está em um local seguro neste momento?",
            "Há alguém de confiança que possa ficar com você ou ajudar a chegar a um local seguro?"
        ),
        "provas": "Não se coloque em risco para coletar provas. Preserve mensagens, links, nomes de perfil e horários somente quando estiver em segurança.",
        "proximos_passos": "Se houver perigo físico imediato, afaste-se do risco se puder e procure o serviço de emergência adequado. No Brasil, ligue 190 para a Polícia Militar; em emergência médica, ligue 192 para o SAMU. Depois, quando estiver em segurança, procure a Polícia Civil ou um serviço especializado."
    }
]


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(caractere for caractere in texto if unicodedata.category(caractere) != "Mn")


def responder_assistente(mensagem):
    texto = normalizar_texto(mensagem)
    texto_curto = re.sub(r"[.!?,;:]+$", "", texto).strip()

    if re.fullmatch(r"(oi|ola|ola tudo bem|bom dia|boa tarde|boa noite|e ai)", texto_curto):
        return (
            "Olá! Sou o assistente local do Protege Digital. Posso ajudar com ameaça ou chantagem, "
            "golpe/fraude/Pix, invasão de conta, cyberbullying, exposição de imagens ou dados, "
            "perseguição/assédio digital, perfil falso, privacidade e situações de emergência. "
            "O que aconteceu, em termos gerais? Não envie senhas, códigos ou dados bancários."
        )

    if re.fullmatch(r"(obrigado|obrigada|muito obrigado|muito obrigada|valeu)", texto_curto):
        return (
            "Por nada. Se precisar, posso ajudar a organizar os próximos passos. "
            "Não compartilhe senhas, códigos de autenticação ou dados bancários."
        )

    if re.search(r"\b(como (guardar|preservar|salvar) (as )?provas|guardar provas|preservar provas)\b", texto):
        return (
            "Para preservar evidências:\n"
            "- Guarde capturas de tela com contexto, conversas completas, links/URLs, e-mails e nomes de perfil.\n"
            "- Anote datas, horários e protocolos de atendimento.\n"
            "- Preserve os arquivos originais e evite editar, apagar ou redistribuir o material.\n"
            "- Guarde cópias em local seguro, sem incluir senhas, códigos ou dados bancários completos.\n"
            "Se envolver imagens íntimas de criança ou adolescente, não baixe nem encaminhe o conteúdo; "
            "procure imediatamente a Polícia Civil, o Conselho Tutelar ou o Disque 100. "
            + AVISO_ASSISTENTE
        )

    if re.search(r"\b(devo bloquear|posso bloquear|devo bloquear a pessoa|bloqueio a pessoa)\b", texto):
        return (
            "Bloquear pode ajudar a interromper o contato, mas, se for seguro, preserve antes mensagens, "
            "links, perfil e datas, e denuncie o conteúdo na plataforma. Se o bloqueio puder aumentar o risco "
            "ou houver ameaça presencial, priorize sua segurança e procure apoio de alguém de confiança ou "
            "da Polícia Civil. Em perigo físico imediato, ligue 190. " + AVISO_ASSISTENTE
        )

    risco_negado = re.search(
        r"\b(nao estou em perigo|nao ha perigo|nao existe perigo|sem risco imediato|nao e risco imediato)\b",
        texto
    )
    padroes_emergencia = (
        r"\b(perigo fisico imediato|risco fisico imediato|risco imediato|perigo imediato|"
        r"emergencia|em perigo agora|esta vindo atras de mim|esta aqui agora|"
        r"ameaca de morte|vai me machucar agora|emergencia medica)\b"
    )
    if not risco_negado and re.search(padroes_emergencia, texto):
        categoria = next(
            item for item in CATEGORIAS_ASSISTENTE
            if item["nome"] == "Emergência ou risco imediato"
        )
        return _formatar_resposta_categoria(categoria)

    padroes_invasao_conta = (
        "invadiram minha conta",
        "invadiram meu instagram",
        "invadiram meu whatsapp",
        "conta invadida",
        "conta hackeada",
        "hackearam minha conta",
        "hackearam meu instagram",
        "roubaram minha conta",
        "mudaram minha senha",
        "mudaram a minha senha",
        "trocaram minha senha",
        "trocaram a minha senha",
        "nao consigo entrar na minha conta",
        "nao consigo acessar minha conta",
        "perderam o acesso a minha conta",
        "perderam acesso a minha conta",
        "perdi o acesso a minha conta",
        "perdi acesso a minha conta"
    )
    categoria_invasao = next(
        item for item in CATEGORIAS_ASSISTENTE
        if item["nome"] == "Invasão de conta"
    )
    if any(normalizar_texto(padrao) in texto for padrao in padroes_invasao_conta):
        return _formatar_resposta_categoria(categoria_invasao)

    if re.search(r"\b(outro problema|outro caso|outro assunto)\b", texto):
        categoria = None
    else:
        categoria = next(
            (
                item for item in CATEGORIAS_ASSISTENTE
                if item["palavras_chave"]
                and any(normalizar_texto(palavra) in texto for palavra in item["palavras_chave"])
            ),
            None
        )

    if categoria is None:
        return (
            "Posso ajudar com ameaça/chantagem, golpe/fraude/Pix, invasão de conta, cyberbullying, "
            "exposição de imagens ou dados, perseguição/assédio digital, perfil falso, privacidade "
            "e risco imediato.\n\n"
            "Qual dessas situações se aproxima mais do que aconteceu? Conte apenas o necessário; "
            "não envie senhas, códigos de autenticação, dados bancários ou imagens íntimas.\n\n"
            "Enquanto isso, preserve mensagens, links, datas e protocolos sem alterar os arquivos originais. "
            + AVISO_ASSISTENTE
        )

    return _formatar_resposta_categoria(categoria)


def _formatar_resposta_categoria(categoria):
    perguntas = "\n".join("- " + pergunta for pergunta in categoria["perguntas"])
    return (
        "Entendi que sua situação pode estar relacionada a: " + categoria["nome"] + ".\n\n"
        "Para entender melhor:\n" + perguntas + "\n\n"
        "Preservação de evidências: " + categoria["provas"] + "\n\n"
        "Próximos passos: " + categoria["proximos_passos"] + "\n\n"
        + AVISO_ASSISTENTE
    )


@app.route("/")
def inicio():
    return jsonify({
        "app": "Protege Digital",
        "status": "online",
        "mensagem": "Backend funcionando!"
    })


@app.route("/api/triagem", methods=["POST"])
def triagem():
    dados = request.get_json() or {}

    crime = dados.get("crime", "").lower()

    orientacoes = {
        "invasão de conta": {
            "categoria": "Invasão de contas ou dispositivos",
            "orientacao": "Troque a senha, ative a autenticação em dois fatores e preserve os registros de acesso."
        },
        "ameaça": {
            "categoria": "Ameaça",
            "orientacao": "Preserve mensagens, áudios, imagens e demais provas. Em situação de risco imediato, procure o serviço de emergência."
        },
        "cyberbullying": {
            "categoria": "Perseguição e cyberbullying",
            "orientacao": "Não apague as mensagens. Faça registros das ocorrências e utilize os canais oficiais da plataforma."
        },
        "vazamento de dados": {
            "categoria": "Vazamento de dados",
            "orientacao": "Confirme o incidente com a organização responsável, proteja as contas afetadas e preserve comunicados e URLs."
        },
        "extorsão digital": {
            "categoria": "Extorsão digital",
            "orientacao": "Não envie dinheiro ou novos dados ao autor. Preserve as conversas, comprovantes e demais evidências."
        }
    }

    resultado = orientacoes.get(crime)

    if not resultado:
        resultado = {
            "categoria": "Situação não identificada",
            "orientacao": "Preserve as evidências e procure orientação adequada para analisar o caso."
        }

    return jsonify(resultado)


@app.route("/api/assistente", methods=["POST"])
def assistente():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "resposta": "Envie uma mensagem em JSON no formato {\"mensagem\": \"...\"}."
        }), 400

    mensagem = dados.get("mensagem")

    if not isinstance(mensagem, str) or not mensagem.strip():
        return jsonify({
            "resposta": "Digite uma mensagem para que eu possa ajudar."
        }), 400

    return jsonify({
        "resposta": responder_assistente(mensagem.strip())
    })


if __name__ == "__main__":
    app.run(debug=True)