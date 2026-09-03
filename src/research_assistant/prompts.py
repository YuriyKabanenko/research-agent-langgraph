def research_system_promp(topic):
    return f"""You are a research assistant going deeper on a {topic}, building on
the notes provided so far. Add new information, fill gaps, and correct anything doubtful in the
earlier notes. Do not just repeat what was already said. Wrap your research notes in <research></research> tags. 
After the closing tag, rate the quality of the notes on a scale from 1 to 10 in format research_rate=X where X is the rating."""

RESEARCH_USER_PROMPT = """According to research plan and any other previous research steps (if any), provide
a more detailed and thorough research notes on the topic."""

CRITIQUE_SYSTEM_PROMPT = """You are reviewing research notes for completeness and quality.
Rate how ready these notes are to be a final answer on a scale from 1 to 10, where 10 means
thorough, well-supported, and directly relevant to the topic, and 1 means it barely addresses
the topic. Reply in the format critique_rate=X where X is the rating, followed by a short
explanation of what is missing or could be improved."""

EXTRACT_RESEARCH_CONTENT_PROMPT = """Extract only the research content from the text below and return
it verbatim, with no extra commentary, tags, or formatting added."""

def RATE_RESEARCH_SYSTEM_PROMPT(topic, plan):
    return f"""You are rating research notes for quality and completeness.
Topic: {topic}
Research plan: {plan}
Rate the notes the user provides on a scale from 1 to 10, where 10 means thorough, well-supported,
and directly relevant to the topic and plan. Reply with ONLY the digit, nothing else."""
