import streamlit as st
import xml.etree.ElementTree as ET
import xml.dom.minidom as md

# Carregar o XML
def carregar_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return tree, root

# Edita o bloco <PD_RelFinalBase>
def editar_relatorio(rel_final):
    st.subheader("📝 Informações Gerais do Relatório Final")

    nomes_campos = {
        "CodProjeto": "Código do Projeto (ANEEL)",
        "ArquivoPDF": "Nome do Arquivo PDF",
        "DataIniODS": "Data de Início da ODS",
        "DataFimODS": "Data de Término da ODS",
        "ProdPrev": "Produto Previsto Alcançado?",
        "ProdJust": "Justificativa do Produto",
        "ProdEspTec": "Especificação Técnica do Produto",
        "TecPrev": "Técnica Prevista Implementada?",
        "TecJust": "Justificativa da Técnica",
        "TecDesc": "Descrição da Técnica Empregada",
        "AplicPrev": "Aplicabilidade Prevista Alcançada?",
        "AplicJust": "Justificativa da Aplicabilidade",
        "AplicFnc": "Resultados dos Testes de Funcionalidade",
        "AplicAbrang": "Abrangência da Aplicação",
        "AplicAmbito": "Âmbito de Aplicação",
        "TxDifTec": "Transferência ou Difusão Tecnológica"
    }

    campos_sn = {"ProdPrev", "TecPrev", "AplicPrev"}

    campos_limite_1000 = {
        "ProdJust", "ProdEspTec", "TecJust", "TecDesc",
        "AplicJust", "AplicFnc", "AplicAbrang", "AplicAmbito", "TxDifTec"
    }

    campos = {}
    for child in rel_final:
        label = nomes_campos.get(child.tag, child.tag)

        if child.tag in campos_sn:
            valor = st.selectbox(label, ["S", "N"], index=0 if (child.text or "S").upper() == "S" else 1, key=f"rel_{child.tag}")
        elif child.tag in campos_limite_1000:
            valor = st.text_area(label, child.text or "", height=100, key=f"rel_{child.tag}")
            num_chars = len(valor)
            if num_chars > 1000:
                st.warning(f"O campo '{label}' ultrapassou 1000 caracteres ({num_chars}). Será cortado.")
                valor = valor[:1000]
        else:
            valor = st.text_area(label, child.text or "", height=100, key=f"rel_{child.tag}")

        campos[child.tag] = valor

    return campos


#----------------------------------------------------------------------------------------------|
#----------------------------------COMEÇO CAMPOS PRINCIPAIS EXECUTORA--------------------------|
#----------------------------------------------------------------------------------------------|


#---------------------------------------------INICIO Funções de manipulaçao de membros----------------
def criar_membro(equipe):
    novo = ET.SubElement(equipe, "EquipeExec")
    campos = [
        "NomeMbEqExec", "BRMbEqExec", "DocMbEqExec", "TitulacaoMbEqExec",
        "FuncaoMbEqExec", "HhMbEqExec", "MesMbEqExec", "HoraMesMbEqExec"
    ]
    for tag in campos:
        ET.SubElement(novo, tag).text = ""
    return novo

nome_campos_membros = {
    "NomeMbEqExec": "Nome do Membro",
    "BRMbEqExec": "Nacionalidade Brasileira ?",
    "DocMbEqExec": "Documento (CPF ou Passaporte)",
    "TitulacaoMbEqExec": "Código Titulação",
    "FuncaoMbEqExec": "Código da Função",
    "HhMbEqExec": "valor da hora trabalhada",
    "MesMbEqExec": "Meses de Atuação",
    "HoraMesMbEqExec": "Horas por Mês",
}

def editar_membro(membro, indice):    
    dados = {}
    col1, col2 = st.columns(2)
    for i, campo in enumerate(membro):
        with (col1 if i % 2 == 0 else col2):
            nome_campos = nome_campos_membros.get(campo.tag, campo.tag)
            valor = st.text_input(nome_campos, campo.text or "", key=f"{campo.tag}_{indice}")
            dados[campo.tag] = valor
    return dados

def excluir_membro(equipe, membro):
    equipe.remove(membro)

#---------------------------------------------FIM Funções de manipulaçao de membros----------------

# Edita executora e membros dentro de <PD_EquipeExec>
def editar_executora_equipe(root, tree, xml_path):
    equipe_exec = root.find(".//PD_EquipeExec")
    if equipe_exec is None:
        st.error("A tag <PD_EquipeExec> não foi encontrada no XML.")
        return None, []

    executoras = equipe_exec.find("Executoras")
    if executoras is None:
        st.error("A tag <Executoras> não foi encontrada em <PD_EquipeExec>.")
        return None, []

    executora = executoras.find("Executora")

    if executora is not None:
        st.subheader("Editar Executora")

        cnpj = st.text_input("CNPJ da Executora", executora.findtext("CNPJExec", ""), key="cnpj_exec")
        razao = st.text_input("Razão Social", executora.findtext("RazaoSocialExec", ""), key="razao_exec")
        uf = st.text_input("UF", executora.findtext("UfExec", ""), key="uf_exec")

        executora.find("CNPJExec").text = cnpj
        executora.find("RazaoSocialExec").text = razao
        executora.find("UfExec").text = uf

        st.markdown("---")
        st.subheader("👥 Membros da Equipe Executora")

        equipe = executora.find("Equipe")
        if equipe is None:
            equipe = ET.SubElement(executora, "Equipe")

        membros_lista = equipe.findall("EquipeExec")
        nomes = [m.findtext("NomeMbEqExec") or f"Membro {i + 1}" for i, m in enumerate(membros_lista)]

        nome_novo = "➕ Novo Membro"
        selecionado = st.selectbox("Selecione um membro para editar ou adicionar", nomes + [nome_novo], key="select_membro")

        if selecionado == nome_novo:
            membro = criar_membro(equipe)
            membros_lista.append(membro)
            st.success("Novo membro criado. Preencha os dados abaixo.")
        else:
            indice = nomes.index(selecionado)
            membro = membros_lista[indice]

        dados_atualizados = editar_membro(membro, membros_lista.index(membro))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar alterações", key="btn_salvar"):
                for campo in membro:
                    campo.text = dados_atualizados.get(campo.tag, "")
                tree.write(xml_path, encoding="utf-8", xml_declaration=True)
                st.success("Alterações salvas.")
                st.rerun()

        with col2:
            if st.button("Excluir membro", key="btn_excluir"):
                excluir_membro(equipe, membro)
                tree.write(xml_path, encoding="utf-8", xml_declaration=True)
                st.success("Membro excluído.")
                st.rerun()

        membros_exec = [(membro, dados_atualizados)]
        return executora, membros_exec

    else:
        st.error("Nenhuma tag <Executora> foi encontrada.")
        return None, []
    
#----------------------------------------------------------------------------------------------
#----------------------------------FIM CAMPOS PRINCIPAIS EXECUTORA-----------------------------
#----------------------------------------------------------------------------------------------

# Edita o bloco <PD_Etapas>
# Função auxiliar: cria nova etapa
def criar_nova_etapa(pd_etapas, tree, xml_path):
    nova = ET.SubElement(pd_etapas, "Etapa")
    ET.SubElement(nova, "EtapaN").text = f"{len(pd_etapas.findall('Etapa')) + 1:02}"
    ET.SubElement(nova, "Atividades").text = ""
    ET.SubElement(nova, "MesExecEtapa").text = ""
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    st.rerun()

# Edita o bloco <PD_Etapas>
def editar_etapas(root, tree, xml_path):
    pd_etapas = root.find(".//PD_Etapas")
    if pd_etapas is None:
        st.error("A tag <PD_Etapas> não foi encontrada no XML.")
        return []

    etapas = pd_etapas.findall("Etapa")

    # Resumo das etapas
    with st.expander("📋 Resumo das Etapas", expanded=False):
        for i, etapa in enumerate(etapas):
            nome = etapa.findtext("EtapaN") or f"{i+1}"
            atividades = etapa.findtext("Atividades") or ""
            st.markdown(f"**Etapa {nome}**: {atividades[:80]}...")

    nomes_etapas = [f"Etapa {etapa.findtext('EtapaN') or i+1}" for i, etapa in enumerate(etapas)]
    selecionada = st.selectbox("Selecione uma etapa para editar", nomes_etapas + ["➕ Nova Etapa"], key="etapa_select")

    if selecionada == "➕ Nova Etapa":
        criar_nova_etapa(pd_etapas, tree, xml_path)

    indice = nomes_etapas.index(selecionada) if selecionada in nomes_etapas else len(etapas) - 1
    etapa = etapas[indice]

    st.markdown(f"### Dados de {selecionada}")
    campos = {}

    # Campo de número da etapa com tratamento de erro
    try:
        etapa_n_atual = int(etapa.findtext("EtapaN"))
    except (TypeError, ValueError):
        etapa_n_atual = indice + 1  

    nova_ordem = st.number_input("Número da Etapa (EtapaN)", min_value=1, value=etapa_n_atual, key=f"etapan_{indice}")
    etapa.find("EtapaN").text = f"{nova_ordem:02}"
    campos["EtapaN"] = f"{nova_ordem:02}"

    for campo in etapa:
        if campo.tag == "EtapaN":
            continue
        valor = st.text_area(f"{campo.tag} - {selecionada}", campo.text or "", height=80, key=f"{campo.tag}_{indice}")
        campos[campo.tag] = valor

    # Atualiza os textos
    for tag, valor in campos.items():
        campo = etapa.find(tag)
        if campo is not None:
            campo.text = valor

    if st.button(f"🗑️ Excluir {selecionada}", key=f"excluir_{indice}"):
        pd_etapas.remove(etapa)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.success(f"{selecionada} removida com sucesso!")
        st.rerun()

    return [(etapa, campos)]

def editar_recursos(root, tree, xml_path):
    pd_recursos = root.find(".//PD_Recursos")
    if pd_recursos is None:
        st.error("A tag <PD_Recursos> não foi encontrada no XML.")
        return []

    recurso_empresa = pd_recursos.find("RecursoEmpresa")
    if recurso_empresa is None:
        st.warning("Nenhuma <RecursoEmpresa> encontrada. Criando nova.")
        recurso_empresa = ET.SubElement(pd_recursos, "RecursoEmpresa")
        ET.SubElement(recurso_empresa, "CodEmpresa").text = ""
        ET.SubElement(recurso_empresa, "DestRecursos")
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.rerun()

    st.subheader("🏢 Empresa Financiadora")
    col1, col2 = st.columns(2)
    with col1:
        cod_empresa = st.text_input("Código da Empresa", recurso_empresa.findtext("CodEmpresa", ""), key="cod_empresa")
        recurso_empresa.find("CodEmpresa").text = cod_empresa

    dest_recursos = recurso_empresa.find("DestRecursos")
    if dest_recursos is None:
        dest_recursos = ET.SubElement(recurso_empresa, "DestRecursos")

    dest_exec = dest_recursos.find("DestRecursosExec")
    if dest_exec is None:
        dest_exec = ET.SubElement(dest_recursos, "DestRecursosExec")
        ET.SubElement(dest_exec, "CNPJExec").text = ""
        ET.SubElement(dest_exec, "CustoCatContabil")
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.rerun()

    with col2:
        cnpj_exec = st.text_input("CNPJ da Executora que recebeu o recurso", dest_exec.findtext("CNPJExec", ""), key="cnpj_dest")
        dest_exec.find("CNPJExec").text = cnpj_exec

    st.divider()
    st.subheader("📁 Seleção de Categoria Contábil")

    # Lista e mapeia categorias por código
    categorias = dest_exec.findall("CustoCatContabil")
    codigos_map = {}
    for i, grupo in enumerate(categorias):
        cod = grupo.findtext("CategoriaContabil") or f"sem_codigo_{i}"
        num_itens = len(grupo.findall("ItemDespesa"))
        resumo = f"{cod} - {num_itens} item{'s' if num_itens != 1 else ''}"
        codigos_map[cod] = {"grupo": grupo, "resumo": resumo}

    codigos_disponiveis = list(codigos_map.keys())

    # Inicializa ou mantém a categoria selecionada
    if "categoria_codigo" not in st.session_state:
        st.session_state["categoria_codigo"] = codigos_disponiveis[0] if codigos_disponiveis else None

    # Lista dos rótulos resumidos
    opcoes_resumo = [codigos_map[c]["resumo"] for c in codigos_disponiveis]
    indice_atual = codigos_disponiveis.index(st.session_state["categoria_codigo"]) if st.session_state["categoria_codigo"] in codigos_disponiveis else 0

    selecionado_resumo = st.selectbox(
        "Escolha a categoria para editar",
        opcoes_resumo + ["➕ Nova Categoria Contábil"],
        index=indice_atual
    )

    # Atualiza categoria selecionada
    if selecionado_resumo != "➕ Nova Categoria Contábil":
        # Extrai o código da categoria a partir do resumo
        codigo = selecionado_resumo.split(" - ")[0]
        st.session_state["categoria_codigo"] = codigo
    else:
        nova_cat = st.selectbox("Categoria:", ["ST", "MP", "MC", "VD", "OU"], key="nova_cat_codigo")
        if st.button("✅ Adicionar nova categoria"):
            nova = ET.SubElement(dest_exec, "CustoCatContabil")
            ET.SubElement(nova, "CategoriaContabil").text = nova_cat
            st.session_state["categoria_codigo"] = nova_cat
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            st.success("Nova categoria criada!")
            st.rerun()
        return

    # Grupo e código atual
    codigo = st.session_state["categoria_codigo"]
    grupo_selecionado = codigos_map[codigo]["grupo"]

    st.markdown(f"### ✏️ Editando categoria: **{codigo}**")

    if st.button(f"❌ Excluir categoria contábil '{codigo}'", key=f"excluir_categoria_{codigo}"):
        dest_exec.remove(grupo_selecionado)
        novo_codigos = [c for c in codigos_disponiveis if c != codigo]
        st.session_state["categoria_codigo"] = novo_codigos[0] if novo_codigos else None
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.success(f"Categoria '{codigo}' excluída com sucesso.")
        st.rerun()

    itens = grupo_selecionado.findall("ItemDespesa")
    for idx, item in enumerate(itens):
        with st.expander(f"🧾 Item de Despesa {idx+1}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                item.find("NomeItem").text = st.text_input("Nome do Item", item.findtext("NomeItem") or "", key=f"nome_{codigo}_{idx}")
                item.find("QtdeItem").text = st.text_input("Quantidade", item.findtext("QtdeItem") or "", key=f"qtde_{codigo}_{idx}")
                item.find("ValorIndItem").text = st.text_input("Valor Unitário", item.findtext("ValorIndItem") or "", key=f"valor_{codigo}_{idx}")
            with col2:
                item.find("TipoItem").text = st.text_input("Tipo", item.findtext("TipoItem") or "", key=f"tipo_{codigo}_{idx}")
                item.find("ItemLabE").text = st.text_input("ItemLabE", item.findtext("ItemLabE") or "", key=f"labe_{codigo}_{idx}")
                item.find("ItemLabN").text = st.text_input("ItemLabN", item.findtext("ItemLabN") or "", key=f"labn_{codigo}_{idx}")

            item.find("JustificaItem").text = st.text_area(
                "Justificativa", item.findtext("JustificaItem") or "", height=100, key=f"just_{codigo}_{idx}"
            )

            if st.button(f"❌ Remover Item {idx+1}", key=f"remover_item_{codigo}_{idx}"):
                grupo_selecionado.remove(item)
                tree.write(xml_path, encoding="utf-8", xml_declaration=True)
                st.success("Item removido com sucesso.")
                st.rerun()

    if st.button(f"➕ Adicionar novo item em {codigo}", key=f"add_item_{codigo}"):
        novo_item = ET.SubElement(grupo_selecionado, "ItemDespesa")
        for tag in ["NomeItem", "JustificaItem", "QtdeItem", "ValorIndItem", "TipoItem", "ItemLabE", "ItemLabN"]:
            ET.SubElement(novo_item, tag).text = ""
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.success("Novo item adicionado.")
        st.rerun()


# Salva o XML com formatação indentada
def salvar_edicoes(campos_base, rel_final, membros_exec, etapas_editadas, tree, xml_path):
    # Atualizar <PD_RelFinalBase>
    for tag, valor in campos_base.items():
        elem = rel_final.find(tag)
        if elem is not None:
            elem.text = valor

    # Atualizar membros da equipe executora
    for membro_xml, novos_valores in membros_exec:
        for tag, valor in novos_valores.items():
            campo = membro_xml.find(tag)
            if campo is not None:
                campo.text = valor

    # Atualizar etapas do projeto
    for etapa_xml, novos_valores in etapas_editadas:
        for tag, valor in novos_valores.items():
            campo = etapa_xml.find(tag)
            if campo is not None:
                campo.text = valor

    # Converter árvore para string e formatar com minidom
    root = tree.getroot()
    xml_str = ET.tostring(root, encoding="utf-8")
    dom = md.parseString(xml_str)

    # Salvar com indentação bonita
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(dom.toprettyxml(indent="  "))

    st.success("XML atualizado e formatado com sucesso!")
    

# Caminho do arquivo
xml_path = "08 - XML do Relatório Final de Projeto de PeD.xml"
tree, root = carregar_xml(xml_path)
rel_final = root.find("PD_RelFinalBase")


aba1, aba2, aba3, aba4, aba5 = st.tabs(["Relatório Final", "Executora e Equipe", "Etapas do Projeto","recursos", "download"])

with aba1:
    campos_base = editar_relatorio(rel_final)

with aba2:
    executora_xml, membros_exec = editar_executora_equipe(root, tree, xml_path)

with aba3:
    etapas_editadas = editar_etapas(root, tree, xml_path)

with aba4:
    recursos = editar_recursos(root, tree, xml_path)

with aba5:        
        try:
            with open(xml_path, "rb") as f:
                st.download_button(
                    label="Baixar XML Modificado",
                    data=f,
                    file_name="relatorio_modificado.xml",
                    mime="application/xml"
                )
        except FileNotFoundError:
            st.warning("Clique em 'Salvar' antes de baixar o arquivo.")


if st.button("Salvar Tudo", key="salvar_tudo"):
    salvar_edicoes(campos_base, rel_final, membros_exec, etapas_editadas, tree, xml_path)
