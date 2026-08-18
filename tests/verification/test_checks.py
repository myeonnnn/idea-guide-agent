from app.verification.checks import validate_claims
from app.verification.models import Claim, SourceTier


def test_primary_claim_without_url_is_invalid():
    claims = [Claim(text="시장규모 100억원", source_tier=SourceTier.PRIMARY, source_url=None)]
    errors = validate_claims(claims)
    assert len(errors) == 1
    assert "시장규모 100억원" in errors[0]


def test_secondary_claim_without_url_is_invalid():
    claims = [Claim(text="업계 뉴스", source_tier=SourceTier.SECONDARY, source_url=None)]
    errors = validate_claims(claims)
    assert len(errors) == 1


def test_estimate_claim_without_url_is_valid():
    claims = [Claim(text="추정치", source_tier=SourceTier.ESTIMATE, source_url=None)]
    errors = validate_claims(claims)
    assert errors == []


def test_primary_claim_with_url_is_valid():
    claims = [
        Claim(text="공식 통계", source_tier=SourceTier.PRIMARY, source_url="https://stats.example.com")
    ]
    errors = validate_claims(claims)
    assert errors == []
