import re
from urllib.parse import urlparse
from typing import Optional

class DomainFilter:
    INVALID_DOMAINS = {
        'apps.apple.com', 'chrome.google.com', 'addons.mozilla.org',
        'marketplace.visualstudio.com', 'github.com', 'gitlab.com'
    }
    
    INVALID_PATTERNS = [
        r'^https?://apps\.apple\.com/',
        r'^https?://chrome\.google\.com/',
        r'^https?://github\.com/[^/]+/[^/]+$'
    ]
    
    @classmethod
    def extract_domain(cls, url: str) -> Optional[str]:
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain if '.' in domain else None
        except:
            return None
    
    @classmethod
    def is_valid_for_similarweb(cls, url: str) -> bool:
        domain = cls.extract_domain(url)
        if not domain or domain in cls.INVALID_DOMAINS:
            return False
        
        for pattern in cls.INVALID_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return False
        
        # Check for major platform subdomains
        major_platforms = ['google.com', 'microsoft.com', 'amazon.com']
        for platform in major_platforms:
            if domain.endswith('.' + platform) and domain != platform:
                return False
                
        return True

## This is advanced domain filter this would be used in real scraping as we are doing it for experiment now so commenting it out
# import re
# from urllib.parse import urlparse
# from typing import Dict, List, Optional, Tuple
# import socket
# import ipaddress

# class AlgorithmicDomainValidator:
#     def __init__(self):
#         # TLD rankings for business legitimacy
#         self.tld_scores = {
#             '.com': 1.0, '.org': 0.9, '.net': 0.8, '.co': 0.85, '.io': 0.7,
#             '.ai': 0.75, '.tech': 0.6, '.biz': 0.7, '.info': 0.4, '.name': 0.3,
#             '.me': 0.5, '.tv': 0.4, '.cc': 0.3, '.tk': 0.1, '.ml': 0.1
#         }
        
#         # Service subdomain patterns (algorithmic detection)
#         self.service_indicators = {
#             'technical': ['api', 'cdn', 'static', 'assets', 'media', 'img', 'js', 'css'],
#             'functional': ['www', 'mail', 'email', 'ftp', 'sftp', 'ssh', 'vpn'],
#             'content': ['blog', 'news', 'docs', 'wiki', 'forum', 'community'],
#             'commercial': ['shop', 'store', 'cart', 'checkout', 'pay', 'billing'],
#             'support': ['support', 'help', 'service', 'ticket', 'chat'],
#             'development': ['dev', 'test', 'staging', 'beta', 'alpha', 'demo'],
#             'mobile': ['m', 'mobile', 'app', 'apps'],
#             'regional': ['us', 'uk', 'eu', 'asia', 'ca', 'au', 'de', 'fr', 'jp']
#         }
    
#     def extract_domain_components(self, url: str) -> Dict:
#         """Extract and analyze domain components without external libs"""
#         try:
#             if not url.startswith(('http://', 'https://')):
#                 url = 'https://' + url
            
#             parsed = urlparse(url)
#             domain_parts = parsed.netloc.lower().split('.')
            
#             # Simple TLD extraction (last part)
#             if len(domain_parts) >= 2:
#                 tld = '.' + domain_parts[-1]
                
#                 # Handle common two-part TLDs
#                 two_part_tlds = ['.co.uk', '.com.au', '.co.jp', '.com.br']
#                 if len(domain_parts) >= 3:
#                     potential_two_part = '.' + '.'.join(domain_parts[-2:])
#                     if potential_two_part in two_part_tlds:
#                         tld = potential_two_part
#                         domain_name = domain_parts[-3] if len(domain_parts) > 2 else domain_parts[0]
#                         subdomain_parts = domain_parts[:-3] if len(domain_parts) > 3 else []
#                     else:
#                         domain_name = domain_parts[-2]
#                         subdomain_parts = domain_parts[:-2] if len(domain_parts) > 2 else []
#                 else:
#                     domain_name = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
#                     subdomain_parts = []
#             else:
#                 tld = ''
#                 domain_name = domain_parts[0] if domain_parts else ''
#                 subdomain_parts = []
            
#             return {
#                 'original_url': url,
#                 'full_domain': parsed.netloc.lower(),
#                 'domain_name': domain_name,
#                 'tld': tld,
#                 'subdomain_parts': subdomain_parts,
#                 'subdomain': '.'.join(subdomain_parts) if subdomain_parts else '',
#                 'has_subdomain': bool(subdomain_parts),
#                 'path': parsed.path,
#                 'path_segments': [p for p in parsed.path.split('/') if p],
#                 'query_params': parsed.query,
#                 'fragment': parsed.fragment
#             }
#         except Exception as e:
#             return {'error': str(e)}
    
#     def analyze_subdomain_type(self, subdomain_parts: List[str]) -> Dict:
#         """Categorize subdomain without external services"""
#         if not subdomain_parts:
#             return {'type': 'root', 'is_service': False, 'confidence': 1.0}
        
#         subdomain_full = '.'.join(subdomain_parts).lower()
        
#         # Check against service patterns
#         service_matches = []
#         for category, indicators in self.service_indicators.items():
#             for indicator in indicators:
#                 if indicator in subdomain_full:
#                     service_matches.append((category, indicator))
        
#         # Pattern analysis
#         patterns = {
#             'numeric': re.search(r'\d+', subdomain_full),
#             'short_code': len(subdomain_full) <= 3 and subdomain_full.isalpha(),
#             'hyphenated': '-' in subdomain_full,
#             'multiple_levels': len(subdomain_parts) > 1,
#             'starts_with_www': subdomain_parts[0] == 'www'
#         }
        
#         # Decision logic
#         if patterns['starts_with_www'] and len(subdomain_parts) == 1:
#             return {'type': 'www', 'is_service': False, 'confidence': 0.9}
#         elif service_matches:
#             primary_match = service_matches[0]
#             return {
#                 'type': 'service',
#                 'service_category': primary_match[0],
#                 'is_service': True,
#                 'confidence': 0.8,
#                 'matches': service_matches
#             }
#         elif patterns['numeric']:
#             return {'type': 'technical', 'is_service': True, 'confidence': 0.7}
#         elif patterns['multiple_levels']:
#             return {'type': 'complex', 'is_service': True, 'confidence': 0.6}
#         else:
#             return {'type': 'unknown', 'is_service': False, 'confidence': 0.4}
    
#     def calculate_business_score(self, components: Dict) -> float:
#         """Calculate likelihood this is a main business website"""
#         if 'error' in components:
#             return 0.0
        
#         score = 1.0
        
#         # TLD quality
#         tld_score = self.tld_scores.get(components['tld'], 0.3)
#         score *= tld_score
        
#         # Subdomain analysis
#         if components['has_subdomain']:
#             subdomain_analysis = self.analyze_subdomain_type(components['subdomain_parts'])
            
#             if subdomain_analysis['is_service']:
#                 # Heavy penalty for service subdomains
#                 penalty = 0.8 * subdomain_analysis['confidence']
#                 score -= penalty
#             elif subdomain_analysis['type'] == 'www':
#                 # www is acceptable
#                 score *= 1.0
#             else:
#                 # Unknown subdomain - moderate penalty
#                 score -= 0.3
        
#         # Path analysis
#         path_segments = components['path_segments']
#         if len(path_segments) > 3:
#             score -= 0.2 * (len(path_segments) - 3)
        
#         # Domain name quality
#         domain_name = components['domain_name']
#         if domain_name:
#             # Length check
#             if 3 <= len(domain_name) <= 20:
#                 score += 0.1
            
#             # Character quality
#             if domain_name.isalpha():
#                 score += 0.05
#             elif re.match(r'^[a-z]+[0-9]*$', domain_name):
#                 score += 0.02
        
#         # Query parameters penalty (dynamic URLs)
#         if components['query_params']:
#             score -= 0.2
        
#         # Fragment penalty
#         if components['fragment']:
#             score -= 0.1
        
#         return max(0.0, min(1.0, score))
    
#     def detect_url_category(self, url: str) -> Dict:
#         """Comprehensive URL categorization"""
#         components = self.extract_domain_components(url)
        
#         if 'error' in components:
#             return {'is_valid': False, 'error': components['error']}
        
#         business_score = self.calculate_business_score(components)
        
#         # Specific pattern detection
#         url_lower = url.lower()
        
#         # App stores
#         app_store_patterns = [
#             r'apps?\.(apple|google)\.com',
#             r'play\.google\.com',
#             r'itunes\.apple\.com',
#             r'marketplace\.(firefox|chrome)',
#             r'addons\.mozilla'
#         ]
        
#         # Code repositories
#         code_repo_patterns = [
#             r'(github|gitlab|bitbucket)\.(com|org)',
#             r'\.github\.io',
#             r'sourceforge\.net',
#             r'codeberg\.org'
#         ]
        
#         # Social media patterns
#         social_patterns = [
#             r'(facebook|twitter|instagram|linkedin)\.com/.+',
#             r'(youtube|vimeo)\.com/(user|channel|c)/',
#             r'(medium|substack)\.com/@'
#         ]
        
#         category = 'main_business'
#         confidence = business_score
        
#         for pattern in app_store_patterns:
#             if re.search(pattern, url_lower):
#                 category = 'app_store'
#                 confidence = 0.95
#                 break
        
#         if category == 'main_business':
#             for pattern in code_repo_patterns:
#                 if re.search(pattern, url_lower):
#                     category = 'code_repository'
#                     confidence = 0.95
#                     break
        
#         if category == 'main_business':
#             for pattern in social_patterns:
#                 if re.search(pattern, url_lower):
#                     category = 'social_media'
#                     confidence = 0.90
#                     break
        
#         # Additional checks
#         if components['has_subdomain'] and business_score < 0.4:
#             subdomain_analysis = self.analyze_subdomain_type(components['subdomain_parts'])
#             if subdomain_analysis['is_service']:
#                 category = 'service_subdomain'
#                 confidence = subdomain_analysis['confidence']
        
#         is_valid = category == 'main_business' and business_score >= 0.6
        
#         return {
#             'is_valid': is_valid,
#             'category': category,
#             'confidence': confidence,
#             'business_score': business_score,
#             'components': components,
#             'reasoning': self._generate_reasoning(category, components, business_score)
#         }
    
#     def _generate_reasoning(self, category: str, components: Dict, score: float) -> str:
#         """Generate human-readable reasoning"""
#         if category == 'app_store':
#             return "Detected app store URL pattern"
#         elif category == 'code_repository':
#             return "Detected code repository URL pattern"
#         elif category == 'social_media':
#             return "Detected social media profile pattern"
#         elif category == 'service_subdomain':
#             subdomain_type = self.analyze_subdomain_type(components['subdomain_parts'])
#             return f"Service subdomain detected: {subdomain_type.get('service_category', 'unknown')}"
#         elif components['has_subdomain']:
#             return f"Subdomain present: {components['subdomain']} (score: {score:.2f})"
#         elif score < 0.6:
#             return f"Low business score: {score:.2f}"
#         else:
#             return f"Main business site (score: {score:.2f})"