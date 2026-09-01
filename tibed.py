"""
    Loader for TibEd (.tib) preset files.

    A .tib file is TibEd's own container format: a small header with a
    partial, TibEd-internal change summary, followed by one or more "TIBZ"
    blocks. Each TIBZ block is a zlib-compressed copy of a *complete*
    standard game config file -- Rules (rules.ini), Art (art.ini), Sound
    (soundmd.ini) have all been observed. That's exactly the same
    [Section]\\nKey=Value\\n format the rest of ra2py already works with, so
    there is no need to reverse-engineer TibEd's own binary format any
    further than locating and decompressing these blocks.

    TIBZ block layout (all integers little-endian):
        b"TIBZ"          4 bytes, tag
        unknown          1 byte  (8 in every sample seen so far)
        label_len        1 byte
        compressed_len   4 bytes, uint32
        uncompressed_len 4 bytes, uint32
        label            label_len bytes, ASCII ("Rules", "Art", "Sound", ...)
        data             compressed_len bytes, raw zlib stream
"""
import struct
import zlib


def parse_ini(text):
    """
        Minimal parser for rules.ini-style text: [Section] headers and
        Key=Value lines with optional trailing ';' comments. Returns
        {section: {key: value}}, in file order.
    """
    sections = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        if line.startswith('[') and ']' in line:
            current = line[1:line.index(']')]
            sections.setdefault(current, {})
            continue
        if current is None or '=' not in line:
            continue
        key, value = line.split('=', 1)
        value = value.split(';', 1)[0].strip()
        sections[current][key.strip()] = value
    return sections


class TibBlock():
    """ One decompressed config file embedded in a .tib preset """
    def __init__(self, label, text):
        self.label = label
        self.text = text
        self.sections = parse_ini(text)

    def __repr__(self):
        return "TibBlock({!r}, {} sections)".format(self.label, len(self.sections))


class TibPreset():
    """
        A TibEd .tib preset file: one or more embedded config files, keyed
        by their label ("Rules", "Art", "Sound", ...).
    """
    def __init__(self, path):
        self.path = path
        self.blocks = {}
        with open(path, 'rb') as f:
            data = f.read()
        self._parse(data)

    def _parse(self, data):
        i = 0
        while True:
            idx = data.find(b'TIBZ', i)
            if idx == -1:
                break
            label, block = self._decode_block(data, idx)
            self.blocks[label] = block
            i = idx + 4

    def _decode_block(self, data, idx):
        label_len = data[idx + 5]
        comp_len, uncomp_len = struct.unpack_from('<II', data, idx + 6)
        header_end = idx + 14
        label = data[header_end:header_end + label_len].decode('latin-1')
        stream_start = header_end + label_len
        raw = zlib.decompress(data[stream_start:stream_start + comp_len])
        assert len(raw) == uncomp_len, "decompressed size mismatch for " + label
        return label, TibBlock(label, raw.decode('latin-1'))

    def get_block(self, label):
        return self.blocks.get(label)

    def get_rules(self):
        """ The Rules block's sections, or {} if this preset has none """
        block = self.blocks.get('Rules')
        return block.sections if block else {}

    def __repr__(self):
        return "TibPreset({!r}, blocks={})".format(self.path, list(self.blocks))


def diff_presets(presets, block_label='Rules'):
    """
        Compare the given TibPreset objects' block (default 'Rules')
        against each other. Returns {(section, key): {preset_path: value}}
        for every (section, key) whose value differs across presets --
        i.e. the keys actually customized per-preset, with the shared
        RA2/YR baseline filtered out automatically (no external baseline
        rules.ini needed).
    """
    rules = {}
    all_sections = set()
    for preset in presets:
        block = preset.get_block(block_label)
        r = block.sections if block else {}
        rules[preset.path] = r
        all_sections |= set(r)

    diffs = {}
    for section in all_sections:
        keys = set()
        for r in rules.values():
            keys |= set(r.get(section, {}))
        for key in keys:
            values = {path: r.get(section, {}).get(key) for path, r in rules.items()}
            if len(set(values.values())) > 1:
                diffs[(section, key)] = values
    return diffs
