from prefab_classes import prefab


@prefab(compile_prefab=True, compile_fallback=True, kw_only=True)
class Config:
    """
    Configuration class to store launch settings.
    """
    quiet_mode: bool = False
    cache_size: int = 5

    def as_dict(self):
        """
        Convert this config to a dictionary to pass to the JSON export.

        The builtin prefab-classes as_dict function is intended for multiple uses in one program.
        """
        return {f: getattr(self, f) for f in getattr(self, "PREFAB_FIELDS")}
