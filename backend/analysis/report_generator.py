"""
Report Generator Module
=======================

Módulo para geração de relatórios em múltiplos formatos (Markdown, HTML, PDF, DOCX)

Migrado de: actions/utils/report_generator.py
Autor: Projeto YARA - IFAM
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ReportGenerator:
    """
    Gerador de relatórios bioinformáticos
    """
    
    def __init__(self, project_name: str = "Análise QIIME 2"):
        """
        Inicializa gerador
        
        Args:
            project_name: Nome do projeto
        """
        self.project_name = project_name
        self.sections: List[Dict] = []
        self.images: List[Dict] = []
        self.tables: List[Dict] = []
        
    def add_section(self, title: str, content: str, level: int = 2):
        """
        Adiciona seção ao relatório
        
        Args:
            title: Título da seção
            content: Conteúdo em Markdown
            level: Nível do cabeçalho (1-6)
        """
        self.sections.append({
            'title': title,
            'content': content,
            'level': level
        })
    
    def add_image(self, image_path: str, caption: str = "", width: Optional[int] = None):
        """
        Adiciona imagem ao relatório
        
        Args:
            image_path: Caminho para imagem
            caption: Legenda da imagem
            width: Largura em pixels (opcional)
        """
        self.images.append({
            'path': image_path,
            'caption': caption,
            'width': width
        })
    
    def add_table(self, df: pd.DataFrame, caption: str = ""):
        """
        Adiciona tabela ao relatório
        
        Args:
            df: DataFrame
            caption: Legenda da tabela
        """
        self.tables.append({
            'data': df,
            'caption': caption
        })
    
    def generate_markdown(self, output_path: str = "relatorio.md") -> str:
        """
        Gera relatório em Markdown
        
        Args:
            output_path: Caminho para salvar
            
        Returns:
            Caminho do arquivo gerado
        """
        md_content = []
        
        # Cabeçalho
        md_content.append(f"# {self.project_name}\n")
        md_content.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        md_content.append(f"**Gerado por:** YARA - Your Assistant for Results Analysis\n")
        md_content.append("\n---\n\n")
        
        # Seções
        for section in self.sections:
            level_marker = '#' * section['level']
            md_content.append(f"{level_marker} {section['title']}\n\n")
            md_content.append(f"{section['content']}\n\n")
        
        # Imagens
        if self.images:
            md_content.append("## Visualizações\n\n")
            for img in self.images:
                if img['caption']:
                    md_content.append(f"### {img['caption']}\n\n")
                md_content.append(f"![{img['caption']}]({img['path']})\n\n")
        
        # Tabelas
        if self.tables:
            md_content.append("## Tabelas\n\n")
            for table in self.tables:
                if table['caption']:
                    md_content.append(f"### {table['caption']}\n\n")
                md_content.append(table['data'].to_markdown())
                md_content.append("\n\n")
        
        # Rodapé
        md_content.append("\n---\n\n")
        md_content.append("*Relatório gerado automaticamente pelo YARA*\n")
        md_content.append("*Projeto IFAM - EMBRAPA - INPA*\n")
        
        # Salvar
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(md_content))
        
        return output_path
    
    def generate_html(self, output_path: str = "relatorio.html") -> str:
        """
        Gera relatório em HTML
        
        Args:
            output_path: Caminho para salvar
            
        Returns:
            Caminho do arquivo gerado
        """
        html_content = []
        
        # HTML Header
        html_content.append("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #7C3AED;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #7C3AED;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #7C3AED;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{}</h1>
        <div class="metadata">
            <strong>Data:</strong> {}<br>
            <strong>Gerado por:</strong> YARA - Your Assistant for Results Analysis
        </div>
""".format(self.project_name, self.project_name, datetime.now().strftime('%d/%m/%Y %H:%M')))
        
        # Seções
        for section in self.sections:
            tag = f"h{section['level']}"
            html_content.append(f"        <{tag}>{section['title']}</{tag}>\n")
            
            # Converter Markdown básico para HTML
            content_html = section['content'].replace('\n\n', '</p><p>')
            content_html = f"<p>{content_html}</p>"
            
            html_content.append(f"        {content_html}\n")
        
        # Imagens
        if self.images:
            html_content.append("        <h2>Visualizações</h2>\n")
            for img in self.images:
                html_content.append(f"        <div>\n")
                if img['caption']:
                    html_content.append(f"            <h3>{img['caption']}</h3>\n")
                
                width_attr = f' width="{img["width"]}"' if img['width'] else ''
                html_content.append(f'            <img src="{img["path"]}"{width_attr} alt="{img["caption"]}">\n')
                html_content.append(f"        </div>\n")
        
        # Tabelas
        if self.tables:
            html_content.append("        <h2>Tabelas</h2>\n")
            for table in self.tables:
                if table['caption']:
                    html_content.append(f"        <h3>{table['caption']}</h3>\n")
                html_content.append(table['data'].to_html(index=True, classes='data-table'))
                html_content.append("\n")
        
        # Rodapé
        html_content.append("""
        <div class="footer">
            <p><em>Relatório gerado automaticamente pelo YARA</em></p>
            <p>Projeto IFAM - EMBRAPA - INPA</p>
        </div>
    </div>
</body>
</html>
""")
        
        # Salvar
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(html_content))
        
        return output_path
    
    def clear(self):
        """Limpa conteúdo do relatório"""
        self.sections = []
        self.images = []
        self.tables = []


def create_alpha_diversity_report(stats: Dict, output_format: str = "markdown") -> str:
    """
    Cria relatório de diversidade alfa
    
    Args:
        stats: Dicionário com estatísticas
        output_format: Formato de saída ('markdown' ou 'html')
        
    Returns:
        Caminho do arquivo gerado
    """
    report = ReportGenerator("Relatório de Diversidade Alfa")
    
    # Introdução
    intro = """Este relatório apresenta a análise de diversidade alfa das amostras metagenômicas.
A diversidade alfa mede a riqueza e equitabilidade de espécies dentro de cada amostra individual."""
    
    report.add_section("Introdução", intro, level=2)
    
    # Resultados
    if 'mean' in stats:
        results = f"""
**Estatísticas Gerais:**

- Média: {stats['mean']:.2f}
- Mediana: {stats['median']:.2f}
- Desvio Padrão: {stats['std']:.2f}
- Mínimo: {stats['min']:.2f}
- Máximo: {stats['max']:.2f}
"""
        report.add_section("Resultados", results, level=2)
    
    # Interpretação
    interpretation = """
**Interpretação:**

Os valores de diversidade alfa indicam a complexidade das comunidades microbianas em cada amostra.
Valores mais altos geralmente indicam comunidades mais diversas e equilibradas.
"""
    report.add_section("Interpretação", interpretation, level=2)
    
    # Gerar relatório
    if output_format == "html":
        return report.generate_html("data/qiime2/relatorio_alpha.html")
    else:
        return report.generate_markdown("data/qiime2/relatorio_alpha.md")


def create_comprehensive_report(analyses: Dict, output_format: str = "markdown") -> str:
    """
    Cria relatório abrangente com múltiplas análises
    
    Args:
        analyses: Dicionário com resultados de análises
                 Chaves: 'alpha', 'beta', 'taxonomy', 'rarefaction'
        output_format: Formato de saída
        
    Returns:
        Caminho do arquivo gerado
    """
    report = ReportGenerator("Relatório Completo de Análise Metagenômica")
    
    # Sumário executivo
    summary = """Este relatório apresenta uma análise abrangente dos dados metagenômicos,
incluindo diversidade alfa, diversidade beta, composição taxonômica e análise de rarefação."""
    
    report.add_section("Sumário Executivo", summary, level=2)
    
    # Adicionar cada análise
    if 'alpha' in analyses:
        report.add_section("Diversidade Alfa", analyses['alpha'], level=2)
    
    if 'beta' in analyses:
        report.add_section("Diversidade Beta", analyses['beta'], level=2)
    
    if 'taxonomy' in analyses:
        report.add_section("Composição Taxonômica", analyses['taxonomy'], level=2)
    
    if 'rarefaction' in analyses:
        report.add_section("Análise de Rarefação", analyses['rarefaction'], level=2)
    
    # Conclusões
    conclusion = """
**Conclusões:**

As análises realizadas fornecem uma visão abrangente da composição e diversidade
das comunidades microbianas presentes nas amostras estudadas.
"""
    report.add_section("Conclusões", conclusion, level=2)
    
    # Gerar relatório
    if output_format == "html":
        return report.generate_html("data/qiime2/relatorio_completo.html")
    else:
        return report.generate_markdown("data/qiime2/relatorio_completo.md")
