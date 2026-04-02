"""
PYQ Auto-Fetcher — muquestionpapers.com
Uses broad link matching (like the original that found 40 papers),
but extracts the SUBJECT NAME from the URL path — not the anchor text.
"""
import urllib.request, urllib.error, re

DEPT_SLUG_MAP = {
    'COMP':  'computer-engineering',
    'IT':    'information-technology',
    'ENTC':  'electronics-and-telecommunication',
    'ETRX':  'electronics-engineering',
    'MECH':  'mechanical-engineering',
    'CIVIL': 'civil-engineering',
    'CHEM':  'chemical-engineering',
    'AUTO':  'automobile-engineering',
    'BIOMED':'biomedical-engineering',
    'ECS':   'electronics-and-computer-science',
    'ELEC':  'electrical-engineering',
    'AIDS':  'computer-engineering-aids',
    'FE':    'first-year-engineering',
    # AIML and DATA branches use AIDS (AI & Data Science) PYQs - same subjects for all years
    'AIML':  'computer-engineering-aids',
    'DATA':  'computer-engineering-aids',
}

BASE_URL = 'https://muquestionpapers.com'

MONTHS = {
    'january','february','march','april','may','june',
    'july','august','september','october','november','december',
    'jan','feb','mar','apr','jun','jul','aug','sep','oct','nov','dec'
}

NOISE_WORDS = {'sem','re','atkt','exam','paper','qp','kt','download',
               'click','here','view','open','pdf','get'}

def slug_to_subject(slug: str) -> str:
    """
    Convert URL slug → clean subject name.
    'engineering-mathematics-3-may-2019'  → 'Engineering Mathematics 3'
    'data-structures-november-2022'       → 'Data Structures'
    'computer-networks-2021'              → 'Computer Networks'
    """
    # Take only the last path segment if a full path is given
    slug = slug.rstrip('/').split('/')[-1]
    parts = slug.split('-')

    # Strip trailing 4-digit year
    while parts and re.fullmatch(r'\d{4}', parts[-1]):
        parts.pop()
    # Strip trailing month names
    while parts and parts[-1].lower() in MONTHS:
        parts.pop()
    # Strip trailing noise words
    while parts and parts[-1].lower() in NOISE_WORDS:
        parts.pop()

    if not parts:
        return 'Question Paper'

    # Capitalise each word; keep numbers as-is
    return ' '.join(
        p.upper() if re.fullmatch(r'[ivxlcdm]+', p, re.I) and len(p) <= 4
        else p.capitalize()
        for p in parts
    )


def get_mu_url(dept_code: str, semester: int) -> str:
    slug = DEPT_SLUG_MAP.get(dept_code.upper(), 'computer-engineering')
    return f"{BASE_URL}/be/{slug}/semester-{semester}"


def fetch_pyq_papers(dept_code: str, semester: int) -> list:
    """
    Fetch PYQ papers.  Strategy:
      1. Download the semester listing page.
      2. Find ALL <a href="..."> links that contain the branch slug in the URL
         (same broad approach that returned 40 results before).
      3. Extract subject name from the URL path — never from anchor text.
    Returns list of dicts: {subject, year, exam_type, url, semester, dept_code}
    """
    dept_slug = DEPT_SLUG_MAP.get(dept_code.upper(), 'computer-engineering')
    page_url  = f"{BASE_URL}/be/{dept_slug}/semester-{semester}"

    try:
        req = urllib.request.Request(page_url, headers={
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://muquestionpapers.com/',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception:
        return []

    papers = []
    seen   = set()

    # ── Strategy 1: match href containing the branch slug ────────
    # This is the broad pattern that found 40 papers originally.
    # Matches both absolute (https://muquestionpapers.com/be/...) and
    # relative (/be/...) hrefs.
    broad_re = re.compile(
        r'href=["\']([^"\']*/' + re.escape(dept_slug) + r'[^"\']*)["\']',
        re.IGNORECASE
    )

    for m in broad_re.finditer(html):
        href = m.group(1).strip()

        # Make absolute
        if href.startswith('/'):
            href = BASE_URL + href
        if not href.startswith('http'):
            continue

        # Must be deeper than the semester listing page itself
        # i.e. URL must have a path segment after semester-N
        sem_marker = f'/semester-{semester}/'
        if sem_marker not in href:
            continue

        # Normalise (remove query strings / fragments)
        href = href.split('?')[0].split('#')[0].rstrip('/')

        if href in seen:
            continue
        seen.add(href)

        # Extract the paper slug — the segment AFTER semester-N
        paper_slug = href.split(sem_marker)[-1]
        if not paper_slug or '/' in paper_slug:
            continue

        # Skip obvious non-paper paths
        if any(skip in paper_slug.lower() for skip in
               ['register','login','certification','mucertification']):
            continue

        # Year from slug
        year_m = re.search(r'(20\d\d)', paper_slug)
        year   = year_m.group(1) if year_m else 'N/A'

        # Exam type
        sl = paper_slug.lower()
        if any(k in sl for k in ['mid','prelim','internal','ct-','unit-test']):
            exam_type = 'Mid-Sem'
        elif any(k in sl for k in ['practical','lab','oral','-tw-','-or-']):
            exam_type = 'Practical'
        elif any(k in sl for k in ['re-exam','atkt','backlog','-kt-']):
            exam_type = 'Re-Exam'
        else:
            exam_type = 'End-Sem'

        # Subject name from slug
        subject = slug_to_subject(paper_slug)
        if not subject or subject.lower() in NOISE_WORDS:
            continue

        papers.append({
            'subject':   subject,
            'year':      year,
            'exam_type': exam_type,
            'url':       href,
            'semester':  semester,
            'dept_code': dept_code.upper(),
        })

    # ── Strategy 2: if strategy 1 found nothing, try .pdf links ──
    if not papers:
        pdf_re = re.compile(r'href=["\']([^"\']*\.pdf)["\']', re.IGNORECASE)
        for m in pdf_re.finditer(html):
            href = m.group(1).strip()
            if href.startswith('/'):
                href = BASE_URL + href
            if href in seen:
                continue
            seen.add(href)
            fname   = href.split('/')[-1].replace('.pdf','')
            year_m  = re.search(r'(20\d\d)', fname)
            year    = year_m.group(1) if year_m else 'N/A'
            subject = slug_to_subject(fname)
            papers.append({
                'subject':   subject, 'year': year,
                'exam_type': 'End-Sem', 'url': href,
                'semester':  semester,  'dept_code': dept_code.upper(),
            })

    # Sort: subject A→Z, year newest first
    papers.sort(key=lambda x: (x['subject'], x['year']), reverse=False)
    return papers[:60]


def get_source_url(dept_code: str, semester: int) -> str:
    return get_mu_url(dept_code, semester)
