"""
    Baseline rules.ini stat lookups, used to derive custom units/buildings/
    infantry that inherit every field from an existing type and only
    override a few -- e.g. a Rhino Tank with more health but everything
    else left at its default.

    A baseline can come from a plain rules.ini file, or from a TibEd .tib
    preset's embedded Rules block (see tibed.py) -- either way it ends up
    as the same {section: {key: value}} shape.
"""
from tibed import parse_ini


class RulesBaseline():
    """ Full stat blocks to derive custom types from """
    def __init__(self, sections):
        self.sections = sections

    @classmethod
    def from_file(cls, path):
        """ Load a plain rules.ini file """
        with open(path, 'r', encoding='latin-1') as f:
            return cls(parse_ini(f.read()))

    @classmethod
    def from_tib_preset(cls, preset, block_label='Rules'):
        """ Load from an already-opened tibed.TibPreset """
        block = preset.get_block(block_label)
        return cls(block.sections if block else {})

    def get_attributes(self, identifier):
        """
            A copy of the complete attribute dict for an existing (base)
            unit/building/infantry identifier, e.g. "MTNK" for the Rhino
            Tank. Raises KeyError if this baseline has no such section.
        """
        if identifier not in self.sections:
            raise KeyError(
                "no baseline definition for '{}' -- check the identifier "
                "or try a different baseline source".format(identifier))
        return dict(self.sections[identifier])
