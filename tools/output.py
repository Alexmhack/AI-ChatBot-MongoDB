from chains.display import create_display_chain


def show_output(response):
    output_format = response.get("display_format", {}).get("output_format")
    output = response.get("output", {})
    tool_used = False  # output.get("tool_used")
    if tool_used:
        if output_format == "table":
            return response.get("output")
        elif output_format == "text" and (output_data := output.get("data")):
            display_chain = create_display_chain()
            output = display_chain.invoke({"input": output_data})
            return output
        else:
            return output.get("data")
    return response.get("output")  # .get("direct_response")
