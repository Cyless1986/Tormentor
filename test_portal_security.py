import unittest
from unittest.mock import patch
import portal_security as s

class SecurityTest(unittest.TestCase):
    def test_production_origin_and_secure_cookie(self):
        with patch.object(s,'PUBLIC_ORIGIN','https://tormentor.example'):
            self.assertTrue(s.allowed_post({'Origin':'https://tormentor.example'}))
            self.assertFalse(s.allowed_post({'Origin':'https://evil.example'}))
            self.assertFalse(s.allowed_post({}))
            self.assertFalse(s.allowed_post({'Origin':'https://tormentor.example','Sec-Fetch-Site':'cross-site'}))
            self.assertIn('; Secure',s.cookie('tormentor_session=test; HttpOnly'))
    def test_auth_limit_and_untrusted_proxy_header(self):
        with patch.object(s,'PUBLIC_ORIGIN',''),patch.object(s,'_requests',{}):
            for i in range(15):self.assertTrue(s.allow_auth('test',{'X-Forwarded-For':str(i)}))
            self.assertFalse(s.allow_auth('test',{'X-Forwarded-For':'other'}))
