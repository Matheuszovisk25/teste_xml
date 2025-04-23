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
    st.subheader("PD_RelFinalBase")
    campos = {}
    for child in rel_final:
        campos[child.tag] = st.text_area(child.tag, child.text or "", height=100, key=f"rel_{child.tag}")
    return campos

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

    executora = None
    for ex in executoras.findall("Executora"):
        if (
            ex.findtext("CNPJExec") == "Número"
            and ex.findtext("RazaoSocialExec") == "Texto"
            and ex.findtext("UfExec") == "UF"
        ):
            executora = ex
            break

    if executora is None:
        executora = executoras.find("Executora")

    if executora is not None:
        st.subheader("🏛️ Editar Executora")

        # Editar campos principais
        cnpj = st.text_input("CNPJ da Executora", executora.findtext("CNPJExec", ""), key="cnpj_exec")
        razao = st.text_input("Razão Social", executora.findtext("RazaoSocialExec", ""), key="razao_exec")
        uf = st.text_input("UF", executora.findtext("UfExec", ""), key="uf_exec")

        executora.find("CNPJExec").text = cnpj
        executora.find("RazaoSocialExec").text = razao
        executora.find("UfExec").text = uf

        # Membros da equipe
        equipe = executora.find("Equipe")
        if equipe is None:
            equipe = ET.SubElement(executora, "Equipe")

        st.markdown("---")
        st.subheader("👥 Membros da Equipe Executora")

        membros_lista = equipe.findall("EquipeExec")
        nomes = [m.findtext("NomeMbEqExec") or f"Membro {i + 1}" for i, m in enumerate(membros_lista)]

        NOME_NOVO = "➕ Novo Membro"
        selecionado = st.selectbox("Selecione um membro para editar", nomes + [NOME_NOVO], key="select_membro")

        # Adicionar novo membro se selecionado
        if selecionado == NOME_NOVO:
            novo = ET.SubElement(equipe, "EquipeExec")
            for tag in [
                "NomeMbEqExec", "BRMbEqExec", "DocMbEqExec", "TitulacaoMbEqExec",
                "FuncaoMbEqExec", "HhMbEqExec", "MesMbEqExec", "HoraMesMbEqExec"
            ]:
                ET.SubElement(novo, tag).text = ""
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            st.rerun()

        # Atualizar dados do membro selecionado
        indice = nomes.index(selecionado) if selecionado in nomes else len(membros_lista) - 1
        membro = membros_lista[indice]

        st.markdown(f"### ✏️ Dados de {selecionado}")
        dados = {}
        for campo in membro:
            valor = st.text_input(f"{campo.tag} - {selecionado}", campo.text or "", key=f"{campo.tag}_{indice}")
            dados[campo.tag] = valor

        membros_exec = [(membro, dados)]
        return executora, membros_exec

    else:
        st.error("❌ Nenhuma tag <Executora> foi encontrada.")
        return None, []

    

# Edita o bloco <PD_Etapas>
def editar_etapas(root, tree, xml_path):
    pd_etapas = root.find(".//PD_Etapas")
    if pd_etapas is None:
        st.error("A tag <PD_Etapas> não foi encontrada no XML.")
        return []

    etapas = pd_etapas.findall("Etapa")
    nomes_etapas = [
        f"Etapa {etapa.findtext('EtapaN') or i+1}" 
        for i, etapa in enumerate(etapas)
    ]

    selecionada = st.selectbox("Selecione uma etapa para editar", nomes_etapas + ["Nova Etapa"], key="etapa_select")

    if selecionada == "Nova Etapa":
        nova = ET.SubElement(pd_etapas, "Etapa")
        ET.SubElement(nova, "EtapaN").text = f"{len(etapas)+1:02}"
        ET.SubElement(nova, "Atividades").text = ""
        ET.SubElement(nova, "MesExecEtapa").text = ""
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.rerun()

    indice = nomes_etapas.index(selecionada) if selecionada in nomes_etapas else len(etapas) - 1
    etapa = etapas[indice]

    st.markdown(f"### Dados de {selecionada}")
    campos = {}
    for campo in etapa:
        valor = st.text_area(f"{campo.tag} - {selecionada}", campo.text or "", height=80, key=f"{campo.tag}_{indice}")
        campos[campo.tag] = valor

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

    # Empresa financiadora
    cod_empresa = st.text_input("Código da Empresa", recurso_empresa.findtext("CodEmpresa", ""), key="cod_empresa")
    recurso_empresa.find("CodEmpresa").text = cod_empresa

    # Execução dos recursos
    dest_recursos = recurso_empresa.find("DestRecursos")
    dest_exec = dest_recursos.find("DestRecursosExec")
    if dest_exec is None:
        dest_exec = ET.SubElement(dest_recursos, "DestRecursosExec")
        ET.SubElement(dest_exec, "CNPJExec").text = ""
        ET.SubElement(dest_exec, "CustoCatContabil")
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.rerun()

    cnpj_exec = st.text_input("CNPJ da Executora que recebeu o recurso", dest_exec.findtext("CNPJExec", ""), key="cnpj_dest")
    dest_exec.find("CNPJExec").text = cnpj_exec

    # Agrupar categorias contábeis
    categorias = dest_exec.findall("CustoCatContabil")
    categorias_map = {}

    for cat in categorias:
        cod = cat.findtext("CategoriaContabil", "")
        if cod in ("Código", "", None):
            cod = "ST"
            cat.find("CategoriaContabil").text = "ST"

        if cod not in categorias_map:
            categorias_map[cod] = []
        categorias_map[cod].append(cat)

    # Mostrar cada grupo de categoria contábil
    for cod_cat, grupos in categorias_map.items():
        for grupo_id, grupo in enumerate(grupos):
            with st.expander(f"Categoria Contábil: {cod_cat} #{grupo_id+1}", expanded=False):
                itens = grupo.findall("ItemDespesa")
                for idx, item in enumerate(itens):
                    st.markdown(f"**Item de Despesa {idx+1}**")
                    for campo in item:
                        item.find(campo.tag).text = st.text_area(
                            f"{campo.tag} ({cod_cat} - Item {idx+1})",
                            item.findtext(campo.tag) or "",
                            height=80,
                            key=f"{campo.tag}_{cod_cat}_{grupo_id}_{idx}"
                        )
                    st.markdown("---")

                # Adicionar novo item nessa categoria
                if st.button(f"Adicionar novo item em {cod_cat} #{grupo_id+1}", key=f"add_{cod_cat}_{grupo_id}"):
                    novo_item = ET.SubElement(grupo, "ItemDespesa")
                    for tag in ["NomeItem", "JustificaItem", "QtdeItem", "ValorIndItem", "TipoItem", "ItemLabE", "ItemLabN"]:
                        ET.SubElement(novo_item, tag).text = ""
                    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
                    st.rerun()

    # -------------------------
    # Criar nova categoria contábil
    # -------------------------
    st.markdown("## Criar nova Categoria Contábil")
    nova_cat = st.selectbox(
        "Escolha a categoria contábil para adicionar", 
        ["ST", "MC", "MP", "VD", "OU"], 
        key=f"nova_categoria_{len(categorias_map)}"
    )

    if st.button("➕ Adicionar nova categoria contábil", key="btn_add_categoria"):
        nova = ET.SubElement(dest_exec, "CustoCatContabil")
        ET.SubElement(nova, "CategoriaContabil").text = nova_cat
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.success(f"Categoria '{nova_cat}' adicionada!")
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
