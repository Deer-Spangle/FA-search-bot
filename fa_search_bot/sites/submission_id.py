import dataclasses


@dataclasses.dataclass(frozen=True)
class SubmissionID:
    site_code: str
    submission_id: str

    @classmethod
    def from_inline_code(cls, inline_code: str) -> "SubmissionID":
        id_split = inline_code.split(":")
        site_id = "fa"
        if len(id_split) == 2:
            site_id = id_split[0]
        sub_id = id_split[-1]
        return cls(site_id, sub_id)

    def to_inline_code(self) -> str:
        return f"{self.site_code}:{self.submission_id}"

    def __repr__(self) -> str:
        return f"SubID({self.site_code}: {self.submission_id})"
