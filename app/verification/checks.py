from app.verification.models import Claim, SourceTier


def validate_claims(claims: list[Claim]) -> list[str]:
    errors: list[str] = []
    for claim in claims:
        if claim.source_tier in (SourceTier.PRIMARY, SourceTier.SECONDARY) and not claim.source_url:
            errors.append(
                f"claim '{claim.text}' labeled {claim.source_tier.value} but missing source_url"
            )
    return errors
