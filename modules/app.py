

    card("assets/icon_extrator.svg","EXTRATOR DE IMAGENS CSV",
         "Baixe imagens diretamente de URLs listadas em um arquivo CSV.",
         "Abrir Extrator CSV","extrator")

    card("assets/icon_removedor.svg","REMOVEDOR DE FUNDO",
         "Remova fundos em lote com preview antes/depois e PNG de alta qualidade.",
         "Abrir Removedor de Fundo","removedor")

elif route == "conversor":
    from modules.conversor_imagem import render
    render(ping_b64="")
elif route == "extrator":
    from modules.extrair_imagens_csv import render
    render(ping_b64="")
elif route == "removedor":
    from modules.removedor_fundo import render
    render(ping_b64="")
