import re
from typing import List

def turkish_lowercase(text: str) -> str:
    """Converts a string to lowercase handling Turkish character mapping (I->ı, İ->i) properly."""
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def clean_word(word: str) -> str:
    """Lowercases the word and strips leading/trailing non-alphanumeric punctuation."""
    word = turkish_lowercase(word)
    # Remove leading and trailing punctuation (like brackets, quotes, dashes)
    word = re.sub(r'^\W+|\W+$', '', word)
    return word

def stem_turkish_word(word: str) -> str:
    """A lightweight heuristic stemmer for Turkish nouns.
    Strips common suffixes (case markers, possessives, plurals)
    and reverses consonant mutation (yumuşama: b->p, c->ç, d->t, ğ->k).
    """
    word = clean_word(word)
    
    # We only stem words of length 3 or more to avoid destroying roots
    if len(word) < 3:
        return word
        
    # Turkish noun suffixes sorted from longest to shortest to strip greedy-first
    suffixes = [
        "larında", "lerinde", "larından", "lerinden",
        "ımızda", "imizde", "umuzda", "ümüzde",
        "ıncı", "inci", "uncu", "üncü",
        "larız", "leriz",
        "ların", "lerin", "ısıyla", "isiyle", "usuyla", "üsüyle",
        "ıyla", "iyle", "ıyla", "yle", "yla",
        "unda", "ünde", "ında", "inde",
        "dan", "den", "tan", "ten",
        "lar", "ler", "ımız", "imiz", "umuz", "ümüz",
        "ınız", "iniz", "nız", "niz",
        "da", "de", "ta", "te", "ya", "ye", "yı", "yi", "yu", "yü",
        "ın", "in", "un", "ün", "ı", "i", "u", "ü", "a", "e"
    ]
    
    stem = word
    for suffix in suffixes:
        if word.endswith(suffix):
            candidate = word[:-len(suffix)]
            if len(candidate) >= 3:
                stem = candidate
                break
                
    # Reverse Consonant Mutation (Ünsüz Yumuşaması)
    # If the word stems to ending with b, c, d, ğ, we restore to p, ç, t, k
    if stem.endswith('ğ'):
        stem = stem[:-1] + 'k'
    elif stem.endswith('b'):
        stem = stem[:-1] + 'p'
    elif stem.endswith('d'):
        stem = stem[:-1] + 't'
    elif stem.endswith('c'):
        stem = stem[:-1] + 'ç'
        
    return stem

def local_keyword_match(title: str, keywords: List[str]) -> bool:
    """Checks if any tracking keywords match words in the title.
    Supports:
    1. Exact clean match (e.g. 'monitör' == 'monitör')
    2. Turkish suffix stemming (e.g. title word 'monitörü' -> stem 'monitör' == keyword 'monitör')
    3. Compound word/brand substring checking (e.g. keyword 'macbook' in title word 'macbookpro')
    """
    title_clean = turkish_lowercase(title)
    
    # Clean and split the title into words
    words = title_clean.split()
    title_words = [clean_word(w) for w in words]
    title_stems = [stem_turkish_word(w) for w in title_words]
    
    # Build keyword stems
    keyword_pairs = []
    for kw in keywords:
        kw_clean = clean_word(kw)
        kw_stem = stem_turkish_word(kw_clean)
        keyword_pairs.append((kw_clean, kw_stem))
        
    # Check match against title words and stems
    for t_word, t_stem in zip(title_words, title_stems):
        if not t_word:
            continue
        for kw_clean, kw_stem in keyword_pairs:
            if not kw_clean:
                continue
            # Match conditions
            if (t_word == kw_clean or 
                t_stem == kw_stem or 
                kw_clean in t_word or 
                kw_stem in t_stem):
                return True
                
    return False
