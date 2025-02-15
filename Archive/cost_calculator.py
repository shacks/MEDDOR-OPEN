def calculate_cost(input_tokens, output_tokens):
    """
    Calculate the cost of an OpenAI API operation based on token usage.

    Parameters:
        input_tokens (int): Number of input tokens.
        output_tokens (int): Number of output tokens.

    Returns:
        dict: Costs for input, output, and total.
    """
    # Define prices per 1M tokens
    price_per_million_input = 0.150  # USD
    price_per_million_output = 0.600  # USD

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * price_per_million_input
    output_cost = (output_tokens / 1_000_000) * price_per_million_output
    total_cost = input_cost + output_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }