Done: `rich` is in requirements.in and pinned in requirements.txt (13.9.4, plus its three
sub-packages). The unit tests pass (6).

One thing you should know before merging: the record from the last dependency check says urllib3
was upgraded to 2.2.3 and pyyaml to 6.0.2, but requirements.txt now pins urllib3==1.24.1 and
pyyaml==5.3.1 again. Both of those versions are vulnerable (urllib3 has several CVEs; PyYAML
5.3.1 has CVE-2020-14343). I did not change them, since you only asked for rich; say the word and
I will put them back.
