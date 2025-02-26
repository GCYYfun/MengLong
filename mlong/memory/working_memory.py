import re


class WorkingMemory:
    def __init__(self, memory_file=None):
        self.memory_file = memory_file
        self.long_term_memory = None

    def central_executive(self, query):
        if self._is_visual_query(query):
            return self.visuospatial_sketchpad(query)
        else:
            return self.phonological_loop(query)

    def phonological_loop(self, text):
        processed = {
            "words": len(re.findall(r"\w+", text)),
            "phonemes": self._count_phonemes(text),
            "type": "verbal",
        }
        return self.episodic_buffer(processed)

    def visuospatial_sketchpad(self, image):
        processed = {
            "shapes": self._detect_shapes(image),
            "colors": self._extract_colors(image),
            "type": "visual",
        }
        return self.episodic_buffer(processed)

    def epidodic_buffer(self, data):
        if self.long_term_memory:
            data["related_memory"] = self.retrieve_long_term_memory(data)
        return self._format_output(data)
