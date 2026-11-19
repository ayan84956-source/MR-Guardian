from mr_guardian.analyzers.ruff_analyzer import RuffAnalyzer
from mr_guardian.analyzers.bandit_analyzer import BanditAnalyzer

class StaticAnalysisEngine:

    def __init__(self):
        self.ruff = RuffAnalyzer()
        self.bandit = BanditAnalyzer()

    def analyze(self, file_path: str) -> list[dict]:

        findings = []

        findings.extend(self.ruff.analyze(file_path))
        findings.extend(self.bandit.analyze(file_path))

        return findings