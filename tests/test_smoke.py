"""Trechos não individualizados de edições reais: DOE/PB 01/05/2026 e 06/03/2026."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import robo
class PublicacoesReais(unittest.TestCase):
    def test_resenha_249(self):
        t=("GERÊNCIA EXECUTIVA DE CONCESSÃO DE DIREITOS E VANTAGENS\n"
           "Resenha n° : 249/2026\n"
           "DEFERIU o(s) seguinte(s) processo(s) de LICENÇA PARA TRATAR DE INTERESSES PARTICULARES")
        self.assertTrue(robo.PAT_GEDIV.search(robo.norm(t)))
        self.assertEqual(robo.PAT_RES.search(robo.norm(t)).group(1),"249/2026")
        self.assertEqual(robo.merit(t),"Deferido")
        self.assertEqual(robo.hierarchy(t)[3],"Licença para Interesses Particulares")
    def test_resenha_113(self):
        t=("GERÊNCIA EXECUTIVA DE CONC. DE DIREITOS E VANTAGENS\n"
           "RESENHA Nº : 113/2026 /DEREH/GS\n"
           "DEFERIU os Processos de PROGRESSÃO FUNCIONAL HORIZONTAL do Grupo Ocupacional de Apoio Judiciário GAJ-1700")
        self.assertTrue(robo.PAT_GEDIV.search(robo.norm(t)))
        self.assertEqual(robo.hierarchy(t)[:3],("Progressão","Horizontal","GAJ"))
        self.assertEqual(robo.merit(t),"Deferido")
