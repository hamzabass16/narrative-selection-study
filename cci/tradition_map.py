"""Map Seshat religion names (core/religions) to canonical-text traditions.
Rule fixed 17 Oct 2026 before any CCI score was computed or linked to outcomes.
A religion maps to a tradition only if it is a branch, sect or regional form of that tradition.
Religions with no written canon that survives in a public-domain English translation map to None."""
import re
RULES = [  # (regex on religion name, tradition); first match wins
 (r'manich|mandea|mithra|yazid|druze|baha|shaykh|muqanna|ajivika|bogomil|marcion|paulician|tondrak|samarit|cult of', None),
 (r'christian|catholic|orthodox|protestant|anglican|calvin|lutheran|presbyter|baptist|methodist|evangelical|congregational|arminian|reformed|arian|monophysite|nestorian|maronite|coptic|melkite|unitates|apostolic|assyrian church|chaldean|syriac|suriyani|pelagian', 'Christianity'),
 (r'islam|sunni|shia|shiite|sufi|qadiri|ibadi|kizilbas|metwali|alawite|kharij', 'Islam'),
 (r'judaism|israelite|yahwism', 'Judaism'),
 (r'hindu|saiv|shaiv|vaisnav|smarta|saktist|vedic|brahmanical', 'Hinduism'),
 (r'buddh|therav|mahayana|hinayana', 'Buddhism'),
 (r'jain|nirgrantha', 'Jainism'),
 (r'zoroastr|mazdi', 'Zoroastrianism'),
 (r'confucian', 'Confucianism'),
 (r'daoism|taoism', 'Daoism'),
 (r'shinto', 'Shinto'),
 (r'egyptian', 'Egyptian'),
 (r'mesopotamian|babylonian|sumerian|akkadian|^assyrian religion', 'Mesopotamian'),
 (r'greek|hellenistic', 'Greek'),
 (r'^roman religion|^latin religion', 'Roman'),
 (r'norse|germanic', 'Norse-Germanic'),
]
def tradition(name):
    if not isinstance(name, str): return None
    n = name.lower()
    if 'shinto-buddhism' in n: return 'Shinto'   # syncretic; Shinto canon (Kojiki) assigned by first element of the name
    if 'hindu-buddhism' in n: return 'Hinduism'  # first element of the name
    if 'greco-egyptian' in n: return 'Greek'     # first element of the name
    for rx, t in RULES:
        if re.search(rx, n): return t
    return None
