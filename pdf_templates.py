from jinja2 import Environment, BaseLoader
from xhtml2pdf import pisa
import io

# Template 1: Two Column Layout exactly fitting your chosen colors and backgrounds
TEMPLATE_1_HTML = """<html>
<head>
<style>
body { font-family: Arial; margin: 0px; padding: 0px; color: #222; }
table { width: 100%; border-collapse: collapse; }
td.left { width: 33%; background: #f4f4f4; padding: 20px 15px; vertical-align: top; }
td.right { width: 67%; padding: 25px 20px; vertical-align: top; }
h1 { font-size: 30pt; margin-top: 0px; margin-bottom: 5px; text-transform: uppercase; color: #111;}
h3 { font-size: 14pt; margin: 0px; margin-bottom: 15px; color: #555; text-transform: uppercase;}
h2 { font-size: 16pt; margin-top: 15px; margin-bottom: 8px; text-transform: uppercase; border-bottom: 2px solid #ccc; padding-bottom: 4px; color: #111;}
p { margin-top: 0px; margin-bottom: 12px; line-height: 1.5; font-size: 12.5pt;}
ul { margin-top: 5px; margin-bottom: 12px; padding-left: 18px;}
li { margin-bottom: 6px; line-height: 1.5; font-size: 12.5pt;}
.section-content { margin-bottom: 15px; font-size: 12.5pt; line-height: 1.5; }
</style>
</head>
<body>
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td class="left">
    {% if data.Contact %}
        <h2>Contact</h2>
        <div class="section-content">{{ data.Contact }}</div>
    {% endif %}

    {% for key, val in data.items() %}
        {% if key|lower in ['skills', 'languages', 'certifications', 'awards', 'hobbies', 'personal information'] %}
            <h2>{{ key }}</h2>
            <div class="section-content">{{ val }}</div>
        {% endif %}
    {% endfor %}
</td>

<td class="right">
    <h1>{{ data.Name | default("Candidate Name") }}</h1>
    {% if data.Title %}
    <h3>{{ data.Title }}</h3>
    {% endif %}

    {% if data.Summary %}
    <h2>Summary</h2>
    <div class="section-content">{{ data.Summary }}</div>
    {% endif %}

    {% for key, val in data.items() %}
        {% if key|lower not in ['name', 'title', 'contact', 'summary', 'about me', 'skills', 'languages', 'certifications', 'awards', 'hobbies', 'personal information'] %}
            <h2>{{ key }}</h2>
            <div class="section-content">{{ val }}</div>
        {% endif %}
    {% endfor %}
</td>
</tr>
</table>
</body>
</html>"""

# Template 2: Single Column Layout with Red/Pink Header styling
TEMPLATE_2_HTML = """<html>
<head>
<style>
@page { margin: 0px; }
body { font-family: Georgia; background: #fdf6f0; margin: 0px; padding: 0px; color: #333; }
.container { padding: 20px 30px; }
h1 { color: #c97b84; margin-top: 0px; margin-bottom: 2px; font-size: 22pt; text-transform: uppercase;}
h3 { color: #555; margin-top: 0px; margin-bottom: 8px; font-style: italic; font-size: 12pt;}
h2 { font-size: 13pt; color: #c97b84; border-bottom: 1px solid #c97b84; padding-bottom: 2px; margin-top: 10px; margin-bottom: 5px; text-transform: uppercase;}
p { margin-top: 0px; margin-bottom: 5px; line-height: 1.25; font-size: 10pt;}
ul { margin-top: 3px; padding-left: 15px; margin-bottom: 5px;}
li { margin-bottom: 2px; line-height: 1.25; font-size: 10pt;}
.contact { font-size: 9.5pt; color: #666; margin-bottom: 10px; padding: 4px 0px; border-top: 1px dashed #ccc; border-bottom: 1px dashed #ccc;}
.section-content { margin-bottom: 8px; font-size: 10pt; line-height: 1.25;}
</style>
</head>
<body>

<div class="container">
    <h1>{{ data.Name | default("Candidate Name") }}</h1>
    {% if data.Title %}
    <h3>{{ data.Title }}</h3>
    {% endif %}
    
    {% if data.Contact %}
    <div class="contact">
        {{ data.Contact | replace('<br>', ' &bull; ') | striptags }}
    </div>
    {% endif %}

    {% if data.Summary %}
    <h2>About Me</h2>
    <div class="section-content">{{ data.Summary }}</div>
    {% endif %}

    {% for key, val in data.items() %}
        {% if key|lower not in ['name', 'title', 'contact', 'summary', 'about me'] %}
            <h2>{{ key }}</h2>
            <div class="section-content">{{ val }}</div>
        {% endif %}
    {% endfor %}
</div>

</body>
</html>"""

TEMPLATE_3_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
    @page { margin: 25px; }
    body { font-family: Times-Roman, serif; font-size: 10pt; color: #000; line-height: 1.25; margin: 0px; padding: 0px;}
    .header { text-align: center; margin-bottom: 10px; }
    h1 { font-size: 24pt; text-transform: uppercase; margin: 0px; letter-spacing: 1px; }
    .title { font-size: 11pt; text-transform: uppercase; font-weight: bold; margin-top: 3px; margin-bottom: 4px; color: #444; }
    .contact { font-size: 8.5pt; color: #555; }
    h2 { font-size: 12pt; text-transform: uppercase; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 2px 0px; margin-top: 12px; margin-bottom: 6px; }
    .section-content { margin-bottom: 8px; font-size: 10pt;}
    ul { margin-top: 3px; padding-left: 15px; }
    li { margin-bottom: 2px; line-height: 1.25; }
</style>
</head>
<body>
    <div class="header">
        <h1>{{ data.Name | default("Candidate Name") }}</h1>
        {% if data.Title %}
        <div class="title">{{ data.Title }}</div>
        {% endif %}
        {% if data.Contact %}
        <div class="contact">
            {{ data.Contact | replace('<br>', ' | ') | striptags }}
        </div>
        {% endif %}
    </div>
    
    {% if data.Summary %}
    <h2>Summary</h2>
    <div class="section-content">{{ data.Summary }}</div>
    {% endif %}

    {% for key, val in data.items() %}
        {% if key|lower not in ['name', 'title', 'contact', 'summary'] and val %}
            <h2>{{ key }}</h2>
            <div class="section-content">{{ val }}</div>
        {% endif %}
    {% endfor %}
</body>
</html>
"""

def render_html_template(template_name, data_dict):
    """Renders the HTML string using Jinja2."""
    formatted_data = {}
    
    # Intelligently clean up and format the output from Gemini into proper HTML
    for key, val in data_dict.items():
        if isinstance(val, dict):
            # Format nested dictionary values cleanly (like Contact info)
            lines = []
            for k, v in val.items():
                lines.append(f"<b>{k}:</b> {v}")
            formatted_data[key] = "<br>".join(lines)
        elif isinstance(val, list):
            ul = "<ul>"
            for item in val:
                ul += f"<li>{item}</li>"
            ul += "</ul>"
            formatted_data[key] = ul
        elif isinstance(val, str):
            # Often Gemini returns string descriptions with bullets inside them.
            raw_text = val.replace("\\n", "\n")
            
            # Fix Gemini glitch where bullets are inline separated by " * " instead of newlines
            if (" * " in raw_text or " • " in raw_text) and raw_text.count("\n") < 2:
                raw_text = raw_text.replace(" * ", "\n* ").replace(" • ", "\n• ")
                if not raw_text.strip().startswith(("*", "•", "-")):
                    raw_text = "* " + raw_text.strip()
            
            lines = raw_text.split('\n')
            
            # Check if there are list markers
            list_lines = [l for l in lines if l.strip().startswith(('-', '*', '•'))]
            if len(list_lines) >= 1 and len(lines) > 1:
                ul = "<ul>"
                for line in lines:
                    stripped = line.strip()
                    if stripped:
                        clean_line = stripped.lstrip('-*• \t')
                        ul += f"<li>{clean_line}</li>"
                ul += "</ul>"
                formatted_data[key] = ul
            else:
                html_formatted = str(val).replace("\\n", "<br>").replace("\n", "<br>")
                # Compress massive artificial vertical gaps 
                while "<br><br><br>" in html_formatted:
                    html_formatted = html_formatted.replace("<br><br><br>", "<br><br>")
                formatted_data[key] = html_formatted
        else:
            formatted_data[key] = str(val)

    env = Environment(loader=BaseLoader())
    
    if template_name == "Template 1":
        html_str = TEMPLATE_1_HTML
    elif template_name == "Template 2":
        html_str = TEMPLATE_2_HTML
    else:
        html_str = TEMPLATE_3_HTML
        
    template = env.from_string(html_str)
    return template.render(data=formatted_data)

def generate_pdf_from_html(html_content):
    """Converts HTML string to PDF bytes using xhtml2pdf."""
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    if pisa_status.err:
        raise Exception("Error rendering PDF")
    pdf_buffer.seek(0)
    return pdf_buffer.read()
