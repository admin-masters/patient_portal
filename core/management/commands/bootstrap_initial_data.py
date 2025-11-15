from django.core.management.base import BaseCommand
from core.models import Language
from geo.models import IndiaState

LANGS = [
    ("en", "English"),
    ("hi", "Hindi"),
    ("te", "Telugu"),
    ("ml", "Malayalam"),
    ("mr", "Marathi"),
    ("kn", "Kannada"),
    ("ta", "Tamil"),
    ("bn", "Bengali"),
]

# ISO 3166-2:IN codes (two-letter, common form)
STATES = [
    ("AN", "Andaman and Nicobar Islands"),
    ("AP", "Andhra Pradesh"),
    ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"),
    ("BR", "Bihar"),
    ("CH", "Chandigarh"),
    ("CT", "Chhattisgarh"),
    ("DH", "Dadra and Nagar Haveli and Daman and Diu"),
    ("DL", "Delhi"),
    ("GA", "Goa"),
    ("GJ", "Gujarat"),
    ("HP", "Himachal Pradesh"),
    ("HR", "Haryana"),
    ("JH", "Jharkhand"),
    ("JK", "Jammu and Kashmir"),
    ("KA", "Karnataka"),
    ("KL", "Kerala"),
    ("LA", "Ladakh"),
    ("LD", "Lakshadweep"),
    ("MH", "Maharashtra"),
    ("ML", "Meghalaya"),
    ("MN", "Manipur"),
    ("MP", "Madhya Pradesh"),
    ("MZ", "Mizoram"),
    ("NL", "Nagaland"),
    ("OD", "Odisha"),
    ("PB", "Punjab"),
    ("PY", "Puducherry"),
    ("RJ", "Rajasthan"),
    ("SK", "Sikkim"),
    ("TG", "Telangana"),
    ("TN", "Tamil Nadu"),
    ("TR", "Tripura"),
    ("UP", "Uttar Pradesh"),
    ("UT", "Uttarakhand"),
    ("WB", "West Bengal"),
]

class Command(BaseCommand):
    help = "Bootstraps Language and IndiaState tables."

    def handle(self, *args, **options):
        # Languages
        for code, name in LANGS:
            obj, created = Language.objects.get_or_create(code=code, defaults={"name": name})
            if not created and obj.name != name:
                obj.name = name
                obj.save(update_fields=["name"])
        self.stdout.write(self.style.SUCCESS("Languages ensured."))

        # States
        for iso, name in STATES:
            obj, created = IndiaState.objects.get_or_create(iso_code=iso, defaults={"name": name})
            if not created and obj.name != name:
                obj.name = name
                obj.save(update_fields=["name"])
        self.stdout.write(self.style.SUCCESS("India states ensured."))
