import dataclasses


@dataclasses.dataclass(frozen=True)
class SiteLink:
    site_code: str
    link: str
