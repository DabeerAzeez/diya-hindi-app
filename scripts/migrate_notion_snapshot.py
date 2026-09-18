# Notion Snapshot Migration Script
import os
import sys
import json
import re
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.agents', 'skills', 'notion-sync', 'scripts')))
import notion_client as nc

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'diya', 'data')
LESSONS_DIR = os.path.join(DATA_DIR, 'lessons')
SONGS_DIR = os.path.join(DATA_DIR, 'songs')

os.makedirs(LESSONS_DIR, exist_ok=True)
os.makedirs(SONGS_DIR, exist_ok=True)

def rich_text_to_markdown(rich_texts):
    if not rich_texts:
        return ''
    out = []
    is_standalone_equation = len(rich_texts) == 1 and rich_texts[0].get('type') == 'equation'
    for rt in rich_texts:
        if rt.get('type') == 'equation':
            expr = rt.get('equation', {}).get('expression', '')
            if is_standalone_equation:
                out.append(f'$${expr}$$')
            else:
                out.append(f'${expr}$')
            continue
        text = rt.get('plain_text', '')
        annot = rt.get('annotations', {})
        if annot.get('code'):
            text = f'`{text}`'
        if annot.get('bold') and annot.get('italic'):
            text = f'***{text}***'
        elif annot.get('bold'):
            text = f'**{text}**'
        elif annot.get('italic'):
            text = f'*{text}*'
        if annot.get('strikethrough'):
            text = f'~~{text}~~'
        out.append(text)
    return ''.join(out)

def fetch_block_children(block_id):
    results = []
    cursor = None
    while True:
        url = f'blocks/{block_id}/children?page_size=100'
        if cursor:
            url += f'&start_cursor={cursor}'
        res = nc.api_request(url, method='GET')
        results.extend(res.get('results', []))
        if not res.get('has_more'):
            break
        cursor = res.get('next_cursor')
    return results

def blocks_to_markdown_and_data(blocks, default_title='Overview'):
    md_lines = []
    structured_sections = []
    current_section = {'title': default_title, 'type': 'heading_1', 'content': []}
    has_explicit_heading = False
    
    for b in blocks:
        b_type = b.get('type')
        has_children = b.get('has_children', False)
        bid = b.get('id')
        
        if b_type in ('heading_1', 'heading_2', 'heading_3'):
            if not has_explicit_heading and len(current_section['content']) > 0:
                structured_sections.append(current_section)
            has_explicit_heading = True
            rt = b.get(b_type, {}).get('rich_text', [])
            h_text = rich_text_to_markdown(rt)
            prefix = '#' if b_type == 'heading_1' else ('##' if b_type == 'heading_2' else '###')
            md_lines.append(f'\n{prefix} {h_text}\n')
            current_section = {'title': h_text, 'type': b_type, 'content': []}
            structured_sections.append(current_section)
            continue
            
        elif b_type == 'paragraph':
            rt = b.get('paragraph', {}).get('rich_text', [])
            p_text = rich_text_to_markdown(rt)
            md_lines.append(p_text + '\n')
            current_section['content'].append({'type': 'paragraph', 'text': p_text})
            
        elif b_type == 'equation':
            expr = b.get('equation', {}).get('expression', '')
            md_lines.append(f'\n$$\n{expr}\n$$\n')
            current_section['content'].append({'type': 'paragraph', 'text': f'$${expr}$$'})

        elif b_type == 'bulleted_list_item':
            rt = b.get('bulleted_list_item', {}).get('rich_text', [])
            item_text = rich_text_to_markdown(rt)
            md_lines.append(f'* {item_text}')
            children_items = []
            if has_children:
                ch_blocks = fetch_block_children(bid)
                for cb in ch_blocks:
                    c_type = cb.get('type')
                    c_rt = cb.get(c_type, {}).get('rich_text', [])
                    c_text = rich_text_to_markdown(c_rt)
                    md_lines.append(f'    * {c_text}')
                    children_items.append(c_text)
            current_section['content'].append({'type': 'bullet', 'text': item_text, 'children': children_items})
            
        elif b_type == 'numbered_list_item':
            rt = b.get('numbered_list_item', {}).get('rich_text', [])
            item_text = rich_text_to_markdown(rt)
            md_lines.append(f'1. {item_text}')
            children_items = []
            if has_children:
                ch_blocks = fetch_block_children(bid)
                for cb in ch_blocks:
                    c_type = cb.get('type')
                    c_rt = cb.get(c_type, {}).get('rich_text', [])
                    c_text = rich_text_to_markdown(c_rt)
                    md_lines.append(f'    * {c_text}')
                    children_items.append(c_text)
            current_section['content'].append({'type': 'numbered', 'text': item_text, 'children': children_items})
            
        elif b_type == 'toggle':
            rt = b.get('toggle', {}).get('rich_text', [])
            title = rich_text_to_markdown(rt)
            md_lines.append(f'<details><summary>{title}</summary>\n')
            toggle_children = []
            if has_children:
                ch_blocks = fetch_block_children(bid)
                for cb in ch_blocks:
                    c_type = cb.get('type')
                    c_rt = cb.get(c_type, {}).get('rich_text', [])
                    c_text = rich_text_to_markdown(c_rt)
                    md_lines.append(f'* {c_text}')
                    toggle_children.append(c_text)
            md_lines.append('</details>\n')
            current_section['content'].append({'type': 'toggle', 'title': title, 'children': toggle_children})
            
        elif b_type == 'table':
            rows_blocks = fetch_block_children(bid) if has_children else []
            table_rows = []
            for r in rows_blocks:
                if r.get('type') == 'table_row':
                    cells = r.get('table_row', {}).get('cells', [])
                    row_data = [re.sub(r'(?:<br\s*/?>\s*)+$', '', rich_text_to_markdown(c), flags=re.I).strip() for c in cells]
                    table_rows.append(row_data)
            
            if table_rows:
                header = table_rows[0]
                sep = ['---'] * len(header)
                md_lines.append('| ' + ' | '.join(header) + ' |')
                md_lines.append('| ' + ' | '.join(sep) + ' |')
                for row in table_rows[1:]:
                    md_lines.append('| ' + ' | '.join(row) + ' |')
                md_lines.append('')
            current_section['content'].append({'type': 'table', 'rows': table_rows})
            
        elif b_type == 'quote':
            rt = b.get('quote', {}).get('rich_text', [])
            q_text = rich_text_to_markdown(rt)
            md_lines.append(f'> {q_text}\n')
            current_section['content'].append({'type': 'quote', 'text': q_text})
            
        elif b_type == 'divider':
            md_lines.append('\n---\n')
            
    if not has_explicit_heading and len(current_section['content']) > 0:
        structured_sections.append(current_section)

    return '\n'.join(md_lines), structured_sections


def migrate():
    print('Starting Notion snapshot migration...')
    pages = nc.get_child_pages()
    lessons_list = []
    songs_list = []
    
    for p in pages:
        if p.get('type') != 'child_page':
            continue
        pid = p.get('id')
        title = p.get('child_page', {}).get('title', '')
        
        if title.startswith('Lesson '):
            print(f'Fetching Lesson: {title}...')
            code_match = re.search(r'Lesson\s+([A-Za-z0-9\.\-]+):', title)
            code = code_match.group(1) if code_match else title
            safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower()).strip('_')
            
            blocks = fetch_block_children(pid)
            clean_topic = re.sub(r'^Lesson\s+[A-Za-z0-9\.\-]+:\s*', '', title)
            md_text, sections = blocks_to_markdown_and_data(blocks, default_title=clean_topic or 'Overview')
            
            lesson_obj = {
                'id': pid,
                'code': code,
                'title': title,
                'slug': safe_slug,
                'sections': sections,
                'markdown': md_text
            }
            
            # Save individual lesson files
            with open(os.path.join(LESSONS_DIR, f'{safe_slug}.json'), 'w', encoding='utf-8') as f:
                json.dump(lesson_obj, f, indent=2, ensure_ascii=False)
            with open(os.path.join(LESSONS_DIR, f'{safe_slug}.md'), 'w', encoding='utf-8') as f:
                f.write(f'# {title}\n\n' + md_text)
                
            lessons_list.append({
                'id': pid,
                'code': code,
                'title': title,
                'slug': safe_slug,
                'filename': f'{safe_slug}.json'
            })
            time.sleep(0.3) # Notion rate-limit grace
            
        else:
            # Song breakdown page
            print(f'Fetching Song: {title}...')
            safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower()).strip('_')
            blocks = fetch_block_children(pid)
            
            spotify_url = None
            lyrics_url = None
            verses = []
            current_verse = {'title': 'Breakdown', 'lines': []}
            
            for b in blocks:
                b_type = b.get('type')
                if b_type == 'paragraph':
                    t = rich_text_to_markdown(b.get('paragraph', {}).get('rich_text', []))
                    if 'spotify.com' in t:
                        spotify_url = t
                    elif 'http' in t:
                        lyrics_url = t
                elif b_type in ('heading_2', 'heading_3'):
                    v_title = rich_text_to_markdown(b.get(b_type, {}).get('rich_text', []))
                    current_verse = {'title': v_title, 'lines': []}
                    verses.append(current_verse)
                elif b_type == 'toggle':
                    t_title = rich_text_to_markdown(b.get('toggle', {}).get('rich_text', []))
                    # Fetch breakdown lines inside toggle
                    tb = fetch_block_children(b['id']) if b.get('has_children') else []
                    line_breakdown = {'line': t_title, 'details': []}
                    for sub in tb:
                        sub_t = rich_text_to_markdown(sub.get(sub.get('type', ''), {}).get('rich_text', []))
                        if sub_t:
                            line_breakdown['details'].append(sub_t)
                    current_verse['lines'].append(line_breakdown)
                    
            if not verses and current_verse['lines']:
                verses.append(current_verse)
                
            song_obj = {
                'id': pid,
                'title': title,
                'slug': safe_slug,
                'spotify_url': spotify_url,
                'lyrics_url': lyrics_url,
                'verses': verses
            }
            
            with open(os.path.join(SONGS_DIR, f'{safe_slug}.json'), 'w', encoding='utf-8') as f:
                json.dump(song_obj, f, indent=2, ensure_ascii=False)
                
            songs_list.append({
                'id': pid,
                'title': title,
                'slug': safe_slug,
                'spotify_url': spotify_url,
                'filename': f'{safe_slug}.json'
            })
            time.sleep(0.3)

    # Save index manifests
    with open(os.path.join(DATA_DIR, 'lessons_index.json'), 'w', encoding='utf-8') as f:
        json.dump(lessons_list, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA_DIR, 'songs_index.json'), 'w', encoding='utf-8') as f:
        json.dump(songs_list, f, indent=2, ensure_ascii=False)
        
    print(f'✅ Successfully migrated {len(lessons_list)} lessons and {len(songs_list)} songs from Notion!')

if __name__ == '__main__':
    migrate()
