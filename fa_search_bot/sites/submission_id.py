import dataclasses


@dataclasses.dataclass(frozen=True)
class SubmissionID:
    site_code: str
    submission_id: str
