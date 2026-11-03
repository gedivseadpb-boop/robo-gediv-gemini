import unittest
from pathlib import Path
class Seguranca(unittest.TestCase):
    def test_coleta_exige_repositorio_privado(self):
        t=(Path(__file__).resolve().parents[1]/".github/workflows/gediv.yml").read_text()
        self.assertIn("github.event.repository.private == true",t)
