import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from score import _extract_keywords, _has_keyword, _tokens  # noqa: E402

assert _tokens("You'll build Jua's K8s EC2 S3 GPT-4 stack") == ["build", "jua", "k8s", "ec2", "s3", "gpt-4", "stack"]
assert not _has_keyword("field", "shipped a greenfield service")
assert not _has_keyword("java", "typescript and javascript")
assert _has_keyword("agent", "tool-calling agents")
assert _has_keyword("retrieval", "indexing, retrieval and reranking")
kws = dict(_extract_keywords("hybrid retrieval, reranking. hybrid retrieval, reranking."))
assert "retrieval reranking" not in kws and kws["hybrid retrieval"] == 2, kws
print("ok")
assert _has_keyword("design", "designed the data layer") and _has_keyword("define", "defined standards")
print("ok endings")
