from typing import List
from langchain_core.outputs import ChatGeneration, Generation
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import (
    BaseGenerationOutputParser,
)


class CustomOutputParser(BaseGenerationOutputParser[str]):
    """An example parser that inverts the case of the characters in the message.

    This is an example parse shown just for demonstration purposes and to keep
    the example as simple as possible.
    """

    def parse_result(self, result: List[Generation], *, partial: bool = False) -> str:
        """Parse a list of model Generations into a specific format.

        Args:
            result: A list of Generations to be parsed. The Generations are assumed
                to be different candidate outputs for a single model input.
                Many parsers assume that only a single generation is passed it in.
                We will assert for that
            partial: Whether to allow partial results. This is used for parsers
                     that support streaming
        """
        if len(result) != 1:
            raise NotImplementedError(
                "This output parser can only be used with a single generation."
            )
        generation = result[0]
        if isinstance(generation, ChatGeneration):
            return generation.message.content
        if isinstance(generation, dict):
            return generation
        else:
            raise OutputParserException(
                "This output parser can only be used with a chat generation."
            )
