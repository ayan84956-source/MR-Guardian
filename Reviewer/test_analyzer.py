from mr_guardian.analyzers.ruff_analyzer import RuffAnalyzer
from mr_guardian.analyzers.bandit_analyzer import BanditAnalyzer

file_path = "tests/sample.py"

ruff = RuffAnalyzer()
bandit = BanditAnalyzer()

ruff_findings = ruff.analyze(file_path)
bandit_findings = bandit.analyze(file_path)

print("\n========== RUFF FINDINGS ==========")

for finding in ruff_findings:
    print(finding)

print("\n========== BANDIT FINDINGS ==========")

for finding in bandit_findings:
    print(finding)

print("\nTotal Ruff findings:", len(ruff_findings))
print("Total Bandit findings:", len(bandit_findings))
print(
    "Total static findings:",
    len(ruff_findings) + len(bandit_findings)
)