SLASH_CMD = """
# Slash commands:
The following yaml is a list of slash prompts. If you see a prompt with a word
starting with the character / and matching the lookup, then replace the
slash prompt and use this prompt instructions that follow. For example /joke
result in telling a joke. If there are additional words after the slash
word then add that to the end of the command instructions.
For example "/joke about zebras" works tell a dad's joke about zebras.

If the slash command is not listed in the yaml below, assume it is a shell
command and run that using shelltools after removing the / at the start,
eg /head CONVENTIONS.md would run the linux command "head CONVENTIONS.md".
Print out the value of 'output' using bash code block in markdown.

hello:
  - reply with the word genius

Joke:
 - tell a dad joke

todo:
 - look for the comments with the words TODO, then follow the instructions contained within the rest of the TODO comment and implement the required code features.

Ofix:
 - list options to fix. IMPORTANT: Don't do so until you have asked me which option to use

Swot:
 - perform a swot analysis and output the results in a markdown table

Gr:
 - draw a chart using mermaid markdown

why:
 - ultrathink and explain why and list options to fix. IMPORTANT: don't apply a fix until you have asked me which option to use

ask:
 - if there are any doubts or ambiguities please ask me for clarification.

summary:
 - can you give me a summary of the files you modified and a diff please

"""
