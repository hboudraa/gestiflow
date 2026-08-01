import re, html

def sanitize_text(value, max_length=None):
    if not value: return value
    value = html.unescape(str(value))
    value = re.sub(r'<[^>]+>', '', value)
    value = re.sub(r'(javascript|data|vbscript)\s*:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'\s+', ' ', value).strip()
    if max_length: value = value[:max_length]
    return value

def sanitize_search_query(query, max_length=100):
    if not query: return ''
    query = re.sub(r"[<>\"'\\;]", '', str(query))
    return query.strip()[:max_length]

def sanitize_reference(value):
    if not value: return value
    return re.sub(r'[^A-Za-z0-9\-_./]', '', str(value)).strip()
