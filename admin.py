from flask import Flask, render_template_string, request, redirect, flash, url_for
from bs4 import BeautifulSoup
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import copy
import re

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = "klassy_super_gizli_anahtar"

# --- AYARLAR ---
HTML_PATH = 'index.html'
BACKUP_DIR = 'backups'
IMG_DIR = 'assets/images' 

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# --- YARDIMCI FONKSİYONLAR ---
def backup_html():
    if os.path.exists(HTML_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f'index_backup_{timestamp}.html')
        shutil.copy2(HTML_PATH, backup_path)

def get_soup():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html_str = f.read()
        html_str = html_str.replace('../images/', 'assets/images/')
        html_str = html_str.replace('assets/images\\', 'assets/images/')
        return BeautifulSoup(html_str, 'html.parser')

def save_soup(soup):
    html_str = str(soup)
    html_str = html_str.replace('../images/', 'assets/images/')
    html_str = html_str.replace('assets/images\\', 'assets/images/')
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_str)

def handle_upload(file_obj):
    if file_obj and file_obj.filename:
        filename = secure_filename(file_obj.filename)
        filepath = os.path.join(IMG_DIR, filename)
        file_obj.save(filepath)
        return filepath.replace('\\', '/')
    return None

INLINE_TAGS = ['a', 'span', 'strong', 'b', 'i', 'em', 'br', 'img', 'small', 'sub', 'sup', 'mark']
def is_text_block(tag):
    if tag.name in ['script', 'style', 'noscript']: return False
    if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th', 'label']:
        return True
    if tag.name == 'div':
        has_text = False
        for c in tag.contents:
            if isinstance(c, str):
                if c.strip(): has_text = True
            elif c.name not in INLINE_TAGS:
                return False 
        return has_text
    return False

def get_page_sections(soup):
    sections = []
    added_ids = set()

    header = soup.find('header')
    if header:
        if not header.get('id'):
            header['id'] = 'site_ust_menu' 
        sec_id = header['id']
        added_ids.add(sec_id)
        sections.append({'id': sec_id, 'name': "🧭 ÜST MENÜ & LOGO"})

    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('#') and len(href) > 1:
            sec_id = href[1:]
            if sec_id not in added_ids and soup.find(id=sec_id):
                added_ids.add(sec_id)
                name = link.get_text(strip=True)
                if not name: name = sec_id.capitalize()
                sections.append({'id': sec_id, 'name': f"📄 {name}"})

    for sec in soup.find_all('section'):
        sec_id = sec.get('id')
        if sec_id and sec_id not in added_ids:
            added_ids.add(sec_id)
            sections.append({'id': sec_id, 'name': f"📑 {sec_id.capitalize()}"})

    for div in soup.find_all('div', class_=lambda c: c and any(x in c for x in ['page', 'slide', 'panel', 'section'])):
        sec_id = div.get('id')
        if sec_id and sec_id not in added_ids:
            added_ids.add(sec_id)
            ikon = "🔄 KOPYA: " if "kopya" in sec_id else "📂 "
            sections.append({'id': sec_id, 'name': f"{ikon}{sec_id.capitalize()}"})

    return sections

# --- HTML ARAYÜZ ŞABLONU ---
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Gelişmiş CMS</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body { background-color: #f8f9fa; }
        .sidebar { background: #2c3e50; min-height: 100vh; color: white; padding-top: 20px;}
        .sidebar a { color: #ecf0f1; padding: 12px 20px; display: block; text-decoration: none; border-bottom: 1px solid #34495e; font-size: 14px;}
        .sidebar a:hover, .sidebar a.active { background: #e74c3c; color: white; padding-left: 25px; border-left: 4px solid #fff;}
        .img-preview { max-height: 100px; border-radius: 5px; border: 1px solid #ddd; object-fit: contain; width: 100%; background: #e9ecef;}
        .data-attr-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin-bottom: 15px; border-radius: 4px; }
    </style>
</head>
<body>
<div class="container-fluid">
    <div class="row">
        <div class="col-md-2 sidebar px-0">
            <h5 class="text-center mb-4 mt-2 font-weight-bold">Site Bölümleri</h5>
            <a href="/" class="{% if not active_section %}active{% endif %}">📊 Genel Özet</a>
            {% for sec in sections %}
                <a href="/edit/{{ sec.id }}" class="{% if active_section == sec.id %}active{% endif %}">
                    {{ sec.name }}
                </a>
            {% endfor %}
        </div>

        <div class="col-md-10 p-4">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert alert-{{ category }} shadow-sm">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            {{ content | safe }}
        </div>
    </div>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
    document.querySelectorAll('.custom-file-input').forEach(function(input) {
        input.addEventListener('change', function(e) {
            var fileName = document.getElementById(input.id).files[0].name;
            e.target.nextElementSibling.innerText = fileName;
        });
    });
</script>
</body>
</html>
"""

# --- ROUTELER ---
@app.route('/', methods=['GET', 'POST'])
def dashboard():
    soup = get_soup()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_empty_section':
            sec_id = request.form.get('new_sec_id', 'yeni_bolum').strip().replace(' ', '_').lower()
            
            if soup.find(id=sec_id):
                flash('Bu ID ile bir bölüm zaten var. Farklı bir isim girin.', 'warning')
            else:
                backup_html()
                new_sec = soup.new_tag("div", id=sec_id, attrs={"class": "section pt-5 pb-5"})
                container = soup.new_tag("div", attrs={"class": "container"})
                row = soup.new_tag("div", attrs={"class": "row"})
                col = soup.new_tag("div", attrs={"class": "col-lg-12 text-center wow fadeInUp", "data-wow-duration": "1s", "data-wow-delay": "0.2s"})
                
                h2 = soup.new_tag("h2")
                h2.string = "Yeni Boş Bölüm"
                p = soup.new_tag("p")
                p.string = "Bu bölüm panelden sıfırdan eklendi. Metinleri, resimleri ve efektleri düzenleyebilirsiniz."
                
                col.append(h2)
                col.append(p)
                row.append(col)
                container.append(row)
                new_sec.append(container)
                
                footer = soup.find('footer')
                if footer:
                    footer.insert_before(new_sec)
                else:
                    soup.body.append(new_sec)
                    
                save_soup(soup)
                flash(f'Yeni boş bölüm (#{sec_id}) başarıyla oluşturuldu!', 'success')
            return redirect(url_for('dashboard'))

        elif action == 'delete_section_from_dash':
            sec_id_to_delete = request.form.get('sec_id')
            target = soup.find(id=sec_id_to_delete)
            if target:
                backup_html()
                target.decompose()
                save_soup(soup)
                flash(f'#{sec_id_to_delete} bölümü tamamen silindi!', 'danger')
            return redirect(url_for('dashboard'))

    sections = get_page_sections(soup)
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
        <h2 class="text-dark m-0">📊 Genel Özet ve Bölüm Yöneticisi</h2>
    </div>
    
    <div class="row mt-3">
        <div class="col-md-4">
            <div class="card shadow-sm border-primary mb-4">
                <div class="card-header bg-primary text-white font-weight-bold">➕ Yeni Boş Bölüm Ekle</div>
                <div class="card-body">
                    <form method="POST">
                        <input type="hidden" name="action" value="add_empty_section">
                        <label class="text-muted small">Bölüm ID (İngilizce karakter, örn: galeri)</label>
                        <input type="text" name="new_sec_id" class="form-control mb-3" placeholder="yeni_bolum" required>
                        <button type="submit" class="btn btn-primary btn-block font-weight-bold shadow-sm">Sayfaya Ekle</button>
                    </form>
                </div>
            </div>
            
            <div class="card p-4 border-success text-center shadow-sm">
                <h1 class="text-success m-0">{len(sections)}</h1>
                <p class="mb-0 text-muted small font-weight-bold">Toplam Düzenlenebilir Bölüm</p>
            </div>
        </div>

        <div class="col-md-8">
            <div class="card shadow-sm border-dark">
                <div class="card-header bg-dark text-white font-weight-bold">⚙️ Mevcut Bölümleri Düzenle / Sil</div>
                <div class="card-body p-0" style="max-height: 600px; overflow-y: auto;">
                    <table class="table table-hover table-striped mb-0">
                        <thead class="bg-light sticky-top">
                            <tr>
                                <th>Bölüm Adı</th>
                                <th>HTML ID</th>
                                <th class="text-right">İşlemler</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    if not sections:
        content += '<tr><td colspan="3" class="text-center text-muted py-4">Henüz hiçbir bölüm bulunamadı.</td></tr>'
    else:
        for sec in sections:
            # --- GİZLİLİK KONTROLÜ ---
            target = soup.find(id=sec['id'])
            is_hidden = False
            if target:
                cls = target.get('class', [])
                if isinstance(cls, str): cls = cls.split()
                if 'd-none' in cls: is_hidden = True
                
            hidden_badge = '<span class="badge badge-warning ml-2 shadow-sm">🙈 Gizli</span>' if is_hidden else ''
            row_style = 'opacity: 0.6;' if is_hidden else ''
            # -------------------------

            content += f"""
                            <tr style="{row_style}">
                                <td class="align-middle font-weight-bold text-dark">{sec['name']} {hidden_badge}</td>
                                <td class="align-middle text-muted small">#{sec['id']}</td>
                                <td class="text-right align-middle">
                                    <a href="/edit/{sec['id']}" class="btn btn-sm btn-info font-weight-bold shadow-sm">✏️ Düzenle</a>
                                    
                                    <form method="POST" class="d-inline-block m-0 ml-1" onsubmit="return confirm('DİKKAT! #{sec['id']} bölümünü kalıcı olarak silmek istediğinize emin misiniz?');">
                                        <input type="hidden" name="action" value="delete_section_from_dash">
                                        <input type="hidden" name="sec_id" value="{sec['id']}">
                                        <button type="submit" class="btn btn-sm btn-danger font-weight-bold shadow-sm">🗑️ Sil</button>
                                    </form>
                                </td>
                            </tr>
            """
            
    content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """
    
    return render_template_string(ADMIN_TEMPLATE, content=content, sections=sections, active_section=None)

@app.route('/edit/<section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    soup = get_soup()
    sections = get_page_sections(soup)
    target_section = soup.find(id=section_id)
    
    if not target_section:
        flash('Bu bölüm bulunamadı!', 'danger')
        return redirect(url_for('dashboard'))

    texts = [tag for tag in target_section.find_all(True) if is_text_block(tag)]
    links = target_section.find_all('a')
    
    data_attrs = []
    for tag in target_section.find_all(True):
        for attr in tag.attrs:
            if attr in ['data-percentage', 'data-count', 'data-value', 'data-number']:
                data_attrs.append({'tag': tag, 'attr': attr, 'val': tag[attr]})

    editable_images = []
    sec_bg_src = ''
    sec_bg_type = 'inject_sec_bg' 
    
    if target_section.has_attr('style') and re.search(r'background.*url\(', target_section['style'], re.IGNORECASE):
        match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', target_section['style'])
        if match:
            sec_bg_src = match.group(1)
            sec_bg_type = 'sec_bg_inline'
    elif target_section.has_attr('data-image'):
        sec_bg_src = target_section['data-image']
        sec_bg_type = 'sec_bg_data'
        
    editable_images.append({
        'type': sec_bg_type,
        'tag': target_section,
        'src': sec_bg_src,
        'label': '🌟 BÖLÜM ANA ARKA PLANI (Tam Ekran)'
    })

    for tag in target_section.find_all(True):
        if tag.name == 'img':
            editable_images.append({'type': 'img', 'tag': tag, 'src': tag.get('src', ''), 'label': 'Standart Resim'})
        elif tag.has_attr('style') and re.search(r'background.*url\(', tag['style'], re.IGNORECASE):
            match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', tag['style'])
            if match:
                editable_images.append({'type': 'bg', 'tag': tag, 'src': match.group(1), 'label': 'Kutucuk Arka Planı'})
        elif tag.has_attr('data-image'):
            editable_images.append({'type': 'data_image', 'tag': tag, 'src': tag['data-image'], 'label': 'Grid/Kutu Resmi (data-image)'})
        elif tag.name == 'div' and tag.has_attr('class') and any(k in ' '.join(tag['class']).lower() for k in ['icon', 'thumb', 'feature', 'service']):
            if not tag.find('img') and not (tag.has_attr('style') and 'url(' in tag.get('style', '')):
                editable_images.append({'type': 'inject_bg', 'tag': tag, 'src': '', 'label': f"CSS İkonu ({' '.join(tag.get('class', []))})"})

    animated_elements = target_section.find_all(class_=re.compile(r'\b(wow)\b'))
    if not animated_elements:
        animated_elements = target_section.find_all(class_=re.compile(r'\bcol-'))

    # ================== POST İŞLEMLERİ ==================
    if request.method == 'POST':
        backup_html()
        action = request.form.get('action', 'save_content')

        if action == 'move_up':
            prev_sec = target_section.find_previous_sibling(['section', 'div'])
            if prev_sec:
                target_section.extract()
                prev_sec.insert_before(target_section)
                save_soup(soup)
                flash('Bölüm bir üste taşındı!', 'success')
            else:
                flash('Bu bölüm zaten en üstte!', 'warning')
            return redirect(url_for('edit_section', section_id=section_id))

        elif action == 'move_down':
            next_sec = target_section.find_next_sibling(['section', 'div'])
            if next_sec:
                target_section.extract()
                next_sec.insert_after(target_section)
                save_soup(soup)
                flash('Bölüm bir alta taşındı!', 'success')
            else:
                flash('Bu bölüm zaten en altta!', 'warning')
            return redirect(url_for('edit_section', section_id=section_id))

        elif action == 'clone_section':
            new_section = copy.copy(target_section)
            new_id = f"{section_id}_kopya_{int(datetime.now().timestamp())}"
            new_section['id'] = new_id
            target_section.insert_after(new_section)
            save_soup(soup)
            flash(f'Bölüm birebir kopyalandı! (KOPYA: {new_id})', 'success')
            return redirect(url_for('dashboard'))

        elif action == 'clone_empty':
            new_section = copy.copy(target_section)
            new_id = f"{section_id}_bos_kopya_{int(datetime.now().timestamp())}"
            new_section['id'] = new_id
            container = new_section.find(class_='container')
            if container:
                container.clear() 
                row = soup.new_tag("div", attrs={"class": "row"})
                col = soup.new_tag("div", attrs={"class": "col-lg-12 text-center py-5"})
                placeholder = soup.new_tag("h5", attrs={"class": "text-muted"})
                placeholder.string = "Bu alan temizlendi. Yeni içeriklerinizi ekleyebilirsiniz."
                col.append(placeholder)
                row.append(col)
                container.append(row)
            else:
                new_section.clear() 
                
            target_section.insert_after(new_section)
            save_soup(soup)
            flash(f'Genel çerçeve korundu, iç veriler temizlenerek kopyalandı! (KOPYA: {new_id})', 'success')
            return redirect(url_for('dashboard'))
        elif action == 'toggle_visibility':
            classes = target_section.get('class', [])
            if isinstance(classes, str):
                classes = classes.split(' ')
            else:
                classes = list(classes)
                
            if 'd-none' in classes:
                classes.remove('d-none')
                flash(f'#{section_id} bölümü artık web sitesinde GÖRÜNÜR durumda!', 'success')
            else:
                classes.append('d-none')
                flash(f'#{section_id} bölümü web sitesinden GİZLENDİ!', 'warning')
                
            if classes:
                target_section['class'] = classes
            elif 'class' in target_section.attrs:
                del target_section['class']
                
            save_soup(soup)
            return redirect(url_for('edit_section', section_id=section_id))
        elif action == 'delete_section':
            target_section.decompose() 
            save_soup(soup)
            flash(f'#{section_id} bölümü ve içindeki tüm veriler başarıyla silindi!', 'danger')
            return redirect(url_for('dashboard')) 
        
        elif action == 'delete_video':
            vid_index = int(request.form.get('vid_index', -1))
            vids = target_section.find_all(['iframe', 'video', 'embed'])
            if 0 <= vid_index < len(vids):
                vid_to_delete = vids[vid_index]
                parent_col = vid_to_delete.find_parent('div', class_=lambda c: c and 'col-' in c)
                if parent_col:
                    parent_row = parent_col.find_parent('div', class_='row')
                    if parent_row:
                        parent_container = parent_row.find_parent('div', class_='container')
                        if parent_container:
                            parent_container.decompose() 
                        else:
                            vid_to_delete.decompose()
                else:
                    vid_to_delete.decompose()
                    
                save_soup(soup)
                flash('İlgili medya başarıyla sayfadan silindi!', 'success')
            return redirect(url_for('edit_section', section_id=section_id))

        elif action == 'embed_pdf':
            pdf_file = request.files.get('pdf_file')
            pdf_height = request.form.get('pdf_height', '800')
            pdf_width = request.form.get('pdf_width', '100%')
            pdf_placement = request.form.get('pdf_placement', 'bottom') 
            
            if pdf_file and pdf_file.filename != '':
                pdf_path = handle_upload(pdf_file)
                if pdf_path:
                    embed_tag = soup.new_tag("embed", src=f"{pdf_path}", type="application/pdf", width=pdf_width, height=f"{pdf_height}px", style="border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); max-width: 100%;")
                    
                    if pdf_placement == 'inside':
                        container = target_section.find(class_='container')
                        if not container:
                            target_section.clear()
                            container = soup.new_tag("div", attrs={"class": "container", "style": "padding: 60px 0;"})
                            target_section.append(container)
                        else:
                            container.clear() 
                            
                        row = soup.new_tag("div", attrs={"class": "row"})
                        col = soup.new_tag("div", attrs={"class": "col-lg-12 text-center"})
                        col.append(embed_tag)
                        row.append(col)
                        container.append(row)
                        flash('İç veriler temizlendi ve PDF tablo çerçevenizin içine oturtuldu!', 'success')
                    elif pdf_placement == 'top':
                        container = soup.new_tag("div", attrs={"class": "container", "style": "padding-top: 40px; margin-bottom: 20px; text-align: center;"})
                        container.append(embed_tag)
                        target_section.insert(0, container)
                        flash('PDF başarıyla bölümün EN BAŞINA eklendi!', 'success')
                    else: 
                        container = soup.new_tag("div", attrs={"class": "container", "style": "padding-bottom: 40px; margin-top: 30px; text-align: center;"})
                        container.append(embed_tag)
                        target_section.append(container)
                        flash('PDF başarıyla bölümün EN SONUNA eklendi!', 'success')
                    save_soup(soup)
            else:
                flash('HATA: Lütfen bir PDF dosyası seçtiğinizden emin olun.', 'danger')
            return redirect(url_for('edit_section', section_id=section_id))

        elif action == 'embed_video':
            video_file = request.files.get('video_file')
            video_url = request.form.get('video_url', '').strip()
            video_width = request.form.get('video_width', '100%')
            video_height = request.form.get('video_height', '450px') 
            video_placement = request.form.get('video_placement', 'bottom')
            
            embed_tag = None
            
            if video_url:
                match = re.search(r'(?:v=|youtu\.be/|embed/|shorts/)([0-9A-Za-z_-]{11})', video_url)
                if match:
                    vid_id = match.group(1)
                    final_url = f"https://www.youtube.com/embed/{vid_id}"
                    
                    embed_tag = soup.new_tag("iframe", 
                        src=final_url, 
                        width=video_width, 
                        height=video_height, 
                        frameborder="0", 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture", 
                        allowfullscreen="true"
                    )
                    embed_tag['style'] = "border-radius: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); max-width: 100%;"
                else:
                    flash('HATA: Geçerli bir YouTube linki kopyaladığınızdan emin olun.', 'danger')
                    return redirect(url_for('edit_section', section_id=section_id))

            elif video_file and video_file.filename != '':
                video_path = handle_upload(video_file)
                if video_path:
                    embed_tag = soup.new_tag("video", attrs={
                        "controls": "", 
                        "width": video_width,
                        "style": "border-radius: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); max-width: 100%; background: #000;"
                    })
                    source_tag = soup.new_tag("source", src=f"{video_path}", type="video/mp4")
                    embed_tag.append(source_tag)

            if embed_tag:
                if video_placement == 'inside':
                    container = target_section.find(class_='container')
                    if not container:
                        target_section.clear()
                        container = soup.new_tag("div", attrs={"class": "container", "style": "padding: 60px 0;"})
                        target_section.append(container)
                    else:
                        container.clear() 
                        
                    row = soup.new_tag("div", attrs={"class": "row"})
                    col = soup.new_tag("div", attrs={"class": "col-lg-12 text-center"})
                    col.append(embed_tag)
                    row.append(col)
                    container.append(row)
                    flash('İç veriler temizlendi ve Video çerçevenizin içine oturtuldu!', 'success')
                elif video_placement == 'top':
                    container = soup.new_tag("div", attrs={"class": "container", "style": "padding-top: 40px; margin-bottom: 20px; text-align: center;"})
                    container.append(embed_tag)
                    target_section.insert(0, container)
                    flash('Video başarıyla bölümün EN BAŞINA eklendi!', 'success')
                else: 
                    container = soup.new_tag("div", attrs={"class": "container", "style": "padding-bottom: 40px; margin-top: 30px; text-align: center;"})
                    container.append(embed_tag)
                    target_section.append(container)
                    flash('Video başarıyla bölümün EN SONUNA eklendi!', 'success')
                    
                save_soup(soup)
            else:
                flash('HATA: Lütfen ya bir Youtube linki girin ya da bir dosya seçin!', 'danger')
            return redirect(url_for('edit_section', section_id=section_id))
        
        elif action == 'save_links':
            for i, link in enumerate(links):
                new_href = request.form.get(f'link_href_{i}')
                new_text = request.form.get(f'link_text_{i}')
                if new_href is not None: link['href'] = new_href
                if new_text and new_text.strip() != "": 
                    link.clear()
                    link.append(BeautifulSoup(new_text.strip(), 'html.parser'))

            new_link_href = request.form.get('new_link_href')
            new_link_text = request.form.get('new_link_text')
            if new_link_href and new_link_text and len(links) > 0:
                ornek_link = links[-1] 
                yeni_link = copy.copy(ornek_link)
                yeni_link['href'] = new_link_href
                yeni_link.clear()
                yeni_link.append(BeautifulSoup(new_link_text, 'html.parser'))
                ornek_link.insert_after(yeni_link)

            save_soup(soup)
            flash('Linkler kaydedildi!', 'success')
            return redirect(url_for('edit_section', section_id=section_id))

        elif action == 'save_effects':
            for i, el in enumerate(animated_elements):
                effect = request.form.get(f'effect_{i}')
                delay = request.form.get(f'delay_{i}')
                duration = request.form.get(f'duration_{i}')
                
                if effect:
                    classes = el.get('class', [])
                    anim_classes = ['fadeIn', 'fadeInUp', 'fadeInDown', 'fadeInLeft', 'fadeInRight', 'zoomIn', 'slideInUp']
                    classes = [c for c in classes if c not in anim_classes and c != 'wow' and c != 'animated']
                    if effect != 'none':
                        classes.append('wow')
                        classes.append(effect)
                    el['class'] = classes
                if delay: el['data-wow-delay'] = delay
                if duration: el['data-wow-duration'] = duration
                
            save_soup(soup)
            flash('Efektler başarıyla güncellendi!', 'success')
            return redirect(url_for('edit_section', section_id=section_id))

        else:
            for i, data_obj in enumerate(data_attrs):
                new_val = request.form.get(f"data_attr_{i}")
                hide_val = request.form.get(f"hide_data_attr_{i}")
                
                if new_val: 
                    data_obj['tag'][data_obj['attr']] = new_val
                
                # --- GİZLE/GÖSTER MANTIĞI ---
                # Etiketin içinde bulunduğu ana sütunu bul (yoksa kendisini al)
                parent_col = data_obj['tag'].find_parent(class_=re.compile(r'\bcol-'))
                target_tag = parent_col if parent_col else data_obj['tag']
                
                target_classes = target_tag.get('class', [])
                if isinstance(target_classes, str): 
                    target_classes = target_classes.split(' ')
                else: 
                    target_classes = list(target_classes)
                
                if hide_val == 'yes':
                    if 'd-none' not in target_classes:
                        target_classes.append('d-none')
                else:
                    if 'd-none' in target_classes:
                        target_classes.remove('d-none')
                        
                if target_classes:
                    target_tag['class'] = target_classes
                elif 'class' in target_tag.attrs:
                    del target_tag['class']
            # ----------------------------

            for i, tag in enumerate(texts):
                new_text = request.form.get(f'text_{i}')
                if new_text and new_text.strip() != "":
                    tag.clear()
                    tag.append(BeautifulSoup(new_text.strip(), 'html.parser'))
                    
            for i, img_data in enumerate(editable_images):
                remove_flag = request.form.get(f'remove_img_{i}')
                uploaded_file = request.files.get(f'img_{i}')
                
                if remove_flag == 'yes':
                    if img_data['type'] == 'img':
                        img_data['tag']['src'] = ''
                    elif img_data['type'] in ['data_image', 'sec_bg_data']:
                        img_data['tag']['data-image'] = ''
                    else:
                        old_override = img_data['tag'].find('style', class_='admin-bg-override')
                        if old_override:
                            old_override.decompose()
                        ex_style = img_data['tag'].get('style', '')
                        ex_style = re.sub(r'background[-image]*\s*:.*?url\([\'"]?.*?[\'"]?\).*?;?', '', ex_style)
                        img_data['tag']['style'] = ex_style + ("; " if ex_style else "") + "background-image: none !important;"
                        
                elif uploaded_file and uploaded_file.filename != '':
                    new_img_path = handle_upload(uploaded_file)
                    if new_img_path:
                        if img_data['type'] == 'img':
                            img_data['tag']['src'] = new_img_path
                        elif img_data['type'] in ['bg', 'sec_bg_inline']:
                            old_style = img_data['tag'].get('style', '')
                            new_style = re.sub(r'url\([\'"]?.*?[\'"]?\)', f"url('{new_img_path}')", old_style)
                            img_data['tag']['style'] = new_style
                        elif img_data['type'] in ['data_image', 'sec_bg_data']:
                            img_data['tag']['data-image'] = new_img_path
                        elif img_data['type'] == 'inject_bg':
                            ex_style = img_data['tag'].get('style', '')
                            inject = f"background-image: url('{new_img_path}') !important; background-size: contain; background-repeat: no-repeat; background-position: center;"
                            img_data['tag']['style'] = ex_style + ("; " if ex_style else "") + inject
                        elif img_data['type'] in ['inject_sec_bg', 'sec_bg_inline', 'bg']:
                            old_style = img_data['tag'].find('style', class_='admin-bg-override')
                            if old_style:
                                old_style.decompose()
                            css_rule = f"#{section_id} {{ background-image: url('{new_img_path}') !important; background-size: cover !important; background-position: center center !important; background-repeat: no-repeat !important; }}"
                            style_tag = soup.new_tag("style", attrs={"class": "admin-bg-override"})
                            style_tag.string = css_rule
                            img_data['tag'].insert(0, style_tag)
                            if img_data['tag'].has_attr('style'):
                                img_data['tag']['style'] = re.sub(r'background.*url\([\'"]?.*?[\'"]?\).*?;?', '', img_data['tag']['style'])

            save_soup(soup)
            flash('İçerikler başarıyla kaydedildi!', 'success')
            return redirect(url_for('edit_section', section_id=section_id))

    # ================== HTML OLUŞTURMA & LİSTELEME ==================
    embedded_videos = target_section.find_all(['iframe', 'video', 'embed'])
    video_list_html = """
    <div class="card shadow-sm border-danger mb-4">
        <div class="card-header bg-danger text-white font-weight-bold">🗑️ Sayfadaki Mevcut Medyalar (Video / PDF)</div>
        <div class="card-body p-0">
            <table class="table mb-0">
                <tbody>
    """
    
    if embedded_videos:
        for i, vid in enumerate(embedded_videos):
            if vid.name == 'iframe': vid_type = "YouTube / Iframe Oynatıcı"
            elif vid.name == 'video': vid_type = "Yerel MP4 Video"
            else: vid_type = "PDF Görüntüleyici"
            
            video_list_html += f"""
                    <tr>
                        <td class="align-middle pl-3"><strong>{vid_type}</strong> (Öğe #{i+1})</td>
                        <td class="text-right pr-3 py-2">
                            <form method="POST" class="m-0" onsubmit="return confirm('Bu öğeyi sayfadan tamamen silmek istediğinize emin misiniz?');">
                                <input type="hidden" name="action" value="delete_video">
                                <input type="hidden" name="vid_index" value="{i}">
                                <button type="submit" class="btn btn-sm btn-danger font-weight-bold shadow-sm">🗑️ Sil</button>
                            </form>
                        </td>
                    </tr>
            """
    else:
        video_list_html += """
                    <tr><td class="text-center text-muted py-3">Bu bölümde henüz eklenmiş bir video veya PDF bulunmuyor. Aşağıdaki formdan ekleyebilirsiniz.</td></tr>
        """
        
    video_list_html += "</tbody></table></div></div>"

    # --- HTML OLUŞTURMADAN ÖNCE BÖLÜM GÖRÜNÜRLÜK DURUMUNU KONTROL ET ---
    sec_classes = target_section.get('class', [])
    if isinstance(sec_classes, str): sec_classes = sec_classes.split(' ')
    is_hidden_section = 'd-none' in sec_classes
    
    visibility_btn_class = "btn-success" if is_hidden_section else "btn-secondary"
    visibility_icon = "👁️ Sayfada Göster" if is_hidden_section else "🙈 Bölümü Gizle"
    # ------------------------------------------------------------------

    html_content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
        <h3 class="text-danger m-0">📝 #{section_id}</h3>
        <div>
            <form method="POST" class="d-inline-block m-0">
                <input type="hidden" name="action" value="move_up">
                <button type="submit" class="btn btn-outline-secondary font-weight-bold shadow-sm" title="Yukarı Taşı">⬆️</button>
            </form>
            <form method="POST" class="d-inline-block m-0 mr-3">
                <input type="hidden" name="action" value="move_down">
                <button type="submit" class="btn btn-outline-secondary font-weight-bold shadow-sm" title="Aşağı Taşı">⬇️</button>
            </form>
            
            <form method="POST" class="d-inline-block m-0 mr-3">
                <input type="hidden" name="action" value="toggle_visibility">
                <button type="submit" class="btn {visibility_btn_class} font-weight-bold shadow-sm" title="Bölümü Aç/Kapat">{visibility_icon}</button>
            </form>

            <form method="POST" class="d-inline-block m-0 mr-1" onsubmit="return confirm('Bu bölümü verileriyle BİREBİR klonlamak istediğinize emin misiniz?');">
                <input type="hidden" name="action" value="clone_section">
                <button type="submit" class="btn btn-warning font-weight-bold shadow-sm">📑 Birebir Kopyala</button>
            </form>
            <form method="POST" class="d-inline-block m-0 mr-3" onsubmit="return confirm('Genel çerçeve (arka plan vb.) tutulup, içindeki tüm veriler temizlenerek klonlanacak. Onaylıyor musunuz?');">
                <input type="hidden" name="action" value="clone_empty">
                <button type="submit" class="btn btn-outline-warning font-weight-bold shadow-sm">🔲 Boş Çerçeve Kopyala</button>
            </form>
            <form method="POST" class="d-inline-block m-0" onsubmit="return confirm('DİKKAT! Bu bölümü ve içindeki TÜM tasarımları/verileri KALICI OLARAK silmek istediğinize emin misiniz? Bu işlem geri alınamaz!');">
                <input type="hidden" name="action" value="delete_section">
                <button type="submit" class="btn btn-danger font-weight-bold shadow-sm">🗑️ Bölümü Sil</button>
            </form>
        </div>
    </div>

    <ul class="nav nav-tabs mb-3">
        <li class="nav-item"><a class="nav-link active font-weight-bold" data-toggle="tab" href="#contentTab">Veriler ve Resimler</a></li>
        <li class="nav-item"><a class="nav-link font-weight-bold text-info" data-toggle="tab" href="#linksTab">🔗 Linkler</a></li>
        <li class="nav-item"><a class="nav-link font-weight-bold text-warning" data-toggle="tab" href="#effectsTab">✨ Efektler</a></li>
        <li class="nav-item"><a class="nav-link font-weight-bold text-danger" data-toggle="tab" href="#pdfTab">📕 PDF Göm</a></li>
        <li class="nav-item"><a class="nav-link font-weight-bold text-success" data-toggle="tab" href="#videoTab">🎬 Video Ekle</a></li>
    </ul>

    <div class="tab-content">
        <div class="tab-pane fade show active" id="contentTab">
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="action" value="save_content">
                <div class="row">
                    <div class="col-md-7">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white font-weight-bold">Açıklamalar</div>
                            <div class="card-body" style="max-height: 600px; overflow-y: auto;">
    """
    
    # DATA ATTR (YÜZDE/SAYI) GİZLEME-GÖSTERME DÖNGÜSÜ
    if data_attrs:
        for i, data_obj in enumerate(data_attrs):
            parent_col = data_obj['tag'].find_parent(class_=re.compile(r'\bcol-'))
            check_tag = parent_col if parent_col else data_obj['tag']
            
            check_classes = check_tag.get('class', [])
            if isinstance(check_classes, str): check_classes = check_classes.split(' ')
            
            is_hidden_item = 'd-none' in check_classes
            checked_str = 'checked' if is_hidden_item else ''
            
            html_content += f"""
            <div class="data-attr-box" style="background: #fff3cd; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="font-weight-bold mb-0 text-dark">{data_obj['attr']} Değeri</label>
                    <div class="custom-control custom-switch">
                        <input type="checkbox" class="custom-control-input" id="hideDataAttr_{i}" name="hide_data_attr_{i}" value="yes" {checked_str}>
                        <label class="custom-control-label text-danger small font-weight-bold" style="cursor:pointer;" for="hideDataAttr_{i}">Kutuyu Gizle</label>
                    </div>
                </div>
                <input type="text" name="data_attr_{i}" class="form-control" value="{data_obj['val']}">
            </div>
            """
            
    if not texts: 
        html_content += '<p class="text-muted">Metin bulunamadı.</p>'
    else:
        for i, tag in enumerate(texts):
            current_text = tag.decode_contents(formatter="html").strip()
            html_content += f"""
            <div class="form-group border-bottom pb-3">
                <label class="text-danger small font-weight-bold mb-1">[{tag.name.upper()}] Alan {i+1}</label>
                <textarea name="text_{i}" class="form-control" rows="2">{current_text}</textarea>
            </div>
            """
            
    html_content += """
                            </div>
                        </div>
                    </div>
                    <div class="col-md-5">
                        <div class="card shadow-sm mb-4">
                            <div class="card-header bg-info text-white font-weight-bold">Görseller</div>
                            <div class="card-body" style="max-height: 500px; overflow-y: auto;">
    """
    
    if not editable_images: 
        html_content += '<p class="text-muted">Görsel bulunamadı.</p>'
    else:
        for i, item in enumerate(editable_images):
            raw_src = item['src'].strip("'\" ")
            if raw_src.startswith('http') or raw_src.startswith('data:'): 
                preview_src = raw_src
            elif raw_src == "": 
                preview_src = "" 
            else:
                clean_src = raw_src.replace('../', '').replace('./', '').replace('\\', '/').lstrip('/')
                preview_src = f"/{clean_src}"

            if preview_src:
                img_tag_html = f'<img src="{preview_src}" class="img-preview mb-2" style="max-height:100px; width:100%; object-fit:contain;" alt="Görsel">'
            else:
                if item['type'] == 'inject_sec_bg':
                    img_tag_html = '<div class="text-danger small py-3" style="border: 1px dashed #dc3545; background: #fff;"><b>🎨 Tema Varsayılanı (CSS İçinde)</b><br><span class="text-muted">Mevcut arka plan harici CSS dosyasındadır. Yeni resim yükleyerek onu anında ezebilirsiniz.</span></div>'
                else:
                    img_tag_html = '<div class="text-muted small py-3" style="border: 1px dashed #ccc; background: #fff;">Boş İkon / CSS Kutusu<br>Resim gömülecek veya kaldırıldı.</div>'

            html_content += f"""
            <div class="mb-3 border p-2 bg-light rounded text-center">
                <span class="badge badge-secondary mb-2">{item['label']}</span>
                <div style="background: #e9ecef; padding: 5px; border-radius: 5px;">{img_tag_html}</div>
                
                <div class="custom-file mt-2">
                    <input type="file" name="img_{i}" class="custom-file-input" id="cImg{i}">
                    <label class="custom-file-label text-left" for="cImg{i}">Yeni Resim Seç...</label>
                </div>
                
                <div class="custom-control custom-checkbox text-left mt-2" style="background: #ffeeba; padding: 5px 5px 5px 30px; border-radius: 5px; border: 1px solid #ffc107;">
                    <input type="checkbox" class="custom-control-input" id="removeImg{i}" name="remove_img_{i}" value="yes">
                    <label class="custom-control-label text-danger font-weight-bold" style="cursor:pointer; font-size:13px;" for="removeImg{i}">🗑️ Bu Resmi / İkonu Tamamen Kaldır</label>
                </div>
            </div>
            """
            
    html_content += f"""
                            </div>
                        </div>
                        <button type="submit" class="btn btn-danger btn-lg btn-block shadow font-weight-bold">💾 Kaydet</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="tab-pane fade" id="linksTab">
            <form method="POST">
                <input type="hidden" name="action" value="save_links">
                <div class="card shadow-sm mb-4">
                    <div class="card-header bg-info text-white font-weight-bold">Link Yönetimi</div>
                    <div class="card-body">
    """
    if links:
        for i, link in enumerate(links):
            l_href = link.get('href', '')
            l_text = link.decode_contents(formatter="html").strip()
            html_content += f"""
            <div class="row mb-3 pb-3 border-bottom">
                <div class="col-6"><input type="text" name="link_text_{i}" class="form-control" value='{l_text}'></div>
                <div class="col-6"><input type="text" name="link_href_{i}" class="form-control" value="{l_href}"></div>
            </div>
            """
    html_content += """
                        <hr>
                        <h6 class="text-success font-weight-bold">Yeni Link Ekle</h6>
                        <div class="row">
                            <div class="col-6"><input type="text" name="new_link_text" class="form-control" placeholder="Link Metni"></div>
                            <div class="col-6"><input type="text" name="new_link_href" class="form-control" placeholder="URL (Örn: #about)"></div>
                        </div>
                    </div>
                    <div class="card-footer bg-white"><button type="submit" class="btn btn-info btn-block">🔗 Kaydet / Ekle</button></div>
                </div>
            </form>
        </div>

        <div class="tab-pane fade" id="effectsTab">
            <form method="POST">
                <input type="hidden" name="action" value="save_effects">
                <div class="card shadow-sm border-warning mb-4">
                    <div class="card-header bg-warning text-dark font-weight-bold">Giriş Efektleri</div>
                    <div class="card-body">
    """
    if not animated_elements: html_content += '<p class="text-muted">Öğe bulunamadı.</p>'
    else:
        for i, el in enumerate(animated_elements):
            classes = " ".join(el.get('class', []))
            current_effect = "none"
            for c in ['fadeIn', 'fadeInUp', 'fadeInDown', 'fadeInLeft', 'fadeInRight', 'zoomIn', 'slideInUp']:
                if c in classes: current_effect = c
            
            snippet = el.get_text(separator=' ', strip=True)[:30]
            if not snippet: snippet = "Görsel Kutu"
            
            html_content += f"""
            <div class="row mb-3 border-bottom pb-2">
                <div class="col-md-4"><small class="text-muted">"{snippet}..."</small></div>
                <div class="col-md-4">
                    <select name="effect_{i}" class="form-control form-control-sm">
                        <option value="none" {'selected' if current_effect == 'none' else ''}>Sabit (Efektsiz)</option>
                        <option value="fadeInUp" {'selected' if current_effect == 'fadeInUp' else ''}>Aşağıdan Yukarı</option>
                        <option value="fadeInLeft" {'selected' if current_effect == 'fadeInLeft' else ''}>Soldan Sağa</option>
                        <option value="fadeInRight" {'selected' if current_effect == 'fadeInRight' else ''}>Sağdan Sola</option>
                        <option value="zoomIn" {'selected' if current_effect == 'zoomIn' else ''}>Büyüyerek</option>
                    </select>
                </div>
                <div class="col-md-2"><input type="text" name="delay_{i}" class="form-control form-control-sm" value="{el.get('data-wow-delay', '0s')}" placeholder="Gecikme"></div>
                <div class="col-md-2"><input type="text" name="duration_{i}" class="form-control form-control-sm" value="{el.get('data-wow-duration', '1s')}" placeholder="Hız"></div>
            </div>
            """
    html_content += f"""
                    </div>
                    <div class="card-footer"><button type="submit" class="btn btn-warning btn-block">✨ Animasyonları Kaydet</button></div>
                </div>
            </form>
        </div>

        <div class="tab-pane fade" id="pdfTab">
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="action" value="embed_pdf">
                <div class="card shadow-sm border-danger">
                    <div class="card-header bg-danger text-white font-weight-bold">Bölüme PDF Ekle</div>
                    <div class="card-body">
                        <p class="text-muted">PDF'in sayfa içindeki konumunu seçebilirsiniz.</p>
                        <div class="row mb-3 border-bottom pb-3">
                            <div class="col-md-12">
                                <label class="font-weight-bold text-danger">Yerleşim / Konum Seçimi</label>
                                <select name="pdf_placement" class="form-control font-weight-bold">
                                    <option value="bottom">⬇️ Mevcut İçeriğin Korunarak BÖLÜM SONUNA Eklenmesi</option>
                                    <option value="top">⬆️ Mevcut İçeriğin Korunarak BÖLÜM BAŞINA Eklenmesi</option>
                                    <option value="inside">💥 İçeriği TEMİZLEYİP Doğrudan Tablo/Çerçeve İçine Oturtulması</option>
                                </select>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label class="font-weight-bold">PDF Dosyası Seç</label>
                                <input type="file" name="pdf_file" class="form-control-file" accept="application/pdf">
                            </div>
                            <div class="col-md-3">
                                <label class="font-weight-bold">Genişlik</label>
                                <input type="text" name="pdf_width" class="form-control" value="100%" placeholder="100% veya 800px">
                            </div>
                            <div class="col-md-3">
                                <label class="font-weight-bold">Yükseklik (px)</label>
                                <input type="number" name="pdf_height" class="form-control" value="800" min="200" max="2000">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-danger btn-lg mt-3 shadow btn-block">📕 Ayarlara Göre PDF Ekle</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="tab-pane fade" id="videoTab">
            {video_list_html}
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="action" value="embed_video">
                <div class="card shadow-sm border-success">
                    <div class="card-header bg-success text-white font-weight-bold">Bölüme YouTube veya Yerel Video Ekle</div>
                    <div class="card-body">
                        <div class="row mb-3 border-bottom pb-3">
                            <div class="col-md-12">
                                <label class="font-weight-bold text-success">Yerleşim / Konum Seçimi</label>
                                <select name="video_placement" class="form-control font-weight-bold">
                                    <option value="bottom">⬇️ BÖLÜM SONUNA Ekle (Mevcut İçeriği Koru)</option>
                                    <option value="top">⬆️ BÖLÜM BAŞINA Ekle (Mevcut İçeriği Koru)</option>
                                    <option value="inside">💥 BÖLÜMÜ TEMİZLE ve Ortasına Ekle</option>
                                </select>
                            </div>
                        </div>
                        <div class="row mb-3 bg-light p-3 rounded border">
                            <div class="col-md-6 border-right">
                                <label class="font-weight-bold text-danger">Seçenek 1: YouTube Linki (Önerilen)</label>
                                <input type="text" name="video_url" class="form-control" placeholder="Örn: https://www.youtube.com/watch?v=...">
                                <small class="text-muted">Linki yapıştırdığınızda otomatik olarak siteye gömülür.</small>
                            </div>
                            <div class="col-md-6">
                                <label class="font-weight-bold">Seçenek 2: Dosya Seç (MP4)</label>
                                <input type="file" name="video_file" class="form-control-file" accept="video/mp4,video/webm">
                                <small class="text-muted">Link girmezseniz buradan yüklediğiniz dosya geçerli olur.</small>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label class="font-weight-bold">Genişlik</label>
                                <input type="text" name="video_width" class="form-control" value="100%" placeholder="Örn: 100% veya 800px">
                            </div>
                            <div class="col-md-6">
                                <label class="font-weight-bold">Yükseklik (YouTube için önerilir)</label>
                                <input type="text" name="video_height" class="form-control" value="450px" placeholder="Örn: 450px">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-success btn-lg mt-4 shadow btn-block">🎬 Videoyu Sayfaya Ekle</button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(ADMIN_TEMPLATE, content=html_content, sections=sections, active_section=section_id)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
