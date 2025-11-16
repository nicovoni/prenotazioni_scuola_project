from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings


class EmailValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Ensure domain is the expected default for tests
        settings.SCHOOL_EMAIL_DOMAIN = getattr(settings, 'SCHOOL_EMAIL_DOMAIN', 'isufol.it')

    def post_email(self, email):
        return self.client.post(reverse('email_login'), {'email': email})

    def test_valid_emails(self):
        valid = [
            'i.nizzo@isufol.it',
            'i.nizzo1@isufol.it',
            'n.cantalupo@isufol.it',
            "m.d'angelo@isufol.it",
        ]
        for e in valid:
            resp = self.post_email(e)
            # valid emails should redirect to verify_pin
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse('verify_pin'), resp['Location'])

    def test_invalid_emails(self):
        invalid = [
            'i.nizzo@example.com',    # wrong domain
            'i-nizzo@isufol.it',      # hyphen not allowed in local-part
            'inizzo@isufol.it',       # missing dot
            'i.m.nizzo@isufol.it',    # multiple dots/local structure
            'i. nizzo@isufol.it',     # space in local-part
            '@isufol.it',             # empty local-part
        ]
        for e in invalid:
            resp = self.post_email(e)
            # invalid should return 200 and render the form with error
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "Formato email non valido", msg_prefix=f"{e} should be invalid")
